"""Regression boundaries for the phase-specific article EOF identities."""

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from scripts.article_figures import common
from scripts.article_figures.phase_eofs import (
    PRODUCT_DIRECTORY, compatibility_tables, load_pinned_phase_inputs,
    matched_phase_eofs, read_phase_product, validate_phase_product,
)

ROOT = Path(__file__).resolve().parents[1]
REPRODUCTION = ROOT / "results/corrected/article"
EXPECTED_RANKS = {
    "incipient": [1, 3, 2, 4], "intensification": [1, 2, 4, 3],
    "mature": [1, 2, 3, 4], "decay": [1, 2, 3, 4],
}


@pytest.fixture(scope="module")
def product():
    return read_phase_product(ROOT)


@pytest.mark.parametrize("phase", common.PHASES)
def test_phase_mapping_from_raw_patterns_and_joint_permutation(phase, product):
    """Recompute matching from the pinned raw patterns, not stored rank metadata."""
    reference = pd.read_csv(ROOT / "results/original/article/eof_loadings_by_phase.csv")
    raw = pd.read_csv(REPRODUCTION / "eof_loadings_by_phase_raw.csv")
    raw_variance = pd.read_csv(REPRODUCTION / "eof_variance_by_phase_raw.csv")
    before = reference[reference.scope.eq(phase)].pivot(index="eof", columns="term", values="loading").loc[range(1, 9), common.EOF_TERMS].to_numpy()
    after = raw[raw.scope.eq(phase)].pivot(index="raw_rank", columns="term", values="loading").loc[range(1, 9), common.EOF_TERMS].to_numpy()
    variance = raw_variance[raw_variance.scope.eq(phase)].set_index("raw_rank").loc[range(1, 9), "explained_variance_pct"].to_numpy() / 100
    scores = np.arange(40, dtype=float).reshape(5, 8)  # distinct columns detect wrong score ordering
    result = common.align_eofs(before, after, scores, variance)
    loadings, pcs, ev, ranks, correlations = result
    assert ranks[:4].tolist() == EXPECTED_RANKS[phase]
    assert sorted(ranks) == list(range(1, 9))
    signs = np.sign(np.sum(loadings * after[ranks - 1], axis=1))
    np.testing.assert_array_equal(loadings, after[ranks - 1] * signs[:, None])
    np.testing.assert_array_equal(pcs, scores[:, ranks - 1] * signs[None, :])
    np.testing.assert_array_equal(ev, variance[ranks - 1])
    assert (correlations >= 0).all()
    for mode in range(8):
        flips = np.ones(8)
        flips[mode] = -1
        flipped = common.align_eofs(before, after * flips[:, None], scores * flips[None, :], variance)
        for actual, expected in zip(flipped, result):
            np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=0)
    stored = product[1].query("scope == @phase and version == 'after'").sort_values("reference_eof")
    np.testing.assert_array_equal(stored.raw_rank, ranks)
    np.testing.assert_array_equal(stored.sign_alignment, signs)
    np.testing.assert_allclose(stored.explained_variance_pct, ev * 100, atol=5e-7, rtol=0)
    if phase == "incipient":
        # 8-significant-digit CSVs retain <5e-7 percentage-point error.
        assert ev[1] * 100 == pytest.approx(10.548160122, abs=5e-7)
        assert ev[2] * 100 == pytest.approx(14.023895264, abs=5e-7)


def test_explicit_identity_and_corrected_only_comparison_equality(product):
    loadings, variance = product
    for name, table in (("loadings", loadings), ("variance", variance)):
        assert "eof" not in table and {"reference_eof", "raw_rank", "sign_alignment"} <= set(table)
        after = pd.read_csv(REPRODUCTION / f"eof_{name}_by_phase.csv")
        pd.testing.assert_frame_equal(after, table[table.version.eq("after")].reset_index(drop=True), check_exact=True)
    for table, name in zip(compatibility_tables(*product), ("loadings", "variance")):
        comparison = pd.read_csv(ROOT / f"results/comparison/article/eof_{name}_by_phase.csv")
        pd.testing.assert_frame_equal(table, comparison, check_exact=True)
    with pytest.raises(ValueError, match="explicit reference"):
        validate_phase_product(*compatibility_tables(*product))
    invalid = variance.copy()
    invalid.loc[invalid.version.eq("after") & invalid.reference_eof.eq(2), "raw_rank"] = 1
    with pytest.raises(ValueError, match="one-to-one"):
        validate_phase_product(loadings, invalid)
    invalid_loadings = loadings.copy()
    invalid_loadings.loc[0, "sign_alignment"] = -1
    with pytest.raises(ValueError, match="metadata disagree"):
        validate_phase_product(invalid_loadings, variance)


def test_real_inputs_are_independent_decompositions_and_scores_are_matched(monkeypatch, product):
    """Integration: current hash-pinned caches; absence is explicit for other hosts."""
    provenance = json.loads((ROOT / "results/comparison/article/provenance.json").read_text())
    if not all(Path(provenance[key]).is_file() for key in ("legacy_cache", "corrected_cache")):
        pytest.skip("external hash-pinned phase caches are not installed on this host")
    legacy, corrected, _ = load_pinned_phase_inputs(ROOT)
    compute = common.compute_eof
    calls = []

    def trace(frame, terms, n_modes):
        result = compute(frame, terms, n_modes)
        calls.append((frame.copy(), result))
        return result

    monkeypatch.setattr(common, "compute_eof", trace)
    loadings, variance, scores = matched_phase_eofs(legacy, corrected)
    assert len(calls) == 8
    assert [len(frame) for frame, _ in calls] == [4587, 3820, 6642, 3820, 4747, 3820, 6488, 3820]
    for index, phase in enumerate(common.PHASES):
        for frame, result in calls[index * 2:index * 2 + 2]:
            assert set(frame.phase) == {phase}
            assert frame.period.eq(phase).all()
            assert len(result[0]) == len(frame)  # no missing complete cases
        before_result = calls[index * 2][1]
        raw = calls[index * 2 + 1][1]
        expected = common.align_eofs(before_result[1], raw[1], raw[2], raw[3])
        actual = scores[scores.scope.eq(phase)].set_index("track_id")[[f"reference_PC{i}" for i in range(1, 9)]]
        assert actual.index.equals(raw[0])
        np.testing.assert_allclose(actual.to_numpy(), expected[1], atol=1e-12, rtol=0)
    for actual, saved in zip((loadings, variance), product):
        # Loading CSV precision <=5e-8; EV precision <=5e-7 percentage points.
        pd.testing.assert_frame_equal(actual, saved, check_dtype=False, atol=5e-7, rtol=0)
    saved_scores = pd.read_csv(REPRODUCTION / "eof_scores_by_phase.csv")
    assert all(column.startswith("reference_PC") for column in saved_scores.columns[2:])
    # Eight significant digits: relative rounding <=5e-8 (small near-zero floor).
    pd.testing.assert_frame_equal(scores, saved_scores, check_dtype=False, atol=5e-9, rtol=5e-8)


def test_both_renderers_receive_identical_sixteen_panels(monkeypatch, tmp_path, product):
    """Intercept the actual plotting boundaries so wrong selection cannot hide in CSV tests."""
    from scripts.article_figures import generate_comparison as comparison
    from scripts.article_figures import generate_corrected_article as corrected

    loadings, variance = product
    rendered = {}
    standalone = {}
    current_mode = [None]

    def capture_comparison(ax, before, after, **kwargs):
        phase = kwargs["title"].splitlines()[1]
        rendered[phase, current_mode[0]] = after

    def capture_corrected(table, variances, zero_based, directory):
        for phase in common.PHASES:
            standalone[phase, zero_based + 1] = (table.loc[phase], variances.loc[phase, zero_based])

    monkeypatch.setattr(comparison, "draw_cycle_comparison", capture_comparison)
    monkeypatch.setattr(comparison, "save_pair", lambda figure, stem: comparison.plt.close(figure))
    monkeypatch.setattr(corrected, "load_definitions", lambda path: SimpleNamespace(plot_lorenzcycletoolkit_eof=capture_corrected))
    monkeypatch.setattr(corrected, "patch_eof_box_renderer", lambda module: None)
    monkeypatch.setattr(corrected, "assemble_panel", lambda *args, **kwargs: None)
    for mode in range(1, 5):
        current_mode[0] = mode
        comparison.fig_eof(mode, loadings, variance, tmp_path / str(mode))
    corrected.render_eof_diagrams(tmp_path, loadings[loadings.version.eq("after")], variance[variance.version.eq("after")], tmp_path, tmp_path)
    assert len(rendered) == len(standalone) == 16
    for (phase, mode), series in rendered.items():
        other, ev = standalone[phase, mode]
        np.testing.assert_array_equal(series.reindex(common.EOF_TERMS), other.reindex(common.EOF_TERMS))
        expected = variance.query("scope == @phase and reference_eof == @mode and version == 'after'").explained_variance_pct.item()
        assert ev == expected


def test_phase_output_hashes():
    directory = ROOT / PRODUCT_DIRECTORY
    provenance = json.loads((directory / "provenance.json").read_text())
    assert any("fig_08" in path for path in provenance["outputs"])
    for path, digest in provenance["outputs"].items():
        assert common.sha256_file(ROOT / path) == digest, path
