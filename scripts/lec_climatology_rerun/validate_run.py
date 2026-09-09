#!/usr/bin/env python3
"""Validate a complete rerun against its manifest, state database, and outputs."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.lec_climatology_rerun.common import (  # noqa: E402
    RunConfig,
    read_track_times,
    validate_lec_output,
)


def validate_one(arguments: tuple[str, str]) -> tuple[str, str | None]:
    run_root, track_id = arguments
    config = RunConfig.load(run_root)
    try:
        validate_lec_output(
            config.results_dir / f"{track_id}_ERA5_track",
            track_id,
            read_track_times(config.tracks_dir / f"track_{track_id}.txt"),
            config.phase_windows_dir / f"{track_id}.csv",
        )
    except Exception as exc:  # returned to the parent for a complete report
        return track_id, str(exc)
    return track_id, None


def audit(run_root: Path, workers: int = 1, quick: bool = False) -> dict:
    config = RunConfig.load(run_root)
    provenance = json.loads((run_root / "provenance.json").read_text())
    manifest = pd.read_csv(config.manifest, dtype={"track_id": str})
    manifest_ids = set(manifest["track_id"])

    connection = sqlite3.connect(f"file:{config.db}?mode=ro", uri=True)
    rows = list(connection.execute("SELECT track_id,state FROM cyclones"))
    connection.close()
    database_ids = {str(track_id) for track_id, _ in rows}
    complete_ids = sorted(str(track_id) for track_id, state in rows if state == "COMPLETE")
    states: dict[str, int] = {}
    for _, state in rows:
        states[state] = states.get(state, 0) + 1
    result_ids = {
        path.name.removesuffix("_ERA5_track")
        for path in config.results_dir.glob("*_ERA5_track")
        if path.is_dir()
    }

    structural = {
        "manifest_rows": len(manifest),
        "manifest_unique_track_ids": len(manifest_ids),
        "states": states,
        "manifest_only_database": sorted(manifest_ids - database_ids),
        "database_only_manifest": sorted(database_ids - manifest_ids),
        "complete_without_result_directory": sorted(set(complete_ids) - result_ids),
        "result_directory_not_complete": sorted(result_ids - set(complete_ids)),
    }
    target = provenance.get("population", {}).get("selected_cyclones")
    if target != len(manifest_ids):
        raise RuntimeError(
            f"provenance target {target} differs from manifest {len(manifest_ids)}"
        )
    if states != {"COMPLETE": target}:
        raise RuntimeError(f"rerun is incomplete: {states}; expected COMPLETE={target}")
    if any(structural[key] for key in (
        "manifest_only_database",
        "database_only_manifest",
        "complete_without_result_directory",
        "result_directory_not_complete",
    )):
        raise RuntimeError(f"manifest/state/artifact mismatch: {structural}")

    errors: list[tuple[str, str]] = []
    if not quick:
        arguments = [(str(run_root), track_id) for track_id in complete_ids]
        if workers == 1:
            checked = map(validate_one, arguments)
        else:
            executor = ProcessPoolExecutor(max_workers=workers)
            checked = executor.map(validate_one, arguments, chunksize=10)
        try:
            errors = [(track_id, error) for track_id, error in checked if error]
        finally:
            if workers != 1:
                executor.shutdown()
        if errors:
            raise RuntimeError(f"{len(errors)} invalid COMPLETE outputs; first: {errors[:5]}")

    return {
        **structural,
        "run_root": str(run_root.resolve()),
        "toolkit_commit": provenance.get("toolkit_commit"),
        "population_sha256": provenance.get("population", {}).get("sha256"),
        "deep_outputs_validated": 0 if quick else len(complete_ids),
        "validation_errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--quick", action="store_true",
        help="check manifest/state/result-directory consistency without opening every output",
    )
    args = parser.parse_args()
    print(json.dumps(audit(args.run_root, max(1, args.workers), args.quick), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
