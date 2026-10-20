from dataclasses import replace
from datetime import date
from pathlib import Path
import csv
import json
import pandas as pd
import pytest
from outreach.loader import open_prepared, get_client_metrics
from outreach.prepare import prepare_data
from outreach.setup import load_config, DataFilters


def config_at(tmp_path,mode='sample',chunk=1):
    text = Path('config.toml').read_text().replace('dataset_root = "../../dataset_listenbrainz"','dataset_root = "raw"')
    p = tmp_path/'config.toml'
    p.write_text(text)
    config = load_config(p,mode)
    config.preparation['chunk_size']=chunk
    config.defaults['minimum_accounts_floor']=1
    root = tmp_path/'raw'
    root.mkdir(exist_ok=True)
    return config


def test_csv_chunks_and_invalidation(tmp_path):
    config = config_at(tmp_path)
    path = config.inputs()[0]
    path.parent.mkdir(parents=True)
    fields = ['user_id','timestamp','ai_submission_client','ai_submission_client_version','ai_recording_mbid']
    with path.open('w',newline='') as f:
        w = csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        for i in range(5):
            w.writerow(dict(user_id=1 if i<4 else '',timestamp=1767225600+i*86400,
                ai_submission_client='Test\nUTF-8 α',ai_submission_client_version='001',ai_recording_mbid='bad' if i==4 else ''))
    d = prepare_data(config)
    assert d.manifest['accepted']==5
    assert d.manifest['input_records'][0]['physical_lines']==11
    q = DataFilters(date(2026,1,1),date(2026,2,1),False,1)
    m = get_client_metrics(d,q)
    assert m.distinct_accounts.tolist()==[1] and m.affected_accounts.tolist()==[1]
    assert m.invalid_recording_mbid.tolist()==[1] and m.unknown_account_listens.tolist()==[1]
    config.preparation['chunk_size']=10
    pd.testing.assert_frame_equal(m,get_client_metrics(prepare_data(config,rebuild=True),q))
    config.aliases['a']='b'
    with pytest.raises(ValueError,match='Rules'):
        open_prepared(config)
    config.aliases.clear()
    path.write_text(path.read_text()+'bad\n')
    with pytest.raises(ValueError,match='Input changed'):
        open_prepared(config)


def test_json_rejections_duplicate_overlap_and_atomicity(tmp_path):
    config = config_at(tmp_path,'full')
    path = config.inputs()[0]
    path.parent.mkdir(parents=True)
    root = path.parents[2]
    (root/'SCHEMA_SEQUENCE').write_text('1')
    (root/'START_TIMESTAMP').write_text('2026-01-01 00:00:00+00:00')
    (root/'END_TIMESTAMP').write_text('2026-01-02 00:00:00+00:00')
    valid = {'user_id':1,'timestamp':1767225600,'track_metadata':{'additional_info':{'submission_client':'ArchiveTune'}}}
    path.write_text(json.dumps(valid)+'\n\n{\n'+json.dumps({'timestamp':1,'track_metadata':[]})+'\n')
    config.paths['full_inputs'] *= 2
    d = prepare_data(config)
    assert (d.manifest['accepted'],d.manifest['rejected'],d.manifest['duplicate_file_count'])==(1,3,1)
    assert any('archivetune' in w for w in d.manifest['warnings'])
    pointer = config.local_path('prepared_root')/'full.json'
    before = pointer.read_text()
    (root/'SCHEMA_SEQUENCE').write_text('2')
    with pytest.raises(ValueError,match='Unsupported'):
        prepare_data(config,rebuild=True)
    assert pointer.read_text()==before


@pytest.mark.parametrize('old,new,match',[
    ('reach_weight = 0.5','reach_weight = 1.5','reach_weight'),
    ('minimum_accounts = 100','minimum_accounts = -1','minimum_accounts'),
    ('chunk_size = 10000','chunk_size = 0','chunk_size'),
    ('target_coverage = 0.75','target_coverage = -1','target_coverage'),
])
def test_config_validation(tmp_path,old,new,match):
    path=tmp_path/'bad.toml'
    path.write_text(Path('config.toml').read_text().replace(old,new))
    with pytest.raises(ValueError,match=match):load_config(path)


def test_interrupted_write_preserves_cache(tmp_path,monkeypatch):
    import outreach.prepare as prepare
    config=config_at(tmp_path)
    path=config.inputs()[0];path.parent.mkdir(parents=True)
    path.write_text('user_id,timestamp,ai_submission_client,ai_submission_client_version,ai_recording_mbid\n1,1767225600,alpha,1,\n')
    data=prepare_data(config)
    pointer=config.local_path('prepared_root')/'sample.json'
    before=pointer.read_text()
    def fail(*args,**kwargs):raise OSError('simulated interrupted disk write')
    monkeypatch.setattr(prepare.pq,'write_table',fail)
    with pytest.raises(OSError,match='interrupted'):
        prepare_data(config,rebuild=True)
    assert pointer.read_text()==before
    assert open_prepared(config).path==data.path
    assert not list(config.local_path('prepared_root').glob('.preparing-*'))


def test_duplicate_file_change_invalidates(tmp_path):
    config=config_at(tmp_path,'full')
    path=config.inputs()[0];path.parent.mkdir(parents=True)
    root=path.parents[2];(root/'SCHEMA_SEQUENCE').write_text('1')
    event=json.dumps({'user_id':1,'timestamp':1767225600})+'\n'
    path.write_text(event)
    other=path.parent/'copy.listens';other.write_text(event)
    config.paths['full_inputs'].append(str(other))
    data=prepare_data(config)
    assert data.manifest['accepted']==1 and data.manifest['duplicate_file_count']==1
    other.write_text(event+event)
    with pytest.raises(ValueError,match='Input changed'):
        open_prepared(config)
