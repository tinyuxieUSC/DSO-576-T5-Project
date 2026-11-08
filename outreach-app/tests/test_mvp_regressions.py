"""Protect the pilot decision and portable two-client evidence workflow."""
from fractions import Fraction
import io
from pathlib import Path
import pandas as pd
from streamlit.testing.v1 import AppTest
from outreach.filters import estimate_scenarios
from outreach.views import export_table, briefing_markdown


def test_minimum_reaches_target_and_one_fewer_does_not():
    # Exact fractions independently define correctness, including the 7%-of-100 boundary.
    for total, valid in [(520,0),(889,469),(100,0),(5,0),(5,5)]:
        for percent in [0,1,7,50,75,100]:
            metrics = pd.DataFrame([dict(client='candidate',total_listens=total,
                                        with_recording_mbid=valid,missing_recording_mbid=total-valid)])
            row = estimate_scenarios(metrics,['candidate'],percent/100).iloc[0]
            minimum = int(row.minimum_additions_to_target)
            target = Fraction(percent,100)
            assert Fraction(valid+minimum,total) >= target
            assert minimum == 0 or Fraction(valid+minimum-1,total) < target
            assert row.achieved_coverage == (valid+row.additional_tagged_listens)/total
    pano = estimate_scenarios(pd.DataFrame([dict(client='pano',total_listens=520,
                              with_recording_mbid=0,missing_recording_mbid=520)]),['pano'],.01).iloc[0]
    assert pano.additional_tagged_listens == 5
    assert pano.minimum_additions_to_target == 6
    assert pano.achieved_coverage == 5/520


def test_two_client_export_is_complete_reproducible_and_aggregate_only():
    metrics = pd.DataFrame([
        dict(client='pano',total_listens=520,with_recording_mbid=0,missing_recording_mbid=520),
        dict(client='navidrome',total_listens=889,with_recording_mbid=469,missing_recording_mbid=420)])
    scenario = estimate_scenarios(metrics,['pano','navidrome'],.01)
    scenario['account_key'] = 'PRIVATE_TEST_VALUE'
    metadata = dict(mode='sample',fingerprint='test-source',playback_start='2005-02-13',
                    playback_end='2026-09-03',exclude_importers=True,minimum_accounts=100,
                    target_coverage=.01,comparison_clients=['pano','navidrome'],
                    limitations='Hypothetical only',account_counts_note='Accounts are not additive',
                    secret='PRIVATE_TEST_VALUE')
    exported = pd.read_csv(io.StringIO(export_table(scenario,metadata)))
    assert exported.client.tolist() == ['pano','navidrome']
    assert exported.minimum_additions_to_target.tolist() == [6,0]
    assert exported.fingerprint.tolist() == ['test-source','test-source']
    assert exported.playback_start.tolist() == ['2005-02-13','2005-02-13']
    assert exported.exclude_importers.all()
    md=briefing_markdown(scenario,metadata)
    assert 'client: pano' in md and 'client: navidrome' in md
    assert 'PRIVATE_TEST_VALUE' not in md+export_table(scenario,metadata)


def test_comparison_briefing_works_without_an_inspected_client(portable_ui):
    app=AppTest.from_file(Path('app.py').resolve(),default_timeout=60).run()
    app.multiselect[0].set_value(['pano scrobbler','navidrome']).run()
    app.slider[1].set_value(1).run()
    assert not app.exception
    assert app.selectbox[0].value is None
    tables=[d.value for d in app.dataframe if 'minimum_additions_to_target' in d.value.columns]
    assert len(tables) == 2  # comparison screen and complete-comparison briefing
    for table in tables:
        assert table.set_index('client').minimum_additions_to_target.to_dict() == {'pano scrobbler':6,'navidrome':0}
    assert any('Complete comparison briefing' in m.value for m in app.markdown)
    # The individual-client briefing remains available alongside the comparison.
    app.selectbox[0].select('navidrome').run()
    assert not app.exception
    assert any('client: navidrome' in m.value for m in app.markdown)


def test_portable_launcher_recovers_after_host_refreshes_source_timestamp(tmp_path):
    import os
    import shutil
    original = Path(__file__).resolve().parents[2]
    shutil.copy2(original/'streamlit_app.py',tmp_path/'streamlit_app.py')
    app_dir=tmp_path/'outreach-app'
    app_dir.mkdir()
    for filename in ['app.py','config.cloud.toml']:
        shutil.copy2(original/'outreach-app'/filename,app_dir/filename)
    shutil.copytree(original/'outreach-app/outreach',app_dir/'outreach',ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(original/'outreach-app/demo-input',app_dir/'demo-input')
    app=AppTest.from_file(tmp_path/'streamlit_app.py',default_timeout=60).run()
    assert not app.exception
    assert len(app.tabs)==4
    source=app_dir/'demo-input/listens_20260904.csv'
    stat=source.stat()
    os.utime(source,ns=(stat.st_atime_ns,stat.st_mtime_ns+1000000))
    app.run()
    assert not app.exception
    assert not app.error
    assert len(app.tabs)==4
