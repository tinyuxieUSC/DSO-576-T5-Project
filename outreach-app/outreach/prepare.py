"""Explicit, bounded offline preparation. Never invoked by a dashboard rerun."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import tempfile
import time
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from .data_rules import COUNT_COLUMNS, GROUP_COLUMNS, RejectedEvent, clean_event, csv_fields, json_fields
from .loader import open_prepared, policy_fingerprint, rss_mb, sha256, MemorySampler
from .setup import AppConfig, load_config

SCHEMA = pa.schema([('play_date', pa.date32()), ('client', pa.string()), ('client_version', pa.string()),
                    ('account_key', pa.string()), ('client_type', pa.string())] + [(c, pa.int64()) for c in COUNT_COLUMNS])


def _metadata(path):
    for parent in path.parents:
        if (parent / 'SCHEMA_SEQUENCE').exists():
            values = {name: (parent / name).read_text().strip() for name in
                      ('SCHEMA_SEQUENCE', 'START_TIMESTAMP', 'END_TIMESTAMP') if (parent / name).exists()}
            if values['SCHEMA_SEQUENCE'] != '1':
                raise ValueError(f'Unsupported SCHEMA_SEQUENCE={values["SCHEMA_SEQUENCE"]!r} at {parent}; expected 1')
            return parent, values
    raise ValueError(f'Missing SCHEMA_SEQUENCE for {path}; select an extracted ListenBrainz dump')


def _group(rows):
    df = pd.DataFrame(rows) if isinstance(rows, list) else rows
    return df.groupby(GROUP_COLUMNS, dropna=False, sort=False, as_index=False)[COUNT_COLUMNS].sum()


def prepare_data(config: AppConfig, rebuild=False):
    with MemorySampler() as memory:
        return _prepare_data(config, rebuild, memory)


def _prepare_data(config, rebuild, memory):
    started = time.perf_counter()
    secret_file = config.local_path('secret_file')
    secret_file.parent.mkdir(parents=True, exist_ok=True)
    if not secret_file.exists():
        with secret_file.open('xb') as f:
            os.chmod(secret_file, 0o600)
            f.write(secrets.token_bytes(32))
    secret = secret_file.read_bytes()
    if len(secret) < 32:
        raise ValueError('Account secret is too short; restore the original 32-byte secret or rebuild every mode')
    if not rebuild:
        try:
            return open_prepared(config, verify=True)
        except (ValueError, FileNotFoundError):
            pass
    inputs, checks, seen, duplicates = [], [], set(), []
    for path in config.inputs():
        if not path.is_file():
            raise ValueError(f'Missing {config.mode} input: {path}. Follow the dataset README download links, extract it, then prepare again. No automatic fallback.')
        digest = sha256(path)
        stat = path.stat()
        item = {'path': str(path), 'sha256': digest, 'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns}
        if config.mode == 'full':
            root, values = _metadata(path)
            item.update(metadata_root=str(root), metadata=values)
        checks.append(item)
        if digest in seen:
            duplicates.append(str(path))
            continue
        seen.add(digest)
        inputs.append(item)
    policy = policy_fingerprint(config)
    fingerprint = hashlib.sha256(json.dumps({'inputs': checks, 'policy': policy, 'mode': config.mode}, sort_keys=True).encode()).hexdigest()
    root = config.local_path('prepared_root')
    root.mkdir(parents=True, exist_ok=True)
    report = {'mode': config.mode, 'fingerprint': fingerprint, 'policy_fingerprint': policy,
              'selected_inputs': [str(p) for p in config.inputs()], 'inputs': checks,
              'rules': config.policy(), 'accepted': 0, 'rejected': 0, 'duplicate_files': duplicates,
              'duplicate_file_count': len(duplicates), 'warnings': [], 'errors': [],
              'quality': Counter(), 'raw_labels': Counter(), 'rejection_reasons': Counter(), 'input_records': [],
              'peak_rss_mb': rss_mb()}
    intervals = []
    for item in inputs:
        md = item.get('metadata', {})
        if 'START_TIMESTAMP' in md and 'END_TIMESTAMP' in md:
            intervals.append((datetime.fromisoformat(md['START_TIMESTAMP']), datetime.fromisoformat(md['END_TIMESTAMP'])))
        else:
            report['warnings'].append(f'Submission collection interval unavailable for {Path(item["path"]).name}. Playback coverage is incomplete.')
    for i, a in enumerate(intervals):
        for b in intervals[:i]:
            if a[0] < b[1] and b[0] < a[1]:
                report['warnings'].append('Source collection intervals overlap. All events retained; duplicate events cannot be inferred.')
    report['source_intervals'] = [[a.isoformat(), b.isoformat()] for a, b in intervals]
    first, last = None, None
    serial = 0
    with tempfile.TemporaryDirectory(prefix='.preparing-', dir=root) as stage:
        stage = Path(stage)
        fragments = stage / '_fragments'
        fragments.mkdir()
        def flush(rows):
            nonlocal serial
            if not rows:
                return
            df = _group(rows)
            df['month'] = df.play_date.map(lambda d: d.strftime('%Y-%m'))
            for month, group in df.groupby('month', sort=False):
                folder = fragments / f'play_month={month}'
                folder.mkdir(exist_ok=True)
                table = pa.Table.from_pandas(group.drop(columns='month'), schema=SCHEMA, preserve_index=False)
                pq.write_table(table, folder / f'{serial}.parquet', compression='zstd', row_group_size=10000)
                serial += 1
            report['peak_rss_mb'] = max(report['peak_rss_mb'], rss_mb())
        for item in inputs:
            path = Path(item['path'])
            physical = parsed = accepted_before = 0
            accepted_before = report['accepted']
            end = item.get('metadata', {}).get('END_TIMESTAMP')
            end = datetime.fromisoformat(end) if end else None
            rows = []
            def accept(fields, line):
                nonlocal first, last
                try:
                    row, label, played = clean_event(fields, secret, config.aliases, config.classification)
                except RejectedEvent as e:
                    reject(str(e), line)
                    return
                report['accepted'] += 1
                report['raw_labels'][label] += 1
                for c in COUNT_COLUMNS[1:]:
                    report['quality'][c] += row[c]
                report['quality']['unknown_account_listens'] += int(row['account_key'] is None)
                report['quality']['unknown_version_listens'] += int(row['client_version'] == 'NOT_REPORTED')
                report['quality']['unreported_client_listens'] += int(row['client'] == 'NOT_REPORTED')
                report['quality']['future_playback_events'] += int(end is not None and played > end)
                if row['client_type'] == 'unknown' and any(t in row['client'] for t in ('import', 'archive', 'takeout')):
                    warning = f'Unverified importer-like label: {row["client"]}; retained as unknown.'
                    if warning not in report['warnings']:
                        report['warnings'].append(warning)
                first = min(first, row['play_date']) if first else row['play_date']
                last = max(last, row['play_date']) if last else row['play_date']
                rows.append(row)
            def reject(reason, line):
                report['rejected'] += 1
                report['rejection_reasons'][reason] += 1
                # Bounded diagnostics retain only location/reason, never source contents.
                if len(report['errors']) < 100:
                    report['errors'].append({'file': path.name, 'line': line, 'reason': reason})
            with path.open(encoding='utf-8', newline='') as f:
                if config.mode == 'sample':
                    reader = csv.DictReader(f, strict=True)
                    required = {'user_id', 'timestamp', 'ai_submission_client', 'ai_submission_client_version', 'ai_recording_mbid'}
                    if not required.issubset(reader.fieldnames or []):
                        raise ValueError(f'{path}: missing required CSV columns {sorted(required - set(reader.fieldnames or []))}')
                    try:
                        for record in reader:
                            parsed += 1
                            if None in record:
                                raise ValueError(f'{path.name}:{reader.line_num}: extra CSV fields; fix malformed CSV')
                            accept(csv_fields(record), reader.line_num)
                            if parsed % config.preparation['chunk_size'] == 0:
                                flush(rows)
                                rows.clear()
                        physical = reader.line_num
                    except csv.Error as e:
                        raise ValueError(f'{path.name}:{reader.line_num}: unrecoverable CSV syntax: {e}') from None
                else:
                    for physical, line in enumerate(f, 1):
                        parsed += 1
                        try:
                            record = json.loads(line)
                            accept(json_fields(record), physical)
                        except (json.JSONDecodeError, RejectedEvent) as e:
                            reject('malformed_json' if isinstance(e, json.JSONDecodeError) else str(e), physical)
                        if parsed % config.preparation['chunk_size'] == 0:
                            flush(rows)
                            rows.clear()
            flush(rows)
            accepted = report['accepted'] - accepted_before
            report['input_records'].append({'file': path.name, 'parsed_records': parsed,
                                           'physical_lines': physical, 'accepted': accepted,
                                           'rejected': parsed - accepted})
        if not report['accepted']:
            raise ValueError('Zero accepted events; inspect source format and timestamp fields')
        # Compact one month at a time, never materializing the full event history.
        compact_started = time.perf_counter()
        for folder in sorted(fragments.iterdir()):
            output = stage / folder.name
            output.mkdir()
            buffer, length, part = [], 0, 0
            def write_buffer():
                nonlocal buffer, length, part
                if not buffer:
                    return
                df = _group(pd.concat(buffer, ignore_index=True)).sort_values(['play_date', 'client'])
                pq.write_table(pa.Table.from_pandas(df, schema=SCHEMA, preserve_index=False),
                               output / f'part-{part:05}.parquet', compression='zstd', row_group_size=10000)
                part += 1
                buffer, length = [], 0
                report['peak_rss_mb'] = max(report['peak_rss_mb'], rss_mb())
            for path in folder.glob('*.parquet'):
                for batch in pq.ParquetFile(path).iter_batches(batch_size=10000):
                    df = batch.to_pandas()
                    buffer.append(df)
                    length += len(df)
                    # Combined cap applies globally because only one month is open.
                    if length >= 150000:
                        write_buffer()
            write_buffer()
        shutil.rmtree(fragments)
        report['compaction_seconds'] = time.perf_counter() - compact_started
        if report['quality']['future_playback_events']:
            report['warnings'].append(f'{report["quality"]["future_playback_events"]:,} events exceed their source submission end; retained.')
        report.update(first_play_date=first.isoformat(), last_play_date=last.isoformat(),
                      preparation_seconds=time.perf_counter() - started,
                      prepared_files=len(list(stage.rglob('*.parquet'))),
                      prepared_bytes=sum(p.stat().st_size for p in stage.rglob('*.parquet')),
                      raw_bytes=sum(i['bytes'] for i in inputs))
        report['peak_rss_mb'] = max(report['peak_rss_mb'], memory.peak)
        (stage / 'manifest.json').write_text(json.dumps(report, indent=2))
        # Unique completed directory plus atomic pointer replacement preserves old caches.
        final = root / f'{fingerprint}-{secrets.token_hex(4)}'
        stage.rename(final)
        pointer_tmp = root / f'.{config.mode}-{secrets.token_hex(4)}.json'
        pointer_tmp.write_text(json.dumps({'manifest': str(final / 'manifest.json')}))
        os.replace(pointer_tmp, root / f'{config.mode}.json')
    return open_prepared(config)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', default='config.toml')
    p.add_argument('--mode', choices=['sample', 'full'])
    p.add_argument('--rebuild', action='store_true')
    p.add_argument('--verify', action='store_true', help='Verify source hashes of an existing cache')
    args = p.parse_args()
    try:
        config = load_config(args.config, args.mode)
        data = open_prepared(config, verify=True) if args.verify else prepare_data(config, args.rebuild)
        m = data.manifest
        print(json.dumps({k: m[k] for k in ['mode', 'fingerprint', 'accepted', 'rejected', 'quality', 'prepared_files', 'prepared_bytes', 'preparation_seconds', 'peak_rss_mb', 'warnings']}, indent=2))
    except (ValueError, OSError) as e:
        p.exit(1, f'Preparation failed: {e}\n')

if __name__ == '__main__':
    main()
