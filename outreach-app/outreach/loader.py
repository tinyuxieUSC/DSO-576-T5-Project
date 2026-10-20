"""Only this module and prepare.py access listening and prepared data files."""
from __future__ import annotations
from collections import Counter
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import threading
import time
import pandas as pd
import psutil
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq
from .data_rules import COUNT_COLUMNS, GROUP_COLUMNS, NOT_REPORTED
from .filters import empty_metrics, eligible
from .setup import AppConfig, DataFilters, DataStatus, PreparedDataset

MIB = 1048576
PROCESS = psutil.Process()


def rss_mb():
    return PROCESS.memory_info().rss / MIB


class MemorySampler:
    """Sample live total-process RSS, independently of batch boundaries."""
    def __init__(self):
        self.peak = rss_mb()
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self.stop.wait(.01):
            self.peak = max(self.peak, rss_mb())

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join()


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * MIB), b''):
            h.update(block)
    return h.hexdigest()


def policy_fingerprint(config):
    secret = config.local_path('secret_file')
    if not secret.exists():
        raise ValueError(f'Missing account secret: {secret}. Restore it or rebuild all caches.')
    return hashlib.sha256(json.dumps(config.policy(), sort_keys=True).encode() + secret.read_bytes()).hexdigest()


def open_prepared(config: AppConfig, verify=False) -> PreparedDataset:
    pointer = config.local_path('prepared_root') / f'{config.mode}.json'
    if not pointer.exists():
        raise ValueError(f'No completed {config.mode} cache. Run: python -m outreach.prepare --config "{config.path}" --mode {config.mode}')
    manifest_path = Path(json.loads(pointer.read_text())['manifest'])
    manifest = json.loads(manifest_path.read_text())
    if manifest['mode'] != config.mode:
        raise ValueError('Cache mode mismatch: prepare the explicitly selected mode again')
    if manifest['policy_fingerprint'] != policy_fingerprint(config):
        raise ValueError('Rules, aliases, classification, or secret changed. Rebuild with --rebuild.')
    expected = [str(p) for p in config.inputs()]
    if expected != manifest['selected_inputs']:
        raise ValueError('Input selection changed. Prepare this mode again with --rebuild.')
    for item in manifest['inputs']:
        path = Path(item['path'])
        if not path.exists():
            raise ValueError(f'Missing source: {path}. Restore it; no sample fallback is performed.')
        stat = path.stat()
        if stat.st_size != item['bytes'] or stat.st_mtime_ns != item['mtime_ns']:
            raise ValueError(f'Input changed: {path}. Prepare again with --rebuild.')
        if verify and sha256(path) != item['sha256']:
            raise ValueError(f'Checksum changed: {path}. Rebuild the cache.')
        for name, content in item.get('metadata', {}).items():
            if (Path(item['metadata_root']) / name).read_text().strip() != content:
                raise ValueError(f'Source metadata changed: {name}. Rebuild the cache.')
    return PreparedDataset(manifest_path.parent, manifest['fingerprint'], config.mode, manifest,
                           config.defaults['query_memory_budget_mb'],
                           minimum_accounts_floor=config.defaults['minimum_accounts_floor'])


def get_data_status(data: PreparedDataset) -> DataStatus:
    m = data.manifest
    return DataStatus(data.mode, data.fingerprint, date.fromisoformat(m['first_play_date']),
                      date.fromisoformat(m['last_play_date']), m['accepted'], m['warnings'], m)


def selected_batches(data, query):
    """Month pruning plus an exact inclusive date predicate, with bounded batches."""
    first_month, last_month = query.start.strftime('%Y-%m'), query.end.strftime('%Y-%m')
    paths = []
    for month in sorted(data.path.glob('play_month=*')):
        if not first_month <= month.name.split('=', 1)[1] <= last_month:
            continue
        paths.extend(str(path) for path in sorted(month.glob('*.parquet')))
    if not paths:
        return
    predicate = (ds.field('play_date') >= pa.scalar(query.start)) & (ds.field('play_date') <= pa.scalar(query.end))
    if query.exclude_importers:
        predicate &= ds.field('client_type') != 'importer'
    scanner = ds.dataset(paths, format='parquet').scanner(
        columns=GROUP_COLUMNS + COUNT_COLUMNS, filter=predicate, batch_size=10000,
        batch_readahead=1, fragment_readahead=1, use_threads=False)
    for batch in scanner.to_batches():
        if batch.num_rows:
            yield batch.to_pandas()


class ExactAccounts:
    """Bounded exact deduplication with deterministic hash-prefix Parquet spill."""
    def __init__(self, temp, allowance, budget):
        self.temp, self.allowance, self.budget = Path(temp), allowance, budget
        self.keys = {}
        self.spilled = False
        self.serial = 0
        self.spill_files = 0

    def check(self):
        if rss_mb() + 8 > self.budget:
            raise MemoryError(f'Query process RSS {rss_mb():.1f} MiB approaches budget {self.budget} MiB. Increase query_memory_budget_mb; exact counts were not approximated.')

    def add(self, group, account, affected):
        k = (group, account)
        self.keys[k] = self.keys.get(k, False) or affected
        if len(self.keys) >= self.allowance:
            self.flush()

    def flush(self):
        if not self.keys:
            return
        if shutil.disk_usage(self.temp).free < max(16 * MIB, len(self.keys) * 256):
            raise OSError('Insufficient temporary disk space for exact-account spill')
        df = pd.DataFrame([(g, a, b) for (g, a), b in self.keys.items()], columns=['group', 'account_key', 'affected'])
        df['bucket'] = df.account_key.str[:1]
        for bucket, rows in df.groupby('bucket'):
            folder = self.temp / bucket
            folder.mkdir(exist_ok=True)
            pq.write_table(pa.Table.from_pandas(rows.drop(columns='bucket'), preserve_index=False), folder / f'{self.serial}.parquet', compression='zstd')
            self.serial += 1
            self.spill_files += 1
        self.keys.clear()
        self.spilled = True
        self.check()

    def _bucket_counts(self, folder, depth):
        keys = {}
        overflow = False
        paths = list(folder.glob('*.parquet'))
        for path in paths:
            for batch in pq.ParquetFile(path).iter_batches(batch_size=min(10000, self.allowance)):
                for g, a, b in batch.to_pandas().itertuples(index=False, name=None):
                    k = (g, a)
                    keys[k] = keys.get(k, False) or b
                self.check()
                if len(keys) > self.allowance:
                    overflow = True
                    break
            if overflow:
                break
        if not overflow:
            counts = Counter()
            for (group, _), affected in keys.items():
                counts[(group, 'distinct')] += 1
                counts[(group, 'affected')] += int(affected)
            return counts
        # A single account can occupy many version/week groups. Its account
        # prefix cannot split those keys; use a secondary group prefix only
        # inside that account bucket, retaining group in the deduplication key.
        if len({account for _, account in keys}) == 1:
            depth = max(depth, 64)
        del keys
        if depth >= 128:
            raise MemoryError('Cannot split exact-account bucket further; increase memory budget')
        for path in paths:
            for batch in pq.ParquetFile(path).iter_batches(batch_size=min(10000, self.allowance)):
                df = batch.to_pandas()
                prefixes = df.apply(lambda r: (r.account_key + hashlib.sha256(r['group'].encode()).hexdigest())[:depth + 1], axis=1)
                for prefix, rows in df.groupby(prefixes):
                    child = folder / prefix
                    child.mkdir(exist_ok=True)
                    pq.write_table(pa.Table.from_pandas(rows, preserve_index=False), child / f'{self.serial}.parquet', compression='zstd')
                    self.serial += 1
        counts = Counter()
        for child in folder.iterdir():
            if child.is_dir():
                counts.update(self._bucket_counts(child, depth + 1))
                shutil.rmtree(child)
        return counts

    def counts(self):
        if not self.spilled:
            counts = Counter()
            for (group, _), affected in self.keys.items():
                counts[(group, 'distinct')] += 1
                counts[(group, 'affected')] += int(affected)
            return counts
        self.flush()
        counts = Counter()
        for folder in self.temp.iterdir():
            if folder.is_dir():
                counts.update(self._bucket_counts(folder, 1))
        return counts


def _query(data: PreparedDataset, query: DataFilters, client=None, grouping=None):
    baseline = rss_mb()
    if baseline + 48 >= data.memory_budget_mb:
        raise MemoryError(f'query_memory_budget_mb={data.memory_budget_mb}: process baseline is {baseline:.1f} MiB; allow at least {int(baseline + 64)} MiB')
    allowance = max(1, min(data.key_set_allowance, int((data.memory_budget_mb - baseline - 48) * MIB / 640)))
    totals = {}
    with tempfile.TemporaryDirectory(prefix='outreach-query-') as temp:
        keys = ExactAccounts(temp, allowance, data.memory_budget_mb)
        for df in selected_batches(data, query):
            keys.check()
            if client is not None:
                df = df.loc[df.client == client].copy()
            if df.empty:
                continue
            if grouping == 'week_start':
                df['week_start'] = df.play_date.map(lambda d: d - timedelta(days=d.weekday()))
            groups = ['client'] + ([grouping] if grouping else [])
            for group_values, group in df.groupby(groups, sort=False):
                if not isinstance(group_values, tuple):
                    group_values = (group_values,)
                identity = json.dumps([str(v) for v in group_values])
                if identity not in totals:
                    totals[identity] = {'client': group_values[0], 'client_type': group.client_type.iloc[0],
                        **{c: 0 for c in COUNT_COLUMNS}, 'unknown_account_listens': 0,
                        'unknown_version_listens': 0, 'first_play_date': group.play_date.min(),
                        'last_play_date': group.play_date.max()}
                    if grouping:
                        totals[identity][grouping] = group_values[1]
                acc = totals[identity]
                for c in COUNT_COLUMNS:
                    acc[c] += int(group[c].sum())
                acc['unknown_account_listens'] += int(group.loc[group.account_key.isna(), 'listens'].sum())
                acc['unknown_version_listens'] += int(group.loc[group.client_version == NOT_REPORTED, 'listens'].sum())
                acc['first_play_date'] = min(acc['first_play_date'], group.play_date.min())
                acc['last_play_date'] = max(acc['last_play_date'], group.play_date.max())
                for a, absent, invalid in group[['account_key', 'missing_mbid_listens', 'invalid_mbid_listens']].itertuples(index=False, name=None):
                    if pd.notna(a):
                        keys.add(identity, a, absent + invalid > 0)
            if rss_mb() + 48 >= data.memory_budget_mb and keys.keys:
                keys.flush()
        counts = keys.counts()
    rows = []
    for identity, r in totals.items():
        r['total_listens'] = r.pop('listens')
        r['with_recording_mbid'] = r.pop('valid_mbid_listens')
        r['absent_recording_mbid'] = r.pop('missing_mbid_listens')
        r['invalid_recording_mbid'] = r.pop('invalid_mbid_listens')
        r['missing_recording_mbid'] = r['absent_recording_mbid'] + r['invalid_recording_mbid']
        r['coverage'] = r['with_recording_mbid'] / r['total_listens']
        r['distinct_accounts'] = counts[(identity, 'distinct')]
        r['affected_accounts'] = counts[(identity, 'affected')]
        rows.append(r)
    result = pd.DataFrame(rows) if rows else empty_metrics({grouping: 'object'} if grouping else None)
    if grouping == 'week_start' and client is not None and len(result):
        weeks = pd.date_range(query.start - timedelta(days=query.start.weekday()), query.end, freq='W-MON').date
        result = result.set_index('week_start').reindex(weeks).rename_axis('week_start').reset_index()
        result['partial_week'] = result.week_start.map(lambda d: d < query.start or d + timedelta(days=6) > query.end)
    return result


def get_client_metrics(data: PreparedDataset, query: DataFilters) -> pd.DataFrame:
    return eligible(_query(data, query), max(query.minimum_accounts, data.minimum_accounts_floor))


def _detail(data, query, client, grouping):
    # Parent eligibility applies once; version/week groups have no account floor.
    parent = get_client_metrics(data, query)
    if client not in set(parent.client):
        return empty_metrics({grouping: 'object'})
    return _query(data, query, client, grouping)


def get_version_metrics(data: PreparedDataset, query: DataFilters, client: str) -> pd.DataFrame:
    result = _detail(data, query, client, 'client_version')
    if len(result):
        result = result.assign(_unknown=result.client_version == NOT_REPORTED).sort_values(
            ['_unknown', 'total_listens', 'client_version'], ascending=[True, False, True]).drop(columns='_unknown')
    return result


def get_weekly_metrics(data: PreparedDataset, query: DataFilters, client: str) -> pd.DataFrame:
    return _detail(data, query, client, 'week_start')
