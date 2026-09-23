from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.article_figures.common import (
    REGIONS,
    classify_region,
    compute_eof,
    deterministic_kmeans,
    season_of_month,
)


def test_genesis_region_boundaries_match_published_boxes():
    assert REGIONS["SE-BR"] == (-52.0, -38.0, -37.0, -23.0)
    assert REGIONS["LA-PLATA"] == (-69.0, -38.0, -52.0, -23.0)
    assert REGIONS["ARG"] == (-70.0, -55.0, -50.0, -39.0)
    assert classify_region(-45.0, -30.0) == "SE-BR"
    assert classify_region(-60.0, -30.0) == "LA-PLATA"
    assert classify_region(-60.0, -45.0) == "ARG"
    assert classify_region(-40.0, -50.0) == "OTHER"


def test_season_mapping_is_southern_hemisphere_quarterly_labeling():
    assert [season_of_month(month) for month in range(1, 13)] == [
        "DJF", "DJF", "MAM", "MAM", "MAM", "JJA",
        "JJA", "JJA", "SON", "SON", "SON", "DJF",
    ]


def test_kmeans_is_deterministic_and_labels_largest_cluster_first():
    rng = np.random.default_rng(7)
    values = np.vstack(
        [
            rng.normal(0.0, 0.05, size=(30, 2)),
            rng.normal(3.0, 0.05, size=(20, 2)),
            rng.normal(-3.0, 0.05, size=(10, 2)),
        ]
    )
    labels_a, centers_a, inertia_a = deterministic_kmeans(values, k=3, seed=42)
    labels_b, centers_b, inertia_b = deterministic_kmeans(values, k=3, seed=42)
    np.testing.assert_array_equal(labels_a, labels_b)
    np.testing.assert_allclose(centers_a, centers_b)
    assert inertia_a == inertia_b
    assert np.bincount(labels_a).tolist() == [30, 20, 10]


def test_correlation_eof_shapes_variance_and_unit_pc_variance():
    rng = np.random.default_rng(3)
    frame = pd.DataFrame(rng.normal(size=(120, 5)), columns=list("abcde"))
    index, loadings, scores, variance = compute_eof(frame, list("abcde"), n_modes=3)
    assert index.equals(frame.index)
    assert loadings.shape == (3, 5)
    assert scores.shape == (120, 3)
    assert variance.shape == (3,)
    assert np.all(np.diff(variance) <= 0)
    assert np.all((variance > 0) & (variance < 1))
    np.testing.assert_allclose(scores.var(axis=0, ddof=1), np.ones(3), atol=1e-10)
