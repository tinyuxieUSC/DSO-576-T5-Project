"""Pure aggregate calculations; no file, identifier, or UI access."""
from __future__ import annotations
import math
import pandas as pd
from .data_rules import NOT_REPORTED

METRIC_DTYPES = {
    'client': 'object', 'client_type': 'object', 'total_listens': 'int64',
    'with_recording_mbid': 'int64', 'absent_recording_mbid': 'int64',
    'invalid_recording_mbid': 'int64', 'missing_recording_mbid': 'int64',
    'coverage': 'float64', 'distinct_accounts': 'int64', 'affected_accounts': 'int64',
    'unknown_account_listens': 'int64', 'unknown_version_listens': 'int64',
    'first_play_date': 'object', 'last_play_date': 'object'}


def empty_metrics(extra=None):
    return pd.DataFrame({k: pd.Series(dtype=v) for k, v in (METRIC_DTYPES | (extra or {})).items()})


def eligible(metrics, minimum):
    return metrics.loc[(metrics.client != NOT_REPORTED) & (metrics.distinct_accounts >= minimum)].copy()


def rank_clients(metrics: pd.DataFrame, reach_weight: float) -> pd.DataFrame:
    if not 0 <= reach_weight <= 1:
        raise ValueError('reach_weight: expected 0–1')
    result = metrics.copy()
    score = pd.Series(0.0, index=result.index)
    for col, weight in [('affected_accounts', reach_weight), ('missing_recording_mbid', 1 - reach_weight)]:
        maximum = result[col].max() if len(result) else 0
        if maximum > 0:
            score += weight * result[col].map(math.log1p) / math.log1p(maximum)
    result['score'] = score
    result = result.sort_values(['score', 'missing_recording_mbid', 'client'], ascending=[False, False, True]).reset_index(drop=True)
    result.insert(0, 'rank', pd.Series(range(1, len(result) + 1), dtype='int64'))
    return result


def rank_sensitivity(metrics: pd.DataFrame, weights: list[float]) -> pd.DataFrame:
    result = [rank_clients(metrics, w)[['client', 'rank', 'score']].assign(reach_weight=w)
              for w in sorted(set(weights))]
    return pd.concat(result, ignore_index=True) if result else pd.DataFrame(columns=['client', 'rank', 'score', 'reach_weight'])


def estimate_scenarios(metrics: pd.DataFrame, clients: list[str], target: float) -> pd.DataFrame:
    if not 0 <= target <= 1:
        raise ValueError('target: expected 0–1')
    result = metrics.loc[metrics.client.isin(clients)].copy()
    result['target_coverage'] = target
    if result.empty:
        result['additional_tagged_listens'] = pd.Series(dtype='int64')
        return result
    result['additional_tagged_listens'] = result.apply(
        lambda r: round(min(r.missing_recording_mbid, max(0, target * r.total_listens - r.with_recording_mbid))), axis=1).astype('int64')
    return result.sort_values(['additional_tagged_listens', 'client'], ascending=[False, True])
