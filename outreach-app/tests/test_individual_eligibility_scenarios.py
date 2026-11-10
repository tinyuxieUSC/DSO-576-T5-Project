import pandas as pd
from outreach.filters import eligible, estimate_scenarios


def test_eligible_excludes_unreported_and_includes_threshold():
    metrics = pd.DataFrame([
        {'client': 'NOT_REPORTED', 'distinct_accounts': 100},
        {'client': 'below', 'distinct_accounts': 9},
        {'client': 'at_threshold', 'distinct_accounts': 10},
    ])
    result = eligible(metrics, 10)
    assert result['client'].tolist() == ['at_threshold']


def test_higher_target_does_not_decrease_scenario_additions():
    metrics = pd.DataFrame([{'client': 'alpha', 'total_listens': 100,
                             'with_recording_mbid': 30, 'missing_recording_mbid': 70}])
    low = estimate_scenarios(metrics, ['alpha'], 0.4)['additional_tagged_listens'].iloc[0]
    high = estimate_scenarios(metrics, ['alpha'], 0.7)['additional_tagged_listens'].iloc[0]
    assert 0 <= low <= high <= 70
    assert (low, high) == (10, 40)
