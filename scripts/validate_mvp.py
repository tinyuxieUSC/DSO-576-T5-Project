"""Independent exact counters for the deployed sample, without publishing account IDs."""
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from fractions import Fraction
import csv, hashlib, json, math, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'outreach-app'))
from outreach.setup import load_config, DataFilters
from outreach.prepare import prepare_data
from outreach.loader import get_client_metrics, get_version_metrics, get_weekly_metrics
from outreach.filters import rank_clients, estimate_scenarios
cfg=load_config(ROOT/'outreach-app/config.cloud.toml')
source=cfg.inputs()[0];events=[];uuid=re.compile(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}')
with source.open(newline='') as f:
 for r in csv.DictReader(f):
  day=datetime.fromtimestamp(float(r['timestamp']),timezone.utc).date()
  client=r['ai_submission_client'].strip().casefold() or 'NOT_REPORTED'
  version=r['ai_submission_client_version'].strip() or 'NOT_REPORTED'
  mbid=r['ai_recording_mbid'].strip(); status='valid' if uuid.fullmatch(mbid) else ('absent' if not mbid else 'invalid')
  account=r['user_id'].strip();account=account if account.isdigit() and int(account)>0 else None
  events.append((day,client,version,status,account))
def count(rows,key):
 groups=defaultdict(lambda:dict(total_listens=0,with_recording_mbid=0,absent_recording_mbid=0,
                               invalid_recording_mbid=0,accounts=set(),affected=set()))
 for e in rows:
  g=groups[key(e)];g['total_listens']+=1
  g[{'valid':'with_recording_mbid','absent':'absent_recording_mbid','invalid':'invalid_recording_mbid'}[e[3]]]+=1
  if e[4]:
   g['accounts'].add(e[4])
   if e[3]!='valid':g['affected'].add(e[4])
 for g in groups.values():
  g['distinct_accounts']=len(g.pop('accounts'));g['affected_accounts']=len(g.pop('affected'))
  g['missing_recording_mbid']=g['absent_recording_mbid']+g['invalid_recording_mbid']
  g['coverage']=g['with_recording_mbid']/g['total_listens']
 return dict(groups)
def compare(table,expected,key):
 assert set(table[key])==set(expected)
 for _,row in table.iterrows():
  for column,value in expected[row[key]].items():
   assert math.isclose(row[column],value,rel_tol=1e-12,abs_tol=1e-12),(key,row[key],column,row[column],value)
prepared=prepare_data(cfg);start=min(e[0] for e in events);end=max(e[0] for e in events)
queries=[('default',DataFilters(start,end,True,100)),('include-importers',DataFilters(start,end,False,5)),
         ('single-playback-day',DataFilters(end,end,True,100)),('empty-threshold',DataFilters(start,end,True,10**8))]
results=[]
for name,q in queries:
 rows=[e for e in events if q.start<=e[0]<=q.end and (not q.exclude_importers or e[1] not in cfg.classification['importers'])]
 expected={k:v for k,v in count(rows,lambda e:e[1]).items() if k!='NOT_REPORTED' and v['distinct_accounts']>=q.minimum_accounts}
 actual=get_client_metrics(prepared,q);compare(actual,expected,'client')
 ranks=rank_clients(actual,.5)
 if expected:
  max_reach=max(g['affected_accounts'] for g in expected.values());max_gap=max(g['missing_recording_mbid'] for g in expected.values())
  scores={c:sum(.5*math.log(1+g[col])/math.log(1+maximum) if maximum else 0
                 for col,maximum in [('affected_accounts',max_reach),('missing_recording_mbid',max_gap)]) for c,g in expected.items()}
  order=sorted(expected,key=lambda c:(-scores[c],-expected[c]['missing_recording_mbid'],c))
  assert list(ranks.client)==order
  for _,r in ranks.iterrows():assert math.isclose(r.score,scores[r.client],abs_tol=1e-12)
 if name=='default':
  for client in expected:
   subset=[e for e in rows if e[1]==client]
   compare(get_version_metrics(prepared,q,client),count(subset,lambda e:e[2]),'client_version')
   weeks=get_weekly_metrics(prepared,q,client)
   compare(weeks[weeks.total_listens.notna()],count(subset,lambda e:e[0]-timedelta(days=e[0].weekday())),'week_start')
  scenarios=[]
  for percent in [1,75,100]:
   table=estimate_scenarios(actual,list(expected),percent/100)
   for _,r in table.iterrows():
    g=expected[r.client]; n=g['total_listens'];v=g['with_recording_mbid'];gap=g['missing_recording_mbid'];target=Fraction(percent,100)
    nearest=round(min(Fraction(gap),max(Fraction(0),target*n-v)))
    minimum=next(k for k in range(gap+1) if Fraction(v+k,n)>=target)
    assert r.additional_tagged_listens==nearest
    assert r.minimum_additions_to_target==minimum
    assert math.isclose(r.achieved_coverage,float(Fraction(v+nearest,n)),abs_tol=1e-12)
   scenarios.append(dict(target_percent=percent,clients_checked=len(table)))
  default_table=actual.to_dict('records');default_ranks=ranks[['rank','client','score']].to_dict('records')
 results.append(dict(name=name,eligible_clients=len(expected),aggregate_and_rank_check='PASS'))
whole=count(events,lambda e:'source')['source']
output=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),events=len(events),
            start=str(start),end=str(end),source_totals=whole,queries=results,
            version_and_measured_week_checks='PASS for every default eligible client',
            scenario_checks=scenarios,default_metrics=default_table,default_ranking=default_ranks)
path=ROOT/'evidence/mvp-numbers.json';path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps(output,indent=2,default=str)+'\n')
print(json.dumps({k:v for k,v in output.items() if k not in ['default_metrics','default_ranking']},indent=2))
