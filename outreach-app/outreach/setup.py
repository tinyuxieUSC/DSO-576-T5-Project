"""Configuration, contracts and UI controls; no listening-file access."""
from __future__ import annotations
import argparse
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import tomllib

@dataclass(frozen=True)
class DataFilters:
    start: date
    end: date
    exclude_importers: bool = True
    minimum_accounts: int = 100

    def __post_init__(self):
        if self.start > self.end:
            raise ValueError('start/end: start must be on or before end; choose an inclusive UTC range')
        if type(self.minimum_accounts) is not int or self.minimum_accounts < 0:
            raise ValueError(f'minimum_accounts={self.minimum_accounts!r}: expected a nonnegative integer')

@dataclass
class AppConfig:
    path: Path
    paths: dict
    preparation: dict
    defaults: dict
    aliases: dict
    classification: dict

    @property
    def mode(self):
        return self.preparation['mode']

    def local_path(self, name):
        return (self.path.parent / self.paths[name]).resolve()

    def inputs(self):
        root = self.local_path('dataset_root')
        names = [self.paths['sample_input']] if self.mode == 'sample' else self.paths['full_inputs']
        return [(root / p).resolve() for p in names]

    def policy(self):
        return {'rules_version': self.preparation['rules_version'], 'aliases': self.aliases,
                'classification': self.classification}

@dataclass(frozen=True)
class PreparedDataset:
    path: Path
    fingerprint: str
    mode: str
    manifest: dict
    memory_budget_mb: int = 1024
    key_set_allowance: int = 200000
    minimum_accounts_floor: int = 1

@dataclass(frozen=True)
class DataStatus:
    mode: str
    fingerprint: str
    start: date
    end: date
    accepted: int
    warnings: list[str]
    provenance: dict


def canonical_name(value):
    return value.strip().casefold()


def load_config(path='config.toml', mode=None):
    path = Path(path).resolve()
    with path.open('rb') as f:
        raw = tomllib.load(f)
    for section in ('paths', 'preparation', 'defaults', 'classification', 'aliases'):
        if section not in raw:
            raise ValueError(f'{section}: missing configuration section; restore it from config.toml')
    p, d = raw['preparation'], raw['defaults']
    for key in ('dataset_root', 'prepared_root', 'secret_file', 'sample_input'):
        value = raw['paths'].get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'paths.{key}={value!r}: expected a nonempty path string')
    full_inputs = raw['paths'].get('full_inputs')
    if not isinstance(full_inputs, list) or not full_inputs or any(not isinstance(v, str) or not v.strip() for v in full_inputs):
        raise ValueError(f'paths.full_inputs={full_inputs!r}: expected a nonempty list of extracted file paths')
    for group in ('importers', 'regular_clients'):
        values = raw['classification'].get(group)
        if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values):
            raise ValueError(f'classification.{group}={values!r}: expected a list of nonblank exact client names')
    if any(not isinstance(v, str) or not v.strip() or not k.strip() for k, v in raw['aliases'].items()):
        raise ValueError('aliases: expected nonblank client-name strings on both sides')
    if mode is not None:
        p['mode'] = mode
    if p.get('mode') not in ('sample', 'full'):
        raise ValueError(f"preparation.mode={p.get('mode')!r}: expected sample or full")
    for container, key, floor in [(p, 'chunk_size', 1), (d, 'minimum_accounts', 0),
                                  (d, 'minimum_accounts_floor', 1), (d, 'query_memory_budget_mb', 1),
                                  (d, 'shortlist_size', 1)]:
        v = container.get(key)
        if type(v) is not int or v < floor:
            raise ValueError(f'{key}={v!r}: expected integer >= {floor}; edit config.toml')
    for key in ('reach_weight', 'target_coverage'):
        v = d.get(key)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 1:
            raise ValueError(f'{key}={v!r}: expected a fraction between 0 and 1')
    if type(d.get('exclude_importers')) is not bool:
        raise ValueError('exclude_importers: expected true or false')
    if d.get('date_range') != 'observed_bounds':
        raise ValueError('date_range: expected observed_bounds; choose dates in the dashboard')
    if d.get('initial_tab') != 'Shortlist':
        raise ValueError('initial_tab: expected Shortlist')
    aliases = {canonical_name(k): canonical_name(v) for k, v in raw['aliases'].items()}
    for key in aliases:
        seen, current = set(), key
        while current in aliases:
            if current in seen:
                raise ValueError(f'aliases: cycle at {key!r}; use acyclic explicit aliases')
            seen.add(current)
            current = aliases[current]
        if not current:
            raise ValueError(f'aliases.{key}: destination cannot be blank')
        aliases[key] = current
    groups = {k: sorted({aliases.get(canonical_name(v), canonical_name(v)) for v in raw['classification'].get(k, [])})
              for k in ('importers', 'regular_clients')}
    overlap = set(groups['importers']) & set(groups['regular_clients'])
    if overlap:
        raise ValueError(f'classification overlap={sorted(overlap)}: assign each client one type')
    return AppConfig(path, raw['paths'], p, d, aliases, groups)


def cli_args():
    p = argparse.ArgumentParser()
    p.add_argument('--config', default='config.toml')
    p.add_argument('--mode', choices=['sample', 'full'])
    return p.parse_args()
