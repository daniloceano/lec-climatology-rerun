"""Canonical reference-identity EOF product for Figures 5–8 only.

Raw eigenvalue rank is never used as a scientific identity here. Each phase
has its own decomposition and its own eight-mode assignment in common.py.
The compatibility article CSVs retain ``eof`` as a reference-identity alias;
new products use ``reference_eof``, ``raw_rank`` and ``sign_alignment``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.article_figures.common import (
    EOF_TERMS, PHASES, independent_eof_by_phase, primary_phase_rows, sha256_file,
)

PRODUCT_DIRECTORY = Path("results/comparison/article/phase_eof_matched")


def matched_phase_eofs(legacy: pd.DataFrame, corrected: pd.DataFrame):
    """Return explicit matched loadings, variance and corrected reference PCs."""
    primary = [primary_phase_rows(frame) for frame in (legacy, corrected)]
    for frame in primary:
        frame["track_id"] = pd.to_numeric(frame["track_id"], errors="raise").astype("int64")
        if frame.duplicated(["track_id", "phase"]).any():
            raise ValueError("duplicate primary cyclone-phase observations")
    loadings, variance, scores, mapping = independent_eof_by_phase(
        *primary, return_details=True
    )
    keys = ["scope", "reference_eof", "version"]
    loadings = loadings.rename(columns={"eof": "reference_eof"}).merge(
        mapping, on=keys, validate="many_to_one"
    )
    variance = variance.rename(columns={"eof": "reference_eof"}).drop(
        columns="matched_rank"
    ).merge(mapping, on=keys, validate="one_to_one")
    validate_phase_product(loadings, variance)
    return loadings, variance, scores


def validate_phase_product(loadings: pd.DataFrame, variance: pd.DataFrame) -> None:
    """Fail closed if a caller supplies raw tables or mixes rank and identity."""
    keys = ["scope", "reference_eof", "version"]
    metadata = ["raw_rank", "sign_alignment"]
    for frame in (loadings, variance):
        missing = set(keys + metadata) - set(frame.columns)
        if missing or "eof" in frame.columns:
            raise ValueError(f"expected explicit reference EOF product; missing {sorted(missing)}")
        if set(frame.scope) != set(PHASES) or set(frame.version) != {"before", "after"}:
            raise ValueError("expected both versions of all four phase decompositions")
    if variance.duplicated(keys).any() or loadings.duplicated(keys + ["term"]).any():
        raise ValueError("duplicate phase EOF rows")
    for (_, version), block in variance.groupby(["scope", "version"]):
        if sorted(block.reference_eof) != list(range(1, 9)) or sorted(block.raw_rank) != list(range(1, 9)):
            raise ValueError("phase EOF matching must be one-to-one over eight modes")
        if not block.sign_alignment.isin([-1, 1]).all():
            raise ValueError("invalid sign alignment")
        if version == "before" and not (block.reference_eof == block.raw_rank).all():
            raise ValueError("published reference identity must equal published raw rank")
    for _, block in loadings.groupby(keys):
        if set(block.term) != set(EOF_TERMS):
            raise ValueError("incomplete phase loading pattern")
    joined = loadings.merge(variance[keys + metadata], on=keys, suffixes=("", "_variance"), validate="many_to_one")
    if len(joined) != len(loadings) or len(loadings) != len(variance) * len(EOF_TERMS):
        raise ValueError("incomplete loading/variance correspondence")
    for column in metadata:
        if not (joined[column] == joined[column + "_variance"]).all():
            raise ValueError("loading and variance mode metadata disagree")
    if not np.isfinite(loadings.loading).all() or not np.isfinite(variance.explained_variance_pct).all():
        raise ValueError("non-finite phase EOF product")


def compatibility_tables(loadings: pd.DataFrame, variance: pd.DataFrame):
    """Lossless adapter for older article tables; eof is reference identity."""
    validate_phase_product(loadings, variance)
    return (
        loadings.rename(columns={"reference_eof": "eof"})[
            ["scope", "eof", "version", "term", "loading"]
        ],
        variance.rename(columns={"reference_eof": "eof", "raw_rank": "matched_rank"})[
            ["scope", "eof", "version", "n", "explained_variance_pct", "matched_rank", "pattern_correlation"]
        ],
    )


def load_pinned_phase_inputs(root: Path, corrected_path: Path | None = None):
    """Use only the inputs explicitly pinned by the existing article provenance."""
    provenance = json.loads((root / "results/comparison/article/provenance.json").read_text())
    frames, sources = [], {}
    for version, key, count in (("before", "legacy_cache", (6789, 25000)), ("after", "corrected_cache", (3820, 15829))):
        path = corrected_path if key == "corrected_cache" and corrected_path is not None else Path(provenance[key])
        expected = provenance[key + "_sha256"]
        if sha256_file(path) != expected:
            raise ValueError(f"pinned {key} hash mismatch: {path}")
        frame = pd.read_parquet(path)
        if (frame.track_id.nunique(), len(frame)) != count:
            raise ValueError(f"unexpected {key} population")
        frames.append(frame)
        sources[version] = {"path": str(path.resolve()), "sha256": expected}
    return *frames, sources


def write_phase_product(root: Path, loadings: pd.DataFrame, variance: pd.DataFrame) -> None:
    validate_phase_product(loadings, variance)
    directory = root / PRODUCT_DIRECTORY
    directory.mkdir(parents=True, exist_ok=True)
    # Same precision as existing article CSVs. Both renderers read these files.
    loadings.to_csv(directory / "loadings.csv", index=False, float_format="%.8g")
    variance.to_csv(directory / "variance.csv", index=False, float_format="%.8g")


def read_phase_product(root: Path):
    directory = root / PRODUCT_DIRECTORY
    loadings = pd.read_csv(directory / "loadings.csv")
    variance = pd.read_csv(directory / "variance.csv")
    validate_phase_product(loadings, variance)
    return loadings, variance
