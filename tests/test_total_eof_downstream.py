"""Canonical four-cluster total-EOF result and comparison regressions."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.article_figures import common as c

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results'
PCS = [f'PC{i}' for i in range(1, 9)]


def product(version, name):
    return pd.read_csv(RESULTS / version / 'article' / name, float_precision='round_trip')


def test_only_three_result_and_figure_families_exist():
    for base in (ROOT / 'results', ROOT / 'figures'):
        assert {p.name for p in base.iterdir() if p.is_dir()} == {'original', 'corrected', 'comparison'}
    for base in (ROOT / 'results', ROOT / 'figures'):
        assert not list(base.rglob('validated_downstream'))
        assert not list(base.rglob('intense_pc_cluster*'))


def test_total_eof_mapping_matches_corrected_scores_and_variance():
    mapping = product('corrected', 'total_eof_mapping.csv')
    variance = product('corrected', 'eof_variance_total.csv')
    scores = product('corrected', 'eof_scores_total.csv')
    assert len(scores) == 3820
    assert sorted(mapping.corrected_raw_rank) == list(range(1, 9))
    assert set(mapping.sign_alignment) <= {-1, 1}
    np.testing.assert_allclose(scores[PCS].std(), mapping.eigenvalue, rtol=1e-12)
    np.testing.assert_allclose(variance.explained_variance_pct, mapping.explained_variance * 100, rtol=1e-12)


def test_comparison_tables_are_exact_versioned_source_products():
    for name in ('eof_scores_total.csv', 'eof_extreme_assignments.csv',
                 'cluster_assignments.csv', 'cluster_centers.csv', 'figure14_statistics.csv'):
        combined = product('comparison', name)
        for version, label in (('original', 'before'), ('corrected', 'after')):
            source = product(version, name)
            view = combined.query('version == @label').drop(columns='version').reset_index(drop=True)
            for column in source.columns:
                pd.testing.assert_series_equal(view[column], source[column], check_names=False, check_dtype=False)
            assert len(view) == len(source)


def test_extreme_memberships_follow_the_versioned_scores():
    for version in ('original', 'corrected'):
        scores = product(version, 'eof_scores_total.csv')
        actual = c.assign_published_eof_extremes(scores)
        saved = product(version, 'eof_extreme_assignments.csv')
        keys = ['track_id', 'sign', 'dominant_eof']
        pd.testing.assert_frame_equal(actual[keys].sort_values(keys).reset_index(drop=True),
                                      saved[keys].sort_values(keys).reset_index(drop=True))


def test_both_populations_have_four_clusters_and_consistent_statistics():
    for version, count in (('original', 679), ('corrected', 603)):
        assignments = product(version, 'cluster_assignments.csv')
        centers = product(version, 'cluster_centers.csv')
        statistics = product(version, 'figure14_statistics.csv')
        assert len(assignments) == count
        assert set(assignments.cluster) == set(centers.cluster) == set(statistics.cluster) == {1, 2, 3, 4}
        assert statistics.set_index('cluster').n.to_dict() == assignments.groupby('cluster').size().to_dict()


def test_provenance_hashes_cover_canonical_comparison_products():
    provenance = json.loads((RESULTS / 'comparison/article/provenance.json').read_text())
    assert provenance['clusters'] == 4
    assert provenance['figure_files'] == 16
    for name, digest in provenance['numeric_outputs'].items():
        assert c.sha256_file(ROOT / name) == digest, name


def test_superseded_five_cluster_fit_is_disabled():
    with pytest.raises(ValueError, match='BLOCKED superseded five-cluster'):
        c.independent_intense_pc_clusters(None, None)


def test_total_eof_function_propagates_joint_alignment_on_independent_populations():
    rng=np.random.default_rng(321)
    legacy=pd.DataFrame(rng.normal(size=(80,24)),columns=c.EOF_TERMS).assign(track_id=np.arange(80))
    corrected=pd.DataFrame(rng.normal(size=(57,24)),columns=c.EOF_TERMS).assign(track_id=np.arange(57))
    b=c.compute_eof(legacy.set_index('track_id'),c.EOF_TERMS)
    a=c.compute_eof(corrected.set_index('track_id'),c.EOF_TERMS)
    expected=c.align_eofs(b[1],a[1],a[2],a[3])
    loadings,variance,scores=c.independent_total_eof(legacy,corrected)
    assert scores.groupby('version').size().to_dict()=={'after':57,'before':80}
    actual=loadings.query('version == "after"').pivot(index='eof',columns='term',values='loading')[c.EOF_TERMS]
    np.testing.assert_allclose(actual,expected[0])
    np.testing.assert_allclose(scores.query('version == "after"')[PCS],expected[1])
    np.testing.assert_allclose(variance.query('version == "after"').explained_variance_pct,100*expected[2])
