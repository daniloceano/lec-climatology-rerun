"""Scientific data preparation shared by the corrected article figures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter
from scipy.optimize import linear_sum_assignment

PHASES = ["incipient", "intensification", "mature", "decay"]
PHASE_COLORS = {
    "incipient": "#65a1e6",
    "intensification": "#f7b538",
    "mature": "#d62828",
    "decay": "#9aa981",
}

ENERGY_TERMS = ["Az", "Ae", "Kz", "Ke"]
CONVERSION_TERMS = ["Cz", "Ca", "Ck", "Ce"]
BOUNDARY_TERMS = ["BAz", "BAe", "BKz", "BKe"]
PRESSURE_TERMS = ["BΦZ", "BΦE"]
GENERATION_TERMS = ["Gz", "Ge", "RGz", "RKz", "RGe", "RKe"]
TENDENCY_TERMS = [
    "∂Az/∂t (finite diff.)",
    "∂Ae/∂t (finite diff.)",
    "∂Kz/∂t (finite diff.)",
    "∂Ke/∂t (finite diff.)",
]
EOF_TERMS = (
    ENERGY_TERMS
    + CONVERSION_TERMS
    + BOUNDARY_TERMS
    + PRESSURE_TERMS
    + ["Gz", "Ge"]
    + TENDENCY_TERMS
    + ["RGz", "RKz", "RGe", "RKe"]
)
CLUSTER_TERMS = ["Ck", "Ca", "Ke", "Ge", "BKe", "BAe"]

# Exact genesis boxes used by the published workflow.
REGIONS = {
    "SE-BR": (-52.0, -38.0, -37.0, -23.0),
    "LA-PLATA": (-69.0, -38.0, -52.0, -23.0),
    "ARG": (-70.0, -55.0, -50.0, -39.0),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_inputs(cache_path: Path, tracks_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    cache = pd.read_parquet(cache_path)
    tracks = pd.read_csv(tracks_path)
    required_cache = {"track_id", "period", "phase", *EOF_TERMS}
    required_tracks = {"track_id", "date", "lon vor", "lat vor", "vor42"}
    missing_cache = sorted(required_cache - set(cache.columns))
    missing_tracks = sorted(required_tracks - set(tracks.columns))
    if missing_cache:
        raise ValueError(f"corrected cache misses columns: {missing_cache}")
    if missing_tracks:
        raise ValueError(f"track table misses columns: {missing_tracks}")

    cache = cache[cache["phase"].isin(PHASES)].copy()
    # The published main panels use the primary four-stage lifecycle. Secondary
    # periods ("intensification 2", etc.) remain in the corrected cache for
    # provenance but belong to separate supplementary analyses.
    cache = cache[cache["period"].astype(str).eq(cache["phase"])].copy()
    cache["track_id"] = pd.to_numeric(cache["track_id"], errors="raise").astype("int64")
    tracks["track_id"] = pd.to_numeric(tracks["track_id"], errors="raise").astype("int64")
    tracks["date"] = pd.to_datetime(tracks["date"], errors="raise")
    tracks["lon vor"] = np.where(tracks["lon vor"] > 180, tracks["lon vor"] - 360, tracks["lon vor"])

    counts = cache.groupby("track_id")["phase"].agg(lambda values: set(values))
    invalid = counts[counts.map(set(PHASES).issubset).eq(False)]
    if not invalid.empty:
        raise ValueError(f"{len(invalid)} corrected cyclones lack a canonical phase")
    if cache["track_id"].nunique() != 3820:
        raise ValueError(
            f"expected 3820 corrected cyclones, got {cache['track_id'].nunique()}"
        )
    if len(cache) != 3820 * len(PHASES):
        raise ValueError(f"expected one primary row per cyclone-phase, got {len(cache)} rows")
    return cache, tracks


def load_comparison_inputs(
    legacy_cache_path: Path,
    corrected_cache_path: Path,
    tracks_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load an exactly paired four-phase legacy/corrected population."""
    corrected, tracks = load_inputs(corrected_cache_path, tracks_path)
    legacy = pd.read_parquet(legacy_cache_path)
    missing = sorted({"track_id", "period", "phase", *EOF_TERMS} - set(legacy.columns))
    if missing:
        raise ValueError(f"legacy cache misses columns: {missing}")
    legacy["track_id"] = pd.to_numeric(legacy["track_id"], errors="raise").astype("int64")
    ids = set(corrected["track_id"])
    legacy = legacy[
        legacy["track_id"].isin(ids)
        & legacy["phase"].isin(PHASES)
        & legacy["period"].astype(str).eq(legacy["phase"])
    ].copy()
    keys = ["track_id", "phase"]
    if legacy.duplicated(keys).any():
        raise ValueError("legacy cache has duplicate primary cyclone-phase rows")
    if len(legacy) != 3820 * len(PHASES) or legacy["track_id"].nunique() != 3820:
        raise ValueError(
            f"expected 15,280 paired legacy rows for 3,820 cyclones, got "
            f"{len(legacy):,} rows for {legacy['track_id'].nunique():,} cyclones"
        )
    legacy_keys = set(map(tuple, legacy[keys].to_numpy()))
    corrected_keys = set(map(tuple, corrected[keys].to_numpy()))
    if legacy_keys != corrected_keys:
        raise ValueError("legacy and corrected cyclone-phase keys differ")
    return legacy.sort_values(keys).reset_index(drop=True), corrected.sort_values(keys).reset_index(drop=True), tracks


def load_article_comparison_inputs(
    legacy_cache_path: Path,
    corrected_cache_path: Path,
    tracks_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the independent populations used by the article and corrected rerun.

    Unlike :func:`load_comparison_inputs`, this loader deliberately does not
    restrict the legacy population to corrected IDs.  The legacy side keeps
    all 6,789 cyclones and every archived lifecycle period, which is the input
    definition that reproduces the published total-lifecycle EOF variance.
    The corrected side keeps all archived periods for the 3,820 validated
    reruns.  Figure-specific primary-phase filtering is applied downstream.
    """
    legacy = pd.read_parquet(legacy_cache_path)
    corrected = pd.read_parquet(corrected_cache_path)
    tracks = pd.read_csv(tracks_path)

    required_cache = {"track_id", "period", "phase", *EOF_TERMS}
    required_tracks = {"track_id", "date", "lon vor", "lat vor", "vor42"}
    for label, frame in (("legacy", legacy), ("corrected", corrected)):
        missing = sorted(required_cache - set(frame.columns))
        if missing:
            raise ValueError(f"{label} cache misses columns: {missing}")
        frame["track_id"] = pd.to_numeric(frame["track_id"], errors="raise").astype("int64")
    missing_tracks = sorted(required_tracks - set(tracks.columns))
    if missing_tracks:
        raise ValueError(f"track table misses columns: {missing_tracks}")

    tracks["track_id"] = pd.to_numeric(tracks["track_id"], errors="raise").astype("int64")
    tracks["date"] = pd.to_datetime(tracks["date"], errors="raise")
    tracks["lon vor"] = np.where(tracks["lon vor"] > 180, tracks["lon vor"] - 360, tracks["lon vor"])

    expected = {
        "legacy": (6789, 25000),
        "corrected": (3820, 15829),
    }
    for label, frame in (("legacy", legacy), ("corrected", corrected)):
        expected_ids, expected_rows = expected[label]
        if frame["track_id"].nunique() != expected_ids or len(frame) != expected_rows:
            raise ValueError(
                f"expected {expected_rows:,} {label} rows for {expected_ids:,} cyclones, "
                f"got {len(frame):,} rows for {frame['track_id'].nunique():,} cyclones"
            )
    return legacy.copy(), corrected.copy(), tracks


def primary_phase_rows(cache: pd.DataFrame) -> pd.DataFrame:
    """Return exact primary incipient/intensification/mature/decay records."""
    return cache[
        cache["phase"].isin(PHASES)
        & cache["period"].astype(str).eq(cache["phase"].astype(str))
    ].copy()


def phase_statistics(cache: pd.DataFrame) -> pd.DataFrame:
    terms = [term for term in EOF_TERMS if term in cache]
    rows: list[dict] = []
    for phase in PHASES:
        block = cache[cache["phase"] == phase]
        for term in terms:
            values = pd.to_numeric(block[term], errors="coerce").dropna()
            rows.append(
                {
                    "phase": phase,
                    "term": term,
                    "n": int(values.size),
                    "mean": float(values.mean()),
                    "std": float(values.std(ddof=1)),
                    "median": float(values.median()),
                    "q25": float(values.quantile(0.25)),
                    "q75": float(values.quantile(0.75)),
                }
            )
    return pd.DataFrame(rows)


def compute_eof(frame: pd.DataFrame, terms: list[str], n_modes: int = 8):
    """Correlation-matrix EOFs with loadings and unit-variance PC scores."""
    clean = frame[terms].astype(float).replace([np.inf, -np.inf], np.nan).dropna()
    if len(clean) < max(10, len(terms) + 1):
        raise ValueError(f"too few complete rows for EOF: {len(clean)}")
    means = clean.mean(axis=0)
    std = clean.std(axis=0, ddof=1)
    if (std == 0).any():
        raise ValueError(f"constant EOF terms: {std[std == 0].index.tolist()}")
    standardized = (clean - means) / std
    covariance = np.cov(standardized.to_numpy(), rowvar=False, ddof=1)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1][:n_modes]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]

    loadings = (eigenvectors * np.sqrt(eigenvalues)).T
    dominant = np.take_along_axis(
        loadings, np.abs(loadings).argmax(axis=1)[:, None], axis=1
    ).ravel()
    signs = np.where(dominant < 0, -1.0, 1.0)
    loadings = loadings * signs[:, None]
    eigenvectors = eigenvectors * signs[None, :]
    scores = standardized.to_numpy() @ eigenvectors / np.sqrt(eigenvalues)[None, :]
    variance = eigenvalues / np.trace(covariance)
    return clean.index, loadings, scores, variance


def align_eofs(
    legacy_loadings: np.ndarray,
    corrected_loadings: np.ndarray,
    corrected_scores: np.ndarray,
    corrected_variance: np.ndarray,
):
    """Match corrected modes to legacy modes and align their arbitrary signs."""
    correlation = np.corrcoef(legacy_loadings, corrected_loadings)[
        : len(legacy_loadings), len(legacy_loadings) :
    ]
    rows, columns = linear_sum_assignment(-np.abs(correlation))
    order = columns[np.argsort(rows)]
    signs = np.sign(correlation[np.arange(len(order)), order])
    signs[signs == 0] = 1.0
    return (
        corrected_loadings[order] * signs[:, None],
        corrected_scores[:, order] * signs[None, :],
        corrected_variance[order],
        order + 1,
        correlation[np.arange(len(order)), order] * signs,
    )


def paired_eof_by_phase(legacy: pd.DataFrame, corrected: pd.DataFrame, n_modes: int = 8):
    loading_rows: list[dict] = []
    variance_rows: list[dict] = []
    for phase in PHASES:
        left = legacy[legacy["phase"] == phase].set_index("track_id").sort_index()
        right = corrected[corrected["phase"] == phase].set_index("track_id").sort_index()
        common = left.index.intersection(right.index)
        left = left.loc[common]
        right = right.loc[common]
        _, legacy_loadings, _, legacy_variance = compute_eof(left, EOF_TERMS, n_modes)
        _, corrected_loadings, corrected_scores, corrected_variance = compute_eof(
            right, EOF_TERMS, n_modes
        )
        corrected_loadings, _, corrected_variance, ranks, correlations = align_eofs(
            legacy_loadings, corrected_loadings, corrected_scores, corrected_variance
        )
        for mode in range(n_modes):
            variance_rows.extend(
                [
                    {
                        "scope": phase,
                        "eof": mode + 1,
                        "version": "before",
                        "n": len(common),
                        "explained_variance_pct": 100 * legacy_variance[mode],
                        "matched_rank": mode + 1,
                        "pattern_correlation": 1.0,
                    },
                    {
                        "scope": phase,
                        "eof": mode + 1,
                        "version": "after",
                        "n": len(common),
                        "explained_variance_pct": 100 * corrected_variance[mode],
                        "matched_rank": int(ranks[mode]),
                        "pattern_correlation": float(correlations[mode]),
                    },
                ]
            )
            for term_index, term in enumerate(EOF_TERMS):
                loading_rows.extend(
                    [
                        {
                            "scope": phase,
                            "eof": mode + 1,
                            "version": "before",
                            "term": term,
                            "loading": float(legacy_loadings[mode, term_index]),
                        },
                        {
                            "scope": phase,
                            "eof": mode + 1,
                            "version": "after",
                            "term": term,
                            "loading": float(corrected_loadings[mode, term_index]),
                        },
                    ]
                )
    return pd.DataFrame(loading_rows), pd.DataFrame(variance_rows)


def paired_total_eof(legacy: pd.DataFrame, corrected: pd.DataFrame, n_modes: int = 8):
    left = legacy.groupby("track_id", sort=True)[EOF_TERMS].mean()
    right = corrected.groupby("track_id", sort=True)[EOF_TERMS].mean()
    common = left.index.intersection(right.index)
    left = left.loc[common]
    right = right.loc[common]
    _, legacy_loadings, legacy_scores, legacy_variance = compute_eof(left, EOF_TERMS, n_modes)
    _, corrected_loadings, corrected_scores, corrected_variance = compute_eof(
        right, EOF_TERMS, n_modes
    )
    corrected_loadings, corrected_scores, corrected_variance, ranks, correlations = align_eofs(
        legacy_loadings, corrected_loadings, corrected_scores, corrected_variance
    )

    def loading_frame(values: np.ndarray, version: str) -> pd.DataFrame:
        rows = []
        for mode in range(n_modes):
            for index, term in enumerate(EOF_TERMS):
                rows.append(
                    {"version": version, "eof": mode + 1, "term": term, "loading": values[mode, index]}
                )
        return pd.DataFrame(rows)

    def score_frame(values: np.ndarray, version: str) -> pd.DataFrame:
        frame = pd.DataFrame(values, columns=[f"PC{i + 1}" for i in range(n_modes)])
        frame.insert(0, "track_id", common.to_numpy(dtype="int64"))
        frame.insert(1, "version", version)
        return frame

    variance_rows = []
    for mode in range(n_modes):
        variance_rows.extend(
            [
                {
                    "scope": "total", "eof": mode + 1, "version": "before", "n": len(common),
                    "explained_variance_pct": 100 * legacy_variance[mode], "matched_rank": mode + 1,
                    "pattern_correlation": 1.0,
                },
                {
                    "scope": "total", "eof": mode + 1, "version": "after", "n": len(common),
                    "explained_variance_pct": 100 * corrected_variance[mode],
                    "matched_rank": int(ranks[mode]), "pattern_correlation": float(correlations[mode]),
                },
            ]
        )
    return (
        pd.concat([loading_frame(legacy_loadings, "before"), loading_frame(corrected_loadings, "after")]),
        pd.DataFrame(variance_rows),
        pd.concat([score_frame(legacy_scores, "before"), score_frame(corrected_scores, "after")]),
    )


def independent_eof_by_phase(
    legacy: pd.DataFrame,
    corrected: pd.DataFrame,
    n_modes: int = 8,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit phase EOFs to the full, independent before and after populations."""
    loading_rows: list[dict] = []
    variance_rows: list[dict] = []
    for phase in PHASES:
        left = legacy[legacy["phase"] == phase].set_index("track_id").sort_index()
        right = corrected[corrected["phase"] == phase].set_index("track_id").sort_index()
        _, legacy_loadings, _, legacy_variance = compute_eof(left, EOF_TERMS, n_modes)
        _, corrected_loadings, corrected_scores, corrected_variance = compute_eof(
            right, EOF_TERMS, n_modes
        )
        corrected_loadings, _, corrected_variance, ranks, correlations = align_eofs(
            legacy_loadings, corrected_loadings, corrected_scores, corrected_variance
        )
        for mode in range(n_modes):
            for version, n_rows, variance_value, rank, correlation in (
                ("before", len(left), legacy_variance[mode], mode + 1, 1.0),
                (
                    "after",
                    len(right),
                    corrected_variance[mode],
                    int(ranks[mode]),
                    float(correlations[mode]),
                ),
            ):
                variance_rows.append(
                    {
                        "scope": phase,
                        "eof": mode + 1,
                        "version": version,
                        "n": n_rows,
                        "explained_variance_pct": 100 * variance_value,
                        "matched_rank": rank,
                        "pattern_correlation": correlation,
                    }
                )
            for term_index, term in enumerate(EOF_TERMS):
                loading_rows.extend(
                    [
                        {
                            "scope": phase,
                            "eof": mode + 1,
                            "version": "before",
                            "term": term,
                            "loading": float(legacy_loadings[mode, term_index]),
                        },
                        {
                            "scope": phase,
                            "eof": mode + 1,
                            "version": "after",
                            "term": term,
                            "loading": float(corrected_loadings[mode, term_index]),
                        },
                    ]
                )
    return pd.DataFrame(loading_rows), pd.DataFrame(variance_rows)


def independent_total_eof(
    legacy: pd.DataFrame,
    corrected: pd.DataFrame,
    n_modes: int = 8,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Fit total-lifecycle EOFs using every archived period in each version."""
    left = legacy.groupby("track_id", sort=True)[EOF_TERMS].mean()
    right = corrected.groupby("track_id", sort=True)[EOF_TERMS].mean()
    left_index, legacy_loadings, legacy_scores, legacy_variance = compute_eof(left, EOF_TERMS, n_modes)
    right_index, corrected_loadings, corrected_scores, corrected_variance = compute_eof(
        right, EOF_TERMS, n_modes
    )
    corrected_loadings, corrected_scores, corrected_variance, ranks, correlations = align_eofs(
        legacy_loadings, corrected_loadings, corrected_scores, corrected_variance
    )

    def loading_frame(values: np.ndarray, version: str) -> pd.DataFrame:
        rows = []
        for mode in range(n_modes):
            for term_index, term in enumerate(EOF_TERMS):
                rows.append(
                    {
                        "version": version,
                        "eof": mode + 1,
                        "term": term,
                        "loading": float(values[mode, term_index]),
                    }
                )
        return pd.DataFrame(rows)

    def score_frame(values: np.ndarray, index: pd.Index, version: str) -> pd.DataFrame:
        frame = pd.DataFrame(values, columns=[f"PC{i + 1}" for i in range(n_modes)])
        frame.insert(0, "track_id", index.to_numpy(dtype="int64"))
        frame.insert(1, "version", version)
        return frame

    variance_rows: list[dict] = []
    for mode in range(n_modes):
        variance_rows.extend(
            [
                {
                    "scope": "total", "eof": mode + 1, "version": "before", "n": len(left),
                    "explained_variance_pct": 100 * legacy_variance[mode], "matched_rank": mode + 1,
                    "pattern_correlation": 1.0,
                },
                {
                    "scope": "total", "eof": mode + 1, "version": "after", "n": len(right),
                    "explained_variance_pct": 100 * corrected_variance[mode],
                    "matched_rank": int(ranks[mode]), "pattern_correlation": float(correlations[mode]),
                },
            ]
        )
    return (
        pd.concat([loading_frame(legacy_loadings, "before"), loading_frame(corrected_loadings, "after")], ignore_index=True),
        pd.DataFrame(variance_rows),
        pd.concat(
            [
                score_frame(legacy_scores, left.loc[left_index].index, "before"),
                score_frame(corrected_scores, right.loc[right_index].index, "after"),
            ],
            ignore_index=True,
        ),
    )


def eof_by_phase(cache: pd.DataFrame, n_modes: int = 8):
    loading_rows: list[dict] = []
    variance_rows: list[dict] = []
    score_rows: list[dict] = []
    for phase in PHASES:
        block = cache[cache["phase"] == phase].copy()
        index, loadings, scores, variance = compute_eof(block, EOF_TERMS, n_modes)
        selected = block.loc[index]
        for mode in range(loadings.shape[0]):
            variance_rows.append(
                {
                    "scope": phase,
                    "eof": mode + 1,
                    "n": int(len(selected)),
                    "explained_variance_pct": float(100 * variance[mode]),
                }
            )
            for term, value in zip(EOF_TERMS, loadings[mode]):
                loading_rows.append(
                    {"scope": phase, "eof": mode + 1, "term": term, "loading": float(value)}
                )
        for row_index, (_, row) in enumerate(selected.iterrows()):
            item = {"scope": phase, "track_id": int(row["track_id"])}
            item.update({f"PC{mode + 1}": float(scores[row_index, mode]) for mode in range(scores.shape[1])})
            score_rows.append(item)
    return pd.DataFrame(loading_rows), pd.DataFrame(variance_rows), pd.DataFrame(score_rows)


def total_eof(cache: pd.DataFrame, n_modes: int = 8):
    numeric = cache.groupby("track_id", sort=True)[EOF_TERMS].mean()
    index, loadings, scores, variance = compute_eof(numeric, EOF_TERMS, n_modes)
    track_ids = numeric.loc[index].index.to_numpy(dtype="int64")
    loadings_frame = pd.DataFrame(loadings, columns=EOF_TERMS)
    loadings_frame.insert(0, "eof", np.arange(1, len(loadings_frame) + 1))
    scores_frame = pd.DataFrame(scores, columns=[f"PC{i + 1}" for i in range(scores.shape[1])])
    scores_frame.insert(0, "track_id", track_ids)
    variance_frame = pd.DataFrame(
        {
            "scope": "total",
            "eof": np.arange(1, len(variance) + 1),
            "n": len(track_ids),
            "explained_variance_pct": 100 * variance,
        }
    )
    return loadings_frame, variance_frame, scores_frame


def assign_eof_extremes(scores: pd.DataFrame, n_modes: int = 4) -> pd.DataFrame:
    columns = [f"PC{i}" for i in range(1, n_modes + 1)]
    values = scores[columns]
    q90 = values.quantile(0.90)
    q10 = values.quantile(0.10)
    positive = values.ge(q90).any(axis=1)
    negative = values.le(q10).any(axis=1)
    rows: list[dict] = []
    for sign, mask, reducer in (
        ("positive", positive, "idxmax"),
        ("negative", negative, "idxmin"),
    ):
        selected = scores.loc[mask, ["track_id", *columns]].copy()
        dominant = getattr(selected[columns], reducer)(axis=1).str.replace("PC", "", regex=False)
        selected["sign"] = sign
        selected["dominant_eof"] = dominant.astype(int)
        rows.extend(selected.to_dict("records"))
    return pd.DataFrame(rows)


def assign_published_eof_extremes(
    scores: pd.DataFrame,
    n_modes: int = 8,
    keep_modes: int = 4,
) -> pd.DataFrame:
    """Apply the published Q90/Q10 selection across all eight retained PCs."""
    columns = [f"PC{i}" for i in range(1, n_modes + 1)]
    missing = sorted(set(columns) - set(scores.columns))
    if missing:
        raise ValueError(f"EOF score table misses columns: {missing}")
    values = scores[columns]
    q90 = values.quantile(0.90)
    q10 = values.quantile(0.10)
    rows: list[dict] = []
    for sign, mask, reducer in (
        ("positive", values.ge(q90).any(axis=1), "idxmax"),
        ("negative", values.le(q10).any(axis=1), "idxmin"),
    ):
        selected = scores.loc[mask, ["track_id", *columns]].copy()
        selected["sign"] = sign
        selected["dominant_eof"] = (
            getattr(selected[columns], reducer)(axis=1)
            .str.replace("PC", "", regex=False)
            .astype(int)
        )
        selected = selected[selected["dominant_eof"] <= keep_modes]
        rows.extend(selected.to_dict("records"))
    return pd.DataFrame(rows)


def first_track_rows(tracks: pd.DataFrame) -> pd.DataFrame:
    first = tracks.sort_values(["track_id", "date"]).groupby("track_id", as_index=False).first()
    first["region"] = [classify_region(lon, lat) for lon, lat in zip(first["lon vor"], first["lat vor"])]
    first["season"] = first["date"].dt.month.map(season_of_month)
    return first


def classify_region(lon: float, lat: float) -> str:
    for name, (lon_min, lat_min, lon_max, lat_max) in REGIONS.items():
        if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max:
            return name
    return "OTHER"


def season_of_month(month: int) -> str:
    if month in (12, 1, 2):
        return "DJF"
    if month in (3, 4, 5):
        return "MAM"
    if month in (6, 7, 8):
        return "JJA"
    return "SON"


def track_density(
    tracks: pd.DataFrame,
    lon_bounds: tuple[float, float] = (-80.0, 180.0),
    lat_bounds: tuple[float, float] = (-85.0, -15.0),
    resolution: float = 2.0,
    sigma: float = 1.4,
):
    lon_edges = np.arange(lon_bounds[0], lon_bounds[1] + resolution, resolution)
    lat_edges = np.arange(lat_bounds[0], lat_bounds[1] + resolution, resolution)
    hist, _, _ = np.histogram2d(
        tracks["lat vor"].to_numpy(),
        tracks["lon vor"].to_numpy(),
        bins=(lat_edges, lon_edges),
    )
    smoothed = gaussian_filter(hist, sigma=sigma, mode=("nearest", "wrap"))
    months = max(1, tracks["date"].dt.to_period("M").nunique())
    density = smoothed / months
    lon = (lon_edges[:-1] + lon_edges[1:]) / 2
    lat = (lat_edges[:-1] + lat_edges[1:]) / 2
    return lon, lat, density


def _kmeans_plus_plus(values: np.ndarray, k: int, rng: np.random.Generator) -> np.ndarray:
    centers = [values[rng.integers(0, len(values))]]
    for _ in range(1, k):
        distance = np.min(
            np.sum((values[:, None, :] - np.asarray(centers)[None, :, :]) ** 2, axis=2),
            axis=1,
        )
        total = distance.sum()
        if total <= 0:
            centers.append(values[rng.integers(0, len(values))])
        else:
            centers.append(values[rng.choice(len(values), p=distance / total)])
    return np.asarray(centers, dtype=float)


def deterministic_kmeans(
    values: np.ndarray,
    k: int = 4,
    restarts: int = 30,
    max_iter: int = 300,
    seed: int = 42,
):
    values = np.asarray(values, dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("k-means input contains non-finite values")
    best = None
    for restart in range(restarts):
        rng = np.random.default_rng(seed + restart)
        centers = _kmeans_plus_plus(values, k, rng)
        labels = np.zeros(len(values), dtype=int)
        for _ in range(max_iter):
            distances = np.sum((values[:, None, :] - centers[None, :, :]) ** 2, axis=2)
            new_labels = distances.argmin(axis=1)
            new_centers = centers.copy()
            for cluster in range(k):
                members = values[new_labels == cluster]
                if len(members):
                    new_centers[cluster] = members.mean(axis=0)
                else:
                    new_centers[cluster] = values[rng.integers(0, len(values))]
            if np.array_equal(new_labels, labels) and np.allclose(new_centers, centers):
                labels = new_labels
                centers = new_centers
                break
            labels = new_labels
            centers = new_centers
        inertia = float(np.sum((values - centers[labels]) ** 2))
        if best is None or inertia < best[0]:
            best = (inertia, labels.copy(), centers.copy())
    assert best is not None
    inertia, labels, centers = best
    counts = np.bincount(labels, minlength=k)
    order = np.argsort(-counts)
    inverse = np.empty(k, dtype=int)
    inverse[order] = np.arange(k)
    labels = inverse[labels]
    centers = centers[order]
    return labels, centers, inertia


def intense_clusters(cache: pd.DataFrame, tracks: pd.DataFrame, k: int = 4):
    threshold = float(tracks["vor42"].quantile(0.90))
    intense_ids = set(tracks.loc[tracks["vor42"] > threshold, "track_id"].unique())
    selected = cache[cache["track_id"].isin(intense_ids)].copy()
    pivot = selected.pivot_table(index="track_id", columns="phase", values=CLUSTER_TERMS)
    expected = pd.MultiIndex.from_product([CLUSTER_TERMS, PHASES])
    pivot = pivot.reindex(columns=expected).dropna()
    labels, centers, inertia = deterministic_kmeans(pivot.to_numpy(), k=k)
    assignments = pd.DataFrame(
        {"track_id": pivot.index.astype("int64"), "cluster": labels + 1}
    )
    metadata = {
        "vorticity_quantile": 0.90,
        "vorticity_threshold": threshold,
        "eligible_corrected_cyclones": int(len(pivot)),
        "clusters": int(k),
        "inertia": inertia,
        "feature_order": [f"{term}:{phase}" for term in CLUSTER_TERMS for phase in PHASES],
    }
    return assignments, centers, metadata


def paired_intense_clusters(
    legacy: pd.DataFrame,
    corrected: pd.DataFrame,
    tracks: pd.DataFrame,
    k: int = 4,
):
    """Fit both versions and match corrected groups to legacy centroids."""
    threshold = float(tracks["vor42"].quantile(0.90))
    intense_ids = set(tracks.loc[tracks["vor42"] > threshold, "track_id"].unique())
    expected = pd.MultiIndex.from_product([CLUSTER_TERMS, PHASES])

    def matrix(cache: pd.DataFrame) -> pd.DataFrame:
        selected = cache[cache["track_id"].isin(intense_ids)]
        return selected.pivot_table(index="track_id", columns="phase", values=CLUSTER_TERMS).reindex(
            columns=expected
        ).dropna()

    left = matrix(legacy)
    right = matrix(corrected)
    common = left.index.intersection(right.index)
    left = left.loc[common]
    right = right.loc[common]
    legacy_labels, legacy_centers, legacy_inertia = deterministic_kmeans(left.to_numpy(), k=k)
    corrected_labels, corrected_centers, corrected_inertia = deterministic_kmeans(right.to_numpy(), k=k)
    scale = left.std(axis=0, ddof=1).replace(0, 1).to_numpy()
    cost = np.sqrt(
        np.sum(
            ((legacy_centers[:, None, :] - corrected_centers[None, :, :]) / scale[None, None, :]) ** 2,
            axis=2,
        )
    )
    rows, columns = linear_sum_assignment(cost)
    corrected_order = columns[np.argsort(rows)]
    inverse = np.empty(k, dtype=int)
    inverse[corrected_order] = np.arange(k)
    corrected_labels = inverse[corrected_labels]
    corrected_centers = corrected_centers[corrected_order]
    legacy_assignments = pd.DataFrame(
        {"track_id": common.to_numpy(dtype="int64"), "cluster": legacy_labels + 1, "version": "before"}
    )
    corrected_assignments = pd.DataFrame(
        {"track_id": common.to_numpy(dtype="int64"), "cluster": corrected_labels + 1, "version": "after"}
    )
    metadata = {
        "vorticity_quantile": 0.90,
        "vorticity_threshold": threshold,
        "eligible_paired_cyclones": int(len(common)),
        "clusters": int(k),
        "legacy_inertia": legacy_inertia,
        "corrected_inertia": corrected_inertia,
        "corrected_original_rank_by_matched_cluster": [int(value) + 1 for value in corrected_order],
        "matched_centroid_distance": [float(cost[index, corrected_order[index]]) for index in range(k)],
        "feature_order": [f"{term}:{phase}" for term in CLUSTER_TERMS for phase in PHASES],
    }
    return legacy_assignments, corrected_assignments, legacy_centers, corrected_centers, metadata


def independent_intense_pc_clusters(
    total_scores: pd.DataFrame,
    tracks: pd.DataFrame,
    k: int = 5,
    n_pcs: int = 8,
):
    """Cluster intense systems on the first eight aligned total-lifecycle PCs."""
    threshold = float(tracks["vor42"].quantile(0.90))
    intense_ids = set(tracks.loc[tracks["vor42"] > threshold, "track_id"].astype(int).unique())
    pc_columns = [f"PC{i}" for i in range(1, n_pcs + 1)]

    def matrix(version: str) -> pd.DataFrame:
        selected = total_scores[
            (total_scores["version"] == version)
            & total_scores["track_id"].isin(intense_ids)
        ].set_index("track_id")
        return selected[pc_columns].dropna().sort_index()

    left = matrix("before")
    right = matrix("after")
    legacy_labels, legacy_centers, legacy_inertia = deterministic_kmeans(left.to_numpy(), k=k)
    corrected_labels, corrected_centers, corrected_inertia = deterministic_kmeans(right.to_numpy(), k=k)

    # PC columns have unit sample variance.  Since corrected EOFs were already
    # permuted and sign-aligned, Euclidean centroid distance is meaningful.
    cost = np.sqrt(
        np.sum((legacy_centers[:, None, :] - corrected_centers[None, :, :]) ** 2, axis=2)
    )
    rows, columns = linear_sum_assignment(cost)
    corrected_order = columns[np.argsort(rows)]
    inverse = np.empty(k, dtype=int)
    inverse[corrected_order] = np.arange(k)
    corrected_labels = inverse[corrected_labels]
    corrected_centers = corrected_centers[corrected_order]

    legacy_assignments = pd.DataFrame(
        {"track_id": left.index.to_numpy(dtype="int64"), "cluster": legacy_labels + 1, "version": "before"}
    )
    corrected_assignments = pd.DataFrame(
        {"track_id": right.index.to_numpy(dtype="int64"), "cluster": corrected_labels + 1, "version": "after"}
    )
    metadata = {
        "vorticity_quantile": 0.90,
        "vorticity_threshold": threshold,
        "eligible_legacy_cyclones": int(len(left)),
        "eligible_corrected_cyclones": int(len(right)),
        "clusters": int(k),
        "pcs_used": int(n_pcs),
        "legacy_inertia": legacy_inertia,
        "corrected_inertia": corrected_inertia,
        "corrected_original_rank_by_matched_cluster": [int(value) + 1 for value in corrected_order],
        "matched_centroid_distance": [float(cost[index, corrected_order[index]]) for index in range(k)],
        "feature_order": pc_columns,
        "method": "K-means on the first eight aligned total-lifecycle PC scores",
    }
    return legacy_assignments, corrected_assignments, legacy_centers, corrected_centers, metadata


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
