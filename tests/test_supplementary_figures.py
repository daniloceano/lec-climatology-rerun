"""Scientific and provenance regressions for the four supplementary figures."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from PIL import Image

from scripts.article_figures.common import sha256_file

ROOT = Path(__file__).resolve().parents[1]


def table(family, name):
    return pd.read_csv(ROOT / f'results/{family}/supplementary/{name}')


def test_published_s1_counts_and_corrected_memberships():
    expected = [1305, 1334, 433, 600, 375, 642, 337, 383]
    original = table('original', 's1_eof_cyclone_metrics.csv')
    actual = [len(original.query('dominant_eof == @mode and sign == @sign'))
              for mode in range(1, 5) for sign in ('positive', 'negative')]
    assert actual == expected
    for family in ('original', 'corrected'):
        s1 = table(family, 's1_eof_cyclone_metrics.csv')
        article = pd.read_csv(ROOT / f'results/{family}/article/eof_extreme_assignments.csv')
        pd.testing.assert_frame_equal(s1[['track_id', 'sign', 'dominant_eof']],
                                      article[['track_id', 'sign', 'dominant_eof']])
        assert s1[['duration', 'max_intensity', 'mean_speed']].notna().all().all()


def test_s2_uses_four_validated_clusters_and_integer_day_duration():
    for family, size in (('original', 679), ('corrected', 603)):
        s2 = table(family, 's2_cluster_duration.csv')
        article = pd.read_csv(ROOT / f'results/{family}/article/cluster_assignments.csv')
        assert len(s2) == size
        assert set(s2.cluster) == {1, 2, 3, 4}
        pd.testing.assert_frame_equal(s2[['track_id', 'cluster']].sort_values('track_id').reset_index(drop=True),
                                      article[['track_id', 'cluster']].sort_values('track_id').reset_index(drop=True))
        assert (s2.duration >= 0).all() and (s2.duration % 1 == 0).all()


def test_s3_uses_matched_pc_columns_and_source_quantile():
    provenance = json.loads((ROOT / 'results/comparison/supplementary/provenance.json').read_text())
    assert provenance['s3_original_script_quantile'] == .95
    assert provenance['s3_selected'] == {'original': 242, 'corrected': 210}
    for family in ('original', 'corrected'):
        s3 = table(family, 's3_intense_pc_scores.csv')
        assert s3.track_id.is_monotonic_increasing
        scores = pd.read_csv(ROOT / f'results/{family}/article/eof_scores_total.csv')
        columns = ['track_id', 'PC1', 'PC2', 'PC3', 'PC4']
        expected = scores[columns].set_index('track_id').loc[s3.track_id].reset_index()
        np.testing.assert_allclose(s3[columns[1:]], expected[columns[1:]], rtol=1e-12)


def test_s4_uses_same_strict_four_phase_population_and_corrected_values():
    before = table('original', 's4_decay_ck_pairs.csv')
    after = table('corrected', 's4_decay_ck_pairs.csv')
    assert len(before) == len(after) == 3637
    assert set(before.track_id) == set(after.track_id)
    assert after.decay_points.ge(1).all()
    assert before[['Ck_initial', 'Ck_final']].median().to_numpy() == pytest.approx([-2.5439018894, -1.0346726758], abs=1e-8)
    assert after[['Ck_initial', 'Ck_final']].median().to_numpy() == pytest.approx([-0.6617816891, -0.1592279928], abs=1e-8)


def test_supplementary_figures_and_tables_are_hashed():
    manifest = table('comparison', 'figure_manifest.csv')
    assert manifest.figure.tolist() == ['S1', 'S2', 'S3', 'S4']
    for row in manifest.itertuples():
        for path, digest in ((row.original_png, row.original_sha256),
                             (row.corrected_png, row.corrected_sha256),
                             (row.comparison_png, row.comparison_sha256),
                             (row.comparison_pdf, row.comparison_pdf_sha256)):
            assert sha256_file(ROOT / path) == digest
        with Image.open(ROOT / row.original_png) as original, Image.open(ROOT / row.corrected_png) as corrected:
            assert original.size == corrected.size
    for family in ('original', 'corrected', 'comparison'):
        provenance = json.loads((ROOT / f'results/{family}/supplementary/provenance.json').read_text())
        for path, digest in provenance['outputs'].items():
            assert sha256_file(ROOT / path) == digest, path
