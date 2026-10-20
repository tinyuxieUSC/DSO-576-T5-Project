import io
import json
import sys
from pathlib import Path
import pandas as pd
from streamlit.testing.v1 import AppTest
from outreach.filters import rank_clients,estimate_scenarios
from outreach.loader import get_client_metrics
from outreach.views import export_table,briefing_markdown,scenario_chart,PUBLIC_COLUMNS,NONADDITIVE


def test_exports_and_chart(fixture_data,january):
    ranked=rank_clients(get_client_metrics(fixture_data,january),.5)
    ranked['account_key']='NEVER_EXPORT'
    ranked['user_id']=123
    metadata={'mode':'sample','reach_weight':.5,'methodology':'test','account_counts_note':NONADDITIVE,'secret':'NEVER_EXPORT'}
    csv=export_table(ranked,metadata)
    assert 'account_key' not in csv and 'user_id' not in csv and 'NEVER_EXPORT' not in csv
    assert 'affected_accounts' in csv and 'reach_weight' in csv and 'methodology' in csv
    md=briefing_markdown(ranked,metadata)
    assert 'NEVER_EXPORT' not in md and NONADDITIVE in md
    scenarios=estimate_scenarios(ranked,['alpha','beta'],.8)
    chart=scenario_chart(scenarios).to_dict()
    assert chart['encoding']['strokeDash']['field']=='kind'
    assert chart['encoding']['xOffset']['field']=='measure'
    assert chart['encoding']['fillOpacity']['field']=='kind'
    assert (scenarios.additional_tagged_listens<=scenarios.missing_recording_mbid).all()


def test_app_interactions(monkeypatch):
    monkeypatch.setattr(sys,'argv',['app.py'])
    app=AppTest.from_file(Path('app.py').resolve(),default_timeout=30).run()
    assert not app.exception
    assert len(app.tabs)==4
    assert app.selectbox[0].value is None
    assert len(app.dataframe)>=1
    options=app.selectbox[0].options
    assert options
    app.selectbox[0].select(options[0]).run()
    assert not app.exception
    assert any(options[0] in item.value for item in app.subheader)
    if len(options)>=2:
        app.multiselect[0].set_value(options[:2]).run()
        assert not app.exception
    app.slider[0].set_value(100).run()
    assert not app.exception
    app.number_input[0].set_value(100000000).run()
    assert not app.exception
    assert app.selectbox[0].value is None


def test_fixture_screens(monkeypatch,fixture_data):
    from datetime import date
    from types import SimpleNamespace
    import outreach.setup as setup
    import outreach.loader as loader
    from dataclasses import replace
    config=setup.load_config()
    config.defaults.update(minimum_accounts=2,minimum_accounts_floor=1,target_coverage=.8)
    manifest={'first_play_date':'2026-01-01','last_play_date':'2026-01-31','accepted':2671,
              'warnings':[],'source_intervals':[],'quality':{},'rejected':0,'input_records':[]}
    data=replace(fixture_data,manifest=manifest)
    monkeypatch.setattr(setup,'cli_args',lambda:SimpleNamespace(config='config.toml',mode=None))
    monkeypatch.setattr(setup,'load_config',lambda *a,**k:config)
    monkeypatch.setattr(loader,'open_prepared',lambda *a,**k:data)
    app=AppTest.from_file(Path('app.py').resolve(),default_timeout=30).run()
    assert not app.exception
    assert app.dataframe[0].value.client.tolist()==['beta','alpha']
    app.selectbox[0].select('alpha').run()
    assert not app.exception
    assert [m.value for m in app.metric][-4:]==['31','4','3','32.3%']
    app.multiselect[0].set_value(['alpha','beta']).run()
    assert not app.exception
    tables=[d.value for d in app.dataframe]
    scenario=next(d for d in tables if 'additional_tagged_listens' in d.columns)
    assert scenario.set_index('client').additional_tagged_listens.to_dict()=={'alpha':15,'beta':92}


def test_ui_controls_do_not_read_raw_sources(monkeypatch):
    monkeypatch.setattr(sys,'argv',['app.py'])
    original=Path.open
    def guard(self,*args,**kwargs):
        if self.suffix in ('.csv','.listens'):
            raise AssertionError('Dashboard rerun attempted raw listening-file access')
        return original(self,*args,**kwargs)
    monkeypatch.setattr(Path,'open',guard)
    app=AppTest.from_file(Path('app.py').resolve(),default_timeout=30).run()
    assert not app.exception
    app.slider[0].set_value(25).run()
    assert not app.exception
    app.slider[1].set_value(90).run()
    assert not app.exception
    assert app.selectbox[0].options
    app.selectbox[0].select(app.selectbox[0].options[-1]).run()
    assert not app.exception


def test_full_mode_ui(monkeypatch):
    import pytest
    if not Path('data/prepared/full.json').exists():
        pytest.skip('Prepare full mode to exercise its UI integration test')
    monkeypatch.setattr(sys,'argv',['app.py','--mode','full'])
    app=AppTest.from_file(Path('app.py').resolve(),default_timeout=30).run()
    assert not app.exception
    assert any('FULL · ' in c.value for c in app.caption)
    assert app.selectbox[0].options
    app.selectbox[0].select(app.selectbox[0].options[0]).run()
    assert not app.exception
