"""Independently verify reach distributions and all-client rank sensitivities."""
from collections import Counter, defaultdict
from datetime import date
from fractions import Fraction
import csv,json,math,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'outreach-app'))
from outreach.setup import DataFilters,load_config
from outreach.prepare import prepare_data
from outreach.loader import get_client_metrics,get_account_distribution,get_version_metrics
from outreach.filters import ranking_comparison
cfg=load_config(ROOT/'outreach-app/config.cloud.toml');q=DataFilters(date(2005,2,13),date(2026,9,3),True,100)
source=cfg.inputs()[0]; per_account=defaultdict(Counter); rows=Counter(); versions=defaultdict(Counter)
pattern=re.compile(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}')
from datetime import datetime,timezone
with source.open(newline='') as f:
 for r in csv.DictReader(f):
  d=datetime.fromtimestamp(float(r['timestamp']),timezone.utc).date()
  client=r['ai_submission_client'].strip().casefold() or 'NOT_REPORTED'
  if not q.start<=d<=q.end or client in cfg.classification['importers']:continue
  account=r['user_id'].strip();account=account if account.isdigit() and int(account)>0 else None
  missing=not bool(pattern.fullmatch(r['ai_recording_mbid'].strip()))
  rows[client]+=int(missing)
  versions[client][r['ai_submission_client_version'].strip() or 'NOT_REPORTED']+=int(missing)
  if account:per_account[client][account]+=int(missing)
data=prepare_data(cfg);metrics=get_client_metrics(data,q);comparison=ranking_comparison(metrics).set_index('client')
accounts={};score_input={}
for _,row in metrics.iterrows():
 c=row.client;counts=per_account[c]; dist=dict(zero=sum(v==0 for v in counts.values()),one=sum(v==1 for v in counts.values()),multiple=sum(v>1 for v in counts.values()))
 assert get_account_distribution(data,q,c)==dist
 assert dist['zero']+dist['one']+dist['multiple']==row.distinct_accounts
 assert dist['one']+dist['multiple']==row.affected_accounts
 vtable=get_version_metrics(data,q,c)
 assert {r.client_version:int(r.missing_recording_mbid) for _,r in vtable.iterrows()}==dict(versions[c])
 accounts[c]=dist;score_input[c]=(sum(v>0 for v in counts.values()),rows[c])
max_reach=max(x[0] for x in score_input.values());max_gap=max(x[1] for x in score_input.values())
for weight,col in [(0,'rank_0'),(.5,'rank_50'),(1,'rank_100')]:
 score={c:weight*math.log(1+r)/math.log(1+max_reach)+(1-weight)*math.log(1+g)/math.log(1+max_gap) for c,(r,g) in score_input.items()}
 order=sorted(score,key=lambda c:(-score[c],-score_input[c][1],c))
 assert [int(comparison.loc[c,col]) for c in order]==list(range(1,len(order)+1))
assert accounts['navidrome']=={'zero':401,'one':279,'multiple':39}
result=dict(account_distribution=accounts,rankings={c:{k:int(comparison.loc[c,k]) for k in ['rank_0','rank_50','rank_100']} for c in comparison.index},version_gap_reconciliation='PASS',method='Independent CSV counters by client, version and pseudonymous account; separate log-rank computation',status='PASS')
p=ROOT/'evidence/team-findings.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
