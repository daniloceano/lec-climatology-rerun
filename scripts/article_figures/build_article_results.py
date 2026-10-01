"""Build the three canonical article result views from the audited workflows."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.article_figures.common import EOF_TERMS, sha256_file

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT / 'results/original/article'
GATE = ORIGINAL / 'reproduction_gate'
CORRECTED = ROOT / 'results/corrected/article'
COMPARISON = ROOT / 'results/comparison/article'


def versioned(before: str, after: str, output: str) -> None:
    left = pd.read_csv(GATE / before).assign(version='before')
    right = pd.read_csv(CORRECTED / after).assign(version='after')
    pd.concat([left, right], ignore_index=True).to_csv(COMPARISON / output, index=False, float_format='%.17g')


def main() -> int:
    gate = json.loads((GATE / 'manifest.json').read_text())
    corrected = json.loads((CORRECTED / 'provenance.json').read_text())
    if not gate['checks'] or not all(item['passed'] for item in gate['checks']):
        raise ValueError('legacy reproduction gate has not passed')
    if corrected['status'] != 'VALIDATED_CORRECTED_CANDIDATES':
        raise ValueError('corrected scientific products are not validated')
    for name in ('eof_scores_total.csv', 'eof_extreme_assignments.csv'):
        shutil.copyfile(GATE / name, ORIGINAL / name)
    for source, target in (('cluster_assignments.csv', 'cluster_assignments.csv'),
                           ('cluster_centers.csv', 'cluster_centers.csv'),
                           ('figure14_statistics.csv', 'figure14_statistics.csv')):
        shutil.copyfile(GATE / source, ORIGINAL / target)

    versioned('eof_scores_total.csv', 'eof_scores_total.csv', 'eof_scores_total.csv')
    versioned('eof_extreme_assignments.csv', 'eof_extreme_assignments.csv', 'eof_extreme_assignments.csv')
    versioned('cluster_assignments.csv', 'cluster_assignments.csv', 'cluster_assignments.csv')
    versioned('cluster_centers.csv', 'cluster_centers.csv', 'cluster_centers.csv')
    versioned('figure14_statistics.csv', 'figure14_statistics.csv', 'figure14_statistics.csv')

    published = pd.read_csv(ORIGINAL / 'eof_loadings_total.csv')
    published = published.query('version == "before"').rename(columns={'eof': 'reference_eof'})
    published = published[['reference_eof', 'term', 'loading']].assign(version='before')
    current = pd.read_csv(CORRECTED / 'eof_loadings_total.csv')
    if current.shape != (8, len(EOF_TERMS) + 1) or set(current.reference_eof) != set(range(1, 9)):
        raise ValueError('corrected total EOF loading matrix has unexpected shape')
    current = current.melt(id_vars='reference_eof', var_name='term', value_name='loading').assign(version='after')
    if len(published) != len(current) or set(published.term) != set(EOF_TERMS):
        raise ValueError('published and corrected EOF terms differ')
    pd.concat([published, current], ignore_index=True).to_csv(COMPARISON / 'eof_loadings_total.csv', index=False, float_format='%.17g')

    reference = pd.read_csv(ORIGINAL / 'eof_variance_total.csv').query('version == "before"')
    reference = reference.rename(columns={'eof': 'reference_eof'})
    reference = reference[['reference_eof', 'explained_variance_pct']].assign(
        version='before', raw_rank=lambda frame: frame.reference_eof,
        sign_alignment=1, pattern_correlation=1.0, n=6789)
    mapping = pd.read_csv(CORRECTED / 'total_eof_mapping.csv')
    if sorted(mapping.reference_eof) != list(range(1, 9)):
        raise ValueError('corrected total EOF mapping is incomplete')
    after = pd.DataFrame(dict(reference_eof=mapping.reference_eof, version='after',
                              raw_rank=mapping.corrected_raw_rank,
                              sign_alignment=mapping.sign_alignment,
                              pattern_correlation=mapping.pattern_correlation,
                              explained_variance_pct=100 * mapping.explained_variance, n=3820))
    columns = ['version', 'reference_eof', 'raw_rank', 'sign_alignment',
               'pattern_correlation', 'explained_variance_pct', 'n']
    pd.concat([reference, after], ignore_index=True)[columns].to_csv(
        COMPARISON / 'eof_variance_total.csv', index=False, float_format='%.17g')
    if not np.allclose(reference.sort_values('reference_eof').explained_variance_pct,
                       mapping.sort_values('reference_eof').ev_legacy * 100, atol=1e-5):
        raise ValueError('published total EOF variance differs from the validated mapping')

    original_outputs = {str(path.relative_to(ROOT)): sha256_file(path)
                        for path in ORIGINAL.glob('*') if path.is_file() and path.name != 'provenance.json'}
    (ORIGINAL / 'provenance.json').write_text(json.dumps(dict(
        status='PUBLISHED_REFERENCE_AND_REPRODUCED_LEGACY',
        reproduction_gate=str((GATE / 'manifest.json').relative_to(ROOT)),
        reproduction_gate_sha256=sha256_file(GATE / 'manifest.json'),
        outputs=original_outputs), indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
