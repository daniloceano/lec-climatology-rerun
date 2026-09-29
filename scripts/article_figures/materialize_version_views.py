#!/usr/bin/env python3
"""Materialize lossless ORIGINAL and CORRECTED views of comparison CSVs.

This script does not recompute scientific quantities. It copies rows from the
validated article-comparison tables according to their existing ``version``
field (``before`` or ``after``), retaining the original textual values.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


VERSIONED_TABLES = (
    "eof_extreme_assignments.csv",
    "eof_loadings_by_phase.csv",
    "eof_loadings_total.csv",
    "eof_scores_total.csv",
    "eof_variance_by_phase.csv",
    "eof_variance_total.csv",
    "intense_pc_cluster_assignments.csv",
    "intense_pc_cluster_centers.csv",
    "intense_pc_cluster_statistics.csv",
    "phase_statistics.csv",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def filter_table(source: Path, target: Path, version: str) -> int:
    with source.open(newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError(f"empty comparison table: {source}") from exc
        if "version" not in header:
            raise ValueError(f"comparison table lacks version column: {source}")
        version_index = header.index("version")
        rows = [row for row in reader if row[version_index] == version]
    if not rows:
        raise ValueError(f"no {version!r} rows in {source}")

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    return len(rows)


def write_view(root: Path, source_dir: Path, status: str, version: str) -> None:
    output_dir = root / "results" / status.lower() / "article"
    row_counts: dict[str, int] = {}
    source_hashes: dict[str, str] = {}
    output_hashes: dict[str, str] = {}
    for name in VERSIONED_TABLES:
        source = source_dir / name
        if not source.is_file():
            raise FileNotFoundError(f"expected comparison table is missing: {source}")
        target = output_dir / name
        row_counts[name] = filter_table(source, target, version)
        source_hashes[name] = sha256(source)
        output_hashes[name] = sha256(target)

    source_provenance = source_dir / "provenance.json"
    if not source_provenance.is_file():
        raise FileNotFoundError(f"expected comparison provenance is missing: {source_provenance}")
    provenance = {
        "scientific_status": status,
        "comparison_version": version,
        "method": "lossless row selection from validated comparison CSVs; no scientific recomputation",
        "source_directory": str(source_dir.relative_to(root)),
        "source_provenance": str(source_provenance.relative_to(root)),
        "source_provenance_sha256": sha256(source_provenance),
        "row_counts": row_counts,
        "source_sha256": source_hashes,
        "output_sha256": output_hashes,
    }
    (output_dir / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.output_root.resolve()
    source_dir = root / "results" / "comparison" / "article"
    write_view(root, source_dir, "ORIGINAL", "before")
    write_view(root, source_dir, "CORRECTED", "after")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
