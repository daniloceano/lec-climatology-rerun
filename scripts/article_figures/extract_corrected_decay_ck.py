"""Read-only extraction of corrected per-timestep Ck for Supplementary Figure S4.

Run on the production host with the source on stdin, redirecting stdout to a
local ignored CSV. The program reads validated integrated results and frozen
period windows; it never modifies the production run.
"""
from __future__ import annotations

import csv
import math
import sqlite3
import sys
from pathlib import Path

PHASES = ['incipient', 'intensification', 'mature', 'decay']


def period_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline='') as handle:
        rows = list(csv.DictReader(handle))
    if not rows or not {'start', 'end'} <= rows[0].keys():
        raise ValueError(f'invalid period table: {path}')
    period_column = next(key for key in rows[0] if key not in {'start', 'end'})
    return [dict(period=row[period_column].strip().lower(), start=row['start'], end=row['end'])
            for row in rows if row[period_column].strip().lower() != 'residual']


def extract(run_root: Path, writer: csv.DictWriter) -> tuple[int, int]:
    if not (run_root / 'PRODUCTION_APPROVED').is_file():
        raise ValueError('corrected production run has not been approved')
    with (run_root / 'population_manifest.csv').open(newline='') as handle:
        population = list(csv.DictReader(handle))
    if len(population) != 3820:
        raise ValueError(f'expected 3820 validated cyclones, found {len(population)}')
    database = run_root / 'state.sqlite3'
    with sqlite3.connect(f'file:{database}?mode=ro', uri=True) as connection:
        states = {str(track_id): state for track_id, state in
                  connection.execute('SELECT track_id, state FROM cyclones')}
    if set(states) != {row['track_id'] for row in population} or set(states.values()) != {'COMPLETE'}:
        raise ValueError('production state does not match the approved population')
    accepted = 0
    for index, record in enumerate(population, 1):
        track_id = record['track_id']
        directory = run_root / 'lec_results' / f'{track_id}_ERA5_track'
        periods = period_rows(directory / 'periods.csv')
        if [row['period'] for row in periods] != PHASES:
            continue
        decay = periods[-1]
        with (directory / f'{track_id}_ERA5_track_results.csv').open(newline='') as handle:
            reader = csv.DictReader(handle)
            time_column = reader.fieldnames[0]
            if 'Ck' not in reader.fieldnames:
                raise ValueError(f'missing Ck for {track_id}')
            values = [float(row['Ck']) for row in reader
                      if decay['start'] <= row[time_column] <= decay['end']
                      and row['Ck'] and math.isfinite(float(row['Ck']))]
        if not values:
            raise ValueError(f'no corrected Ck values during decay for {track_id}')
        writer.writerow(dict(track_id=track_id, Ck_initial=values[0], Ck_final=values[-1], decay_points=len(values)))
        accepted += 1
        if index % 500 == 0:
            print(f'processed {index}/{len(population)}', file=sys.stderr, flush=True)
    return accepted, len(population)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit('usage: python - RUN_ROOT < extract_corrected_decay_ck.py > ck_corrected.csv')
    writer = csv.DictWriter(sys.stdout, fieldnames=['track_id', 'Ck_initial', 'Ck_final', 'decay_points'])
    writer.writeheader()
    accepted, population = extract(Path(sys.argv[1]), writer)
    print(f'extracted {accepted}/{population} complete four-phase cyclones', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
