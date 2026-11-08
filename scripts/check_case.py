"""Independent CSV counters versus app aggregates; publishes no account IDs."""
import csv
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'outreach-app'))
from outreach.setup import load_config, DataFilters
from outreach.prepare import prepare_data
from outreach.loader import get_client_metrics, get_data_status
from outreach.filters import estimate_scenarios

cfg = load_config(ROOT / 'outreach-app/config.cloud.toml')
source = cfg.inputs()[0]
groups = defaultdict(lambda: dict(total=0, valid=0, absent=0, invalid=0, accounts=set(), affected=set()))
dates = []
uuid = re.compile(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}')
with source.open(newline='') as f:
    for row in csv.DictReader(f):
        dates.append(datetime.fromtimestamp(float(row['timestamp']), timezone.utc).date())
        client = row['ai_submission_client'].strip().casefold() or 'NOT_REPORTED'
        if client in cfg.classification['importers'] or client == 'NOT_REPORTED':
            continue
        g = groups[client]
        g['total'] += 1
        value = row['ai_recording_mbid'].strip()
        status = 'valid' if uuid.fullmatch(value) else ('absent' if not value else 'invalid')
        g[status] += 1
        account = row['user_id'].strip()
        if account.isdigit() and int(account) > 0:
            g['accounts'].add(account)
            if status != 'valid':
                g['affected'].add(account)

prepared = prepare_data(cfg)
query = DataFilters(min(dates), max(dates), True, 100)
metrics = get_client_metrics(prepared, query).set_index('client')
eligible = {c: g for c, g in groups.items() if len(g['accounts']) >= 100}
assert set(metrics.index) == set(eligible)
for client, g in eligible.items():
    row = metrics.loc[client]
    assert (row.total_listens, row.with_recording_mbid, row.absent_recording_mbid,
            row.invalid_recording_mbid, row.distinct_accounts, row.affected_accounts) == (
        g['total'], g['valid'], g['absent'], g['invalid'], len(g['accounts']), len(g['affected']))
    assert row.coverage == g['valid']/g['total']

evidence = []
for client in ['navidrome', 'pano scrobbler']:
    g = eligible[client]
    for target in [.01, .75]:
        actual = int(estimate_scenarios(metrics.reset_index(), [client], target).iloc[0].additional_tagged_listens)
        needed = next(n for n in range(g['total'] - g['valid'] + 1)
                      if (g['valid'] + n)/g['total'] >= target)
        evidence.append(dict(client=client, total=g['total'], valid=g['valid'],
                             accounts=len(g['accounts']), affected=len(g['affected']),
                             target=target, app_additions=actual,
                             achieved_coverage=(g['valid'] + actual)/g['total'],
                             minimum_to_reach=needed))
result = dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              events=len(dates), start=str(min(dates)), end=str(max(dates)),
              eligible_clients=len(eligible), independent_aggregate_check='PASS',
              scenarios=evidence)
output = ROOT / 'cases/tinyu/calculation-evidence.json'
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
