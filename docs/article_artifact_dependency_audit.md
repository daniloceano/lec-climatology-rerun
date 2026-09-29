# Article artifact dependency audit

The action refers to corrected or comparison production. ORIGINAL artifacts
are the verbatim final-submission PNGs under `figures/original/article/`.

| Figure/result | Original source | Input variables | Affected by toolkit correction? | Action | Corrected script | Corrected/comparison output | Notes |
|---|---|---|---|---|---|---|---|
| 1 track density | `combined_density_map_all_phases_regions_with_regions.png` | Track positions and genesis regions | No LEC dependency | REUSE_UNCHANGED | `generate_article_comparison.py` | `figures/corrected/article/fig_01_track_density.png`; `figures/comparison/article/fig_01_track_density.*` | Reference map, not a population-change diagnostic. |
| 2 LEC reference | `LEC_chains.png` | Conceptual LEC topology | No dataset dependency | REUSE_UNCHANGED | `generate_article_comparison.py` | `figures/corrected/article/fig_02_lec_reference.png`; `figures/comparison/article/fig_02_lec_reference.*` | Published artwork is retained as the side-specific reference. |
| 3 term distributions | `combined_ridge.png` | All LEC terms by phase | Yes | REGENERATE | `generate_article_comparison.py` | `figures/comparison/article/fig_03_term_pdfs_published_corrected.*` | Corrected numerical rows also live under `results/corrected/article/`. |
| 4 phase-mean LEC | `panel_LEC_mean_phases.png` | Phase means and standard deviations | Yes | REGENERATE | `generate_article_comparison.py` | `figures/comparison/article/fig_04_phase_mean_lec_published_corrected.*` | Uses corrected `Ca`, `Ck`, pressure work and residuals. |
| 5–8 phase EOFs | `panel_LEC_EOF1.png` … `panel_LEC_EOF4.png` | Phase LEC EOF loadings and variance | Yes | REGENERATE | `generate_article_comparison.py` | `figures/comparison/article/fig_05_*` … `fig_08_*` | EOFs independently fitted, matched and sign-aligned. |
| 9–10 PC-extreme density | `density_panel_q90.png`, `density_panel_q10.png` | Total-lifecycle EOF scores and tracks | Indirectly | REGENERATE | `generate_article_comparison.py` | `figures/comparison/article/fig_09_*`, `fig_10_*` | Track fields are unchanged; membership depends on corrected EOF scores. |
| 11 PC-extreme composition | `panel_2x2_q90_vs_q10.png` | EOF-extreme assignments, genesis and season | Indirectly | REGENERATE | `generate_article_comparison.py` | `figures/comparison/article/fig_11_*` | Metadata are unchanged; selected systems can change. |
| 12 intense LEC/groups | `panel_LEC_clusters.png` | Intensity filter, PCs, clusters and LEC means | Yes | REGENERATE | `generate_article_comparison.py` | `figures/comparison/article/fig_12a_*`, `fig_12b_*` | Current workflow uses five PC-space groups; the obsolete four-group corrected set is not reused. |
| 13 group density | `density_panel.png` | Cluster assignments and tracks | Indirectly | REGENERATE | `generate_article_comparison.py` | `figures/comparison/article/fig_13_*` | Membership depends on corrected PCs/clusters. |
| 14 group characteristics | `cluster_analysis_panel.png` | Cluster assignments, intensity, season and genesis | Indirectly | REGENERATE | `generate_article_comparison.py` | `figures/comparison/article/fig_14_*` | Metadata remain unchanged but group membership changes. |
| 15 phase synthesis | `LEC_total_v6.png` | Phase LEC means | Yes | REGENERATE | `generate_article_comparison.py` | `figures/comparison/article/fig_15_*` | Direct corrected-LEC dependency. |
| 16 EOF-group LEC | `EOFs_panel.png` | Positive EOF-group assignments and mean LEC | Yes | REGENERATE | `generate_article_comparison.py` | `figures/comparison/article/fig_16a_*` … `fig_16d_*` | Current validated definition differs from the legacy EOF-loading synthesis. |

Standalone corrected Figures 3–16 were deliberately not regenerated. The
validated comparison figures already expose the complete corrected side, and
the exact corrected numerical views are materialized without recomputation in
`results/corrected/article/`. Creating a second visual suite would duplicate
compute and introduce another plotting product without adding scientific
information.
