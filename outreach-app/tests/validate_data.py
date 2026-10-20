"""Reproducible integration/audit benchmarks; not part of dashboard execution.
Run: .venv/bin/python tests/validate_data.py --mode sample [--layout]
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from dataclasses import replace
from datetime import date,datetime,timezone
import csv
import importlib.metadata
import json
from pathlib import Path
import re
import shutil
import sys
import threading
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from outreach.setup import load_config,DataFilters,PreparedDataset
from outreach.prepare import prepare_data,SCHEMA,_group
from outreach.data_rules import json_fields,clean_event
from outreach.loader import open_prepared,get_data_status,get_client_metrics,_query,rss_mb,sha256


def direct_audit(config,data):
    """Independent raw counts: no production adapters, grouping, or query helpers."""
    counts=defaultdict(lambda:dict(total=0,valid=0,absent=0,invalid=0,accounts=set(),affected=set()))
    global_accounts=set()
    pattern=re.compile(r'^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$')
    seen=set()
    for path in config.inputs():
        digest=sha256(path)
        if digest in seen:continue
        seen.add(digest)
        with path.open(encoding='utf-8',newline='') as f:
            records=csv.DictReader(f) if config.mode=='sample' else (json.loads(line) for line in f)
            for raw in records:
                ai=raw if config.mode=='sample' else raw.get('track_metadata',{}).get('additional_info',{})
                label=ai.get('ai_submission_client' if config.mode=='sample' else 'submission_client')
                client=label.strip().casefold() if isinstance(label,str) and label.strip() else 'NOT_REPORTED'
                client=config.aliases.get(client,client)
                mbid=ai.get('ai_recording_mbid' if config.mode=='sample' else 'recording_mbid')
                missing=mbid is None or isinstance(mbid,str) and not mbid.strip()
                valid=isinstance(mbid,str) and bool(pattern.fullmatch(mbid.strip()))
                # All real supplied data timestamps are valid; assert rather than silently skip.
                datetime.fromtimestamp(float(raw['timestamp']),timezone.utc)
                r=counts[client]
                r['total']+=1;r['valid']+=valid;r['absent']+=missing;r['invalid']+=not(missing or valid)
                account=raw.get('user_id')
                if account is not None and not isinstance(account,bool) and str(account).strip().isdigit() and int(account)>0:
                    account=int(account)
                    r['accounts'].add(account);global_accounts.add(account)
                    if not valid:r['affected'].add(account)
    status=get_data_status(data)
    m=_query(data,DataFilters(status.start,status.end,False,0)).set_index('client')
    assert set(m.index)==set(counts)
    for client,r in counts.items():
        actual=m.loc[client]
        assert (actual.total_listens,actual.with_recording_mbid,actual.absent_recording_mbid,
                actual.invalid_recording_mbid,actual.distinct_accounts,actual.affected_accounts)==(
                r['total'],r['valid'],r['absent'],r['invalid'],len(r['accounts']),len(r['affected'])),client
    return {'events':sum(r['total'] for r in counts.values()),'distinct_accounts':len(global_accounts),
            'valid_mbid_listens':sum(r['valid'] for r in counts.values()),
            'all_client_measures_match_independent_raw_count':True}


def benchmark(data):
    status=get_data_status(data)
    query=DataFilters(status.start,status.end,False,0)
    times=[]
    for _ in range(3):
        started=time.perf_counter();metrics=_query(data,query);times.append(time.perf_counter()-started)
    started=time.perf_counter();get_client_metrics(data,replace(query,exclude_importers=True));excluded=time.perf_counter()-started
    # Explicitly measure an aggregate-only cache hit separately from a scan.
    from functools import lru_cache
    @lru_cache(maxsize=4)
    def cached(q):return get_client_metrics(data,q)
    cached(query)
    started=time.perf_counter();cached(query);hit=time.perf_counter()-started
    return {'all_dates_importers_included_seconds':times,'importers_excluded_seconds':excluded,
            'aggregate_cache_hit_seconds':hit,'query_peak_rss_mb':rss_mb(),
            'query_process_budget_mb':data.memory_budget_mb,'cache_conditions':'OS caches not flushed; query-result cache disabled except explicit cache-hit measurement',
            'prepared_files':data.manifest['prepared_files'],'prepared_bytes':data.manifest['prepared_bytes']}


def layout_benchmark(config):
    """Same systematic input, old per-date/chunk layout versus bounded month layout."""
    root=Path('data/validation').resolve();root.mkdir(parents=True,exist_ok=True)
    subset=root/'raw'/'dump'/'listens'/'2026'/'subset.listens';subset.parent.mkdir(parents=True,exist_ok=True)
    source=config.inputs()[0]
    if config.mode!='full':return None
    with source.open('rb') as src,subset.open('wb') as dst:
        for line_no,line in enumerate(src,1):
            if line_no%1000==0:dst.write(line)
    for name in ['SCHEMA_SEQUENCE','START_TIMESTAMP','END_TIMESTAMP']:
        shutil.copyfile(source.parents[2]/name,subset.parents[2]/name)
    cfg=replace(config,paths=dict(config.paths),preparation=dict(config.preparation))
    cfg.paths.update(dataset_root=str(root/'raw'),full_inputs=['dump/listens/2026/subset.listens'],
                     prepared_root=str(root/'prepared'),secret_file=str(config.local_path('secret_file')))
    cfg.preparation['chunk_size']=1000
    compact=prepare_data(cfg,rebuild=True)
    old=root/('date-layout-'+str(time.time_ns()));old.mkdir()
    started=time.perf_counter();serial=0;rows=[]
    secret=cfg.local_path('secret_file').read_bytes()
    def flush():
        nonlocal serial
        if not rows:return
        grouped=_group(rows)
        for played,group in grouped.groupby('play_date'):
            folder=old/f'play_month={played:%Y-%m}';folder.mkdir(exist_ok=True)
            pq.write_table(pa.Table.from_pandas(group,schema=SCHEMA,preserve_index=False),folder/f'{serial}.parquet',compression='zstd',row_group_size=10000)
            serial+=1
        rows.clear()
    with subset.open() as f:
        for line in f:
            rows.append(clean_event(json_fields(json.loads(line)),secret,cfg.aliases,cfg.classification)[0])
            if len(rows)>=1000:flush()
    flush()
    old_seconds=time.perf_counter()-started
    baseline=replace(compact,path=old)
    status=get_data_status(compact)
    cases=[DataFilters(status.start,status.end,False,0),
           DataFilters(date(2026,9,9),date(2026,9,9),False,0),
           DataFilters(date(2026,1,31),date(2026,2,1),False,0)]
    timings={}
    for name,data in [('date_per_chunk',baseline),('compacted_month',compact)]:
        runs=[]
        for _ in range(2):
            start=time.perf_counter();_query(data,cases[0]);runs.append(time.perf_counter()-start)
        timings[name]=runs
    # Client, version and observed weekly groups compared over every client and case.
    for q in cases:
        for grouping in [None,'client_version','week_start']:
            a=_query(baseline,q,grouping=grouping);b=_query(compact,q,grouping=grouping)
            cols=['client']+([grouping] if grouping else [])
            a=a.sort_values(cols).reset_index(drop=True).sort_index(axis=1)
            b=b.sort_values(cols).reset_index(drop=True).sort_index(axis=1)
            pd.testing.assert_frame_equal(a,b)
    audit=direct_audit(cfg,compact)
    return {'input_events':compact.manifest['accepted'],'input_sha256':sha256(subset),
            'input_bytes':subset.stat().st_size,'sampling':'Every 1000th physical line from full JSONL; isolated validation cache',
            'exact_all_client_version_weekly_and_date_boundary_equality':True,
            'independent_raw_audit':audit,'date_per_chunk_files':serial,'compacted_month_files':compact.manifest['prepared_files'],
            'date_per_chunk_bytes':sum(p.stat().st_size for p in old.rglob('*.parquet')),
            'compacted_month_bytes':compact.manifest['prepared_bytes'],
            'date_per_chunk_preparation_seconds':old_seconds,
            'compacted_month_preparation_seconds':compact.manifest['preparation_seconds'],
            'compaction_seconds':compact.manifest['compaction_seconds'],
            'compacted_preparation_peak_rss_mb':compact.manifest['peak_rss_mb'],'query_seconds':timings,
            'os_caches':'Not flushed. Layouts measured sequentially; no full-size extrapolation.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['sample','full'],required=True);p.add_argument('--layout',action='store_true');a=p.parse_args()
    config=load_config('config.toml',a.mode);data=open_prepared(config)
    peak=[rss_mb()];stop=threading.Event()
    def monitor():
        while not stop.wait(.01):peak[0]=max(peak[0],rss_mb())
    thread=threading.Thread(target=monitor,daemon=True);thread.start()
    result={'fingerprint':data.fingerprint,'source_sha256':[i['sha256'] for i in data.manifest['inputs']],
            'preparation':{k:data.manifest[k] for k in ['accepted','rejected','preparation_seconds','compaction_seconds','peak_rss_mb','input_records','quality']}}
    result['benchmark']=benchmark(data)
    result['benchmark']['query_peak_rss_mb']=peak[0]
    result['audit']=direct_audit(config,data)
    if a.layout:result['layout']=layout_benchmark(config)
    stop.set();thread.join()
    path=Path(f'build-findings-{a.mode}.json');path.write_text(json.dumps(result,indent=2,default=str));print(path.read_text())

if __name__=='__main__':main()
