# Phase EOF identity matching for Figures 5–8

The legacy and corrected EOFs are independently fitted to each lifecycle phase. Each fit uses the 24 published LEC terms and only rows with `period` equal to that phase. The archived matrices contain 4,587 / 6,642 / 4,747 / 6,488 rows for incipient / intensification / mature / decay; the corrected matrices each contain 3,820 rows.

The corrected patterns are matched one-to-one to published EOF identities and their signs are aligned. Scores, loadings and explained variance move together under the permutation; a sign flip changes scores and loadings but not variance. The incipient published EOF 2 corresponds to corrected raw rank 3 (10.548160122% explained variance), while published EOF 3 corresponds to raw rank 2 (14.023895264%).

The canonical matched tables are `results/comparison/article/phase_eof_matched/loadings.csv` and `variance.csv`. `reference_eof`, `raw_rank` and `sign_alignment` make the identity explicit. Corrected phase scores and raw-rank audit tables are directly in `results/corrected/article/`; `results/comparison/article/phase_eof_matched/provenance.json` records input and output hashes. Figures 5–8 and the corrected Figure 16 consume the same matched phase identities.

Verify the stored products and renderer inputs with `python -m pytest -q tests/test_phase_eof_matching.py tests/test_downstream_reproduction.py`.
