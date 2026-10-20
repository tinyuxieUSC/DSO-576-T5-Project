from datetime import date
from pathlib import Path
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from outreach.prepare import SCHEMA
from outreach.setup import PreparedDataset, DataFilters

@pytest.fixture
def fixture_data(tmp_path):
    records = [
        ('a1','alpha','1.0','01-01',10,10,'regular'),
        ('a1','alpha','1.0','01-02',5,5,'regular'),
        ('a2','alpha','1.1','01-02',10,0,'regular'),
        ('a3','alpha','1.1','01-03',5,5,'regular'),
        ('a10','alpha','1.1','01-03',1,1,'regular'),
        ('a4','beta','2.0','01-01',100,100,'regular'),
        ('a5','beta','2.0','01-02',40,20,'regular'),
        ('a6','beta','2.0','02-01',10,10,'regular'),
        ('a7','imp','1','01-01',1000,1000,'importer'),
        ('a8','imp','1','01-02',1000,1000,'importer'),
        ('a9','solo','1','01-01',500,500,'regular')]
    for i, (a,c,v,d,n,m,t) in enumerate(records):
        # SHA-like keys ensure the forced-spill path exercises prefix splitting.
        import hashlib
        row = dict(play_date=date.fromisoformat('2026-'+d), client=c, client_version=v,
                   account_key=hashlib.sha256(a.encode()).hexdigest(), client_type=t, listens=n,
                   valid_mbid_listens=n-m, missing_mbid_listens=m, invalid_mbid_listens=0)
        folder = tmp_path / f'play_month=2026-{d[:2]}'
        folder.mkdir(exist_ok=True)
        pq.write_table(pa.Table.from_pylist([row], schema=SCHEMA), folder/f'{i}.parquet')
    return PreparedDataset(tmp_path, 'fixture', 'sample', {}, 1024)

@pytest.fixture
def january():
    return DataFilters(date(2026,1,1), date(2026,1,31), True, 2)
