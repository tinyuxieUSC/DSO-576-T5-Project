from dataclasses import replace
from datetime import date
import json
import math
from pathlib import Path
import pandas as pd
import pytest
from outreach.data_rules import clean_event, csv_fields, json_fields, RejectedEvent
from outreach.filters import rank_clients, rank_sensitivity, estimate_scenarios, empty_metrics
from outreach.loader import get_client_metrics, get_version_metrics, get_weekly_metrics
from outreach.setup import DataFilters, load_config

POLICY = {'importers':['imp'], 'regular_clients':['alpha']}
SECRET = b'x'*32
UUID = 'AABBCCDD-1234-5678-9012-123456789ABC'

def test_adapters_and_rules():
    raw = {'user_id':12, 'timestamp':1767225600, 'track_metadata':{'additional_info':{
        'submission_client':' ALPHA ', 'submission_client_version':' 1.0 ', 'recording_mbid':UUID}}}
    flat = {'user_id':'12', 'timestamp':'1767225600', 'ai_submission_client':' ALPHA ',
            'ai_submission_client_version':' 1.0 ', 'ai_recording_mbid':UUID}
    assert clean_event(json_fields(raw), SECRET, {}, POLICY) == clean_event(csv_fields(flat), SECRET, {}, POLICY)
    r, _, _ = clean_event(json_fields({'timestamp':1767225600}), SECRET, {}, POLICY)
    assert r['account_key'] is None and r['client'] == 'NOT_REPORTED' and r['missing_mbid_listens'] == 1
    for account in [True, 0, -1, 1.5, '1.5', '', None]:
        r, _, _ = clean_event((account,1767225600,'α',None,False), SECRET, {}, POLICY)
        assert r['account_key'] is None and r['invalid_mbid_listens'] == 1
    for timestamp in [None,'','abc',True,float('inf'),1e40]:
        with pytest.raises(RejectedEvent):
            clean_event((1,timestamp,'a',None,None), SECRET, {}, POLICY)
    for block in [[],None,False]:
        with pytest.raises(RejectedEvent):
            json_fields({'track_metadata':block})
    r,_,_ = clean_event((1,1767225600,' Alias ','02',None), SECRET, {'alias':'alpha'}, POLICY)
    assert r['client'] == 'alpha' and r['client_type'] == 'regular'


def test_exact_january(fixture_data,january):
    m = get_client_metrics(fixture_data,january).set_index('client')
    a,b = m.loc['alpha'],m.loc['beta']
    assert (a.total_listens,a.with_recording_mbid,a.missing_recording_mbid,a.distinct_accounts,a.affected_accounts)==(31,10,21,4,3)
    assert (b.total_listens,b.with_recording_mbid,b.missing_recording_mbid,b.distinct_accounts,b.affected_accounts)==(140,20,120,2,2)
    assert a.coverage == 10/31
    ranked = rank_clients(m.reset_index(),.5)
    assert list(ranked.client)==['beta','alpha']
    assert ranked.score.tolist()==pytest.approx([.896241,.822266],abs=1e-6)
    sensitivity = rank_sensitivity(m.reset_index(),[0,.5,1,.5])
    assert list(sensitivity[sensitivity['rank']==1].client)==['beta','beta','alpha']
    scenarios = estimate_scenarios(m.reset_index(),['alpha','beta'],.8).set_index('client')
    assert scenarios.loc['alpha','additional_tagged_listens']==15
    assert scenarios.loc['beta','additional_tagged_listens']==92
    assert estimate_scenarios(m.reset_index(),['beta'],.1).additional_tagged_listens.iloc[0]==0
    versions = get_version_metrics(fixture_data,january,'alpha').set_index('client_version')
    assert (versions.loc['1.1','total_listens'],versions.loc['1.1','distinct_accounts'],versions.loc['1.1','coverage'])==(16,3,.625)
    assert versions.total_listens.sum()==31
    with_imp = get_client_metrics(fixture_data,replace(january,exclude_importers=False)).set_index('client')
    assert with_imp.loc['imp','total_listens']==2000
    feb = get_client_metrics(fixture_data,replace(january,end=date(2026,2,1))).set_index('client')
    assert (feb.loc['beta','total_listens'],feb.loc['beta','distinct_accounts'])==(150,3)


def test_forced_spill(fixture_data,january):
    normal = get_client_metrics(fixture_data,january)
    spilled = get_client_metrics(replace(fixture_data,key_set_allowance=1),january)
    pd.testing.assert_frame_equal(normal,spilled)
    pd.testing.assert_frame_equal(get_version_metrics(fixture_data,january,'alpha'),
                                  get_version_metrics(replace(fixture_data,key_set_allowance=1),january,'alpha'))
    pd.testing.assert_frame_equal(get_weekly_metrics(fixture_data,january,'alpha'),
                                  get_weekly_metrics(replace(fixture_data,key_set_allowance=1),january,'alpha'))
    with pytest.raises(MemoryError,match='baseline'):
        get_client_metrics(replace(fixture_data,memory_budget_mb=1),january)


def test_endpoints_weeks_empty(fixture_data,january):
    one = get_client_metrics(fixture_data,replace(january,start=date(2026,1,2),end=date(2026,1,2),minimum_accounts=1)).set_index('client')
    assert one.loc['alpha','total_listens']==15
    cross = get_client_metrics(fixture_data,DataFilters(date(2026,1,31),date(2026,2,1),True,1))
    assert cross.total_listens.tolist()==[10]
    weekly = get_weekly_metrics(fixture_data,january,'alpha')
    assert weekly.total_listens.iloc[0]==31 and weekly.total_listens.iloc[1:].isna().all()
    assert weekly.partial_week.iloc[0]
    assert get_client_metrics(fixture_data,replace(january,minimum_accounts=100)).empty
    assert get_version_metrics(fixture_data,january,'solo').empty
    with pytest.raises(ValueError):
        DataFilters(date(2026,2,1),date(2026,1,1))


def test_zero_ties_targets():
    m = pd.DataFrame([dict(client=c,affected_accounts=0,missing_recording_mbid=0,total_listens=5,with_recording_mbid=5) for c in ['b','a']])
    r = rank_clients(m,.5)
    assert r.client.tolist()==['a','b'] and r.score.tolist()==[0,0]
    for bad in [-.1,1.1]:
        with pytest.raises(ValueError): rank_clients(m,bad)
        with pytest.raises(ValueError): estimate_scenarios(m,['a'],bad)
    m = pd.DataFrame([dict(client='a', total_listens=5,with_recording_mbid=0,missing_recording_mbid=5)])
    assert estimate_scenarios(m,['a'],.5).additional_tagged_listens.iloc[0]==2
    assert rank_clients(empty_metrics(),.5).empty
    assert estimate_scenarios(empty_metrics(),[],.75).empty


def test_shared_account_across_clients(fixture_data,january):
    import hashlib
    import pyarrow.parquet as pq
    import pyarrow as pa
    path=fixture_data.path/'play_month=2026-01'/'5.parquet'
    table=pq.ParquetFile(path).read().to_pandas()
    table['account_key']=hashlib.sha256(b'a1').hexdigest()
    pq.write_table(pa.Table.from_pandas(table,preserve_index=False),path)
    m=get_client_metrics(fixture_data,january).set_index('client')
    assert m.loc['alpha','distinct_accounts']==4
    assert m.loc['beta','distinct_accounts']==2
    # Shared identity is deduplicated within its client, never removed from another client.
    assert m.loc['alpha','affected_accounts']==3 and m.loc['beta','affected_accounts']==2


def test_loader_enforces_floor(fixture_data,january):
    assert get_client_metrics(replace(fixture_data,minimum_accounts_floor=5),january).empty


def test_spill_same_account_across_versions(fixture_data,january):
    import hashlib
    import pyarrow.parquet as pq
    import pyarrow as pa
    path=fixture_data.path/'play_month=2026-01'/'2.parquet'
    table=pq.ParquetFile(path).read().to_pandas()
    table['account_key']=hashlib.sha256(b'a1').hexdigest()
    pq.write_table(pa.Table.from_pandas(table,preserve_index=False),path)
    spilled=replace(fixture_data,key_set_allowance=1)
    for query in [get_client_metrics,
                  lambda d,q:get_version_metrics(d,q,'alpha'),
                  lambda d,q:get_weekly_metrics(d,q,'alpha')]:
        pd.testing.assert_frame_equal(query(fixture_data,january),query(spilled,january))
