# Original article workflow inventory

Audit source: `/Users/danilocoutodesouza/Documents/danilo_thesis_iag/manuscript_lec_climatology`.
The authoritative figure references are the `\includegraphics` entries in
`submission_files-clim_dyn_rev2/LEC_climatology_clim_dyn_vCBG-2/sn-article_rev2.tex`.
The published PNGs were copied verbatim; they were not regenerated.

| Published figure | Legacy script(s) | Apparent purpose | Principal input | Legacy output | Reuse assessment |
|---|---|---|---|---|---|
| 1 | `map_density.py` | Combined track-density map and genesis boxes | Three regional track-density NetCDF files | `combined_density_map_all_phases_regions_with_regions.png` | Artifact reused. Script requires external NetCDFs and should not be rerun without those exact files. |
| 2 | `lec_chains.py`, `pdfs.py` | Conceptual/mean LEC chain | Legacy per-cyclone phase CSVs | `LEC_chains.png` | Artifact reused unchanged; script logic is usable with explicit input-path adaptation. |
| 3 | `pdfs.py` | PDFs/ridgelines of LEC terms | Legacy per-cyclone phase CSVs | `combined_ridge.png` | Artifact reused; corrected input requires a small path/schema adapter. |
| 4 | `plot_LEC_std.py`, `plot_LEC_panel_mean_phases.py` | Phase-mean LEC with spread | Legacy per-cyclone phase CSVs | `panel_LEC_mean_phases.png` | Artifact reused; plotting logic is reusable, but current validated generator already implements the same role with explicit inputs. |
| 5–8 | `plot_LEC_eofs.py`, `plot_LEC_panel_eofs.py` | Phase EOF LEC panels | Legacy phase CSVs and phase EOF tables | `panel_LEC_EOF1.png` … `panel_LEC_EOF4.png` | Artifacts reused. The legacy scripts hard-code paths; use only after a small compatibility wrapper. |
| 9–10 | `map_density_eof.py` | Positive/negative PC-extreme density | EOF assignments and track-density fields | `density_panel_q90.png`, `density_panel_q10.png` | Artifacts reused. Corrected rendering is covered by the validated article comparison workflow. |
| 11 | `eof_cyclone_statistics_q10_q90.py` | Genesis/season statistics for PC extremes | PC-extreme assignments and tracks | `panel_2x2_q90_vs_q10.png` | Artifact reused; script needs explicit paths to be portable. |
| 12 | `eofs_kmeans_pcs.py`, `eof_plot_lec_centroids.py`, `plot_LEC_panel_clusters.py` | Intense-cyclone clustering and LEC panels | EOF scores, legacy LEC CSVs and tracks | `panel_LEC_clusters.png` | Validated current reproduction uses the archived four-cluster publication layout. |
| 13 | `map_density_intense.py` | Density of intense-cyclone groups | Cluster density NetCDFs | `density_panel.png` | Artifact reused; source depends on exact external NetCDF products. |
| 14 | `eof_cluster_statistics.py` | Cluster count/intensity/season/genesis summary | Cluster assignments and track table | `cluster_analysis_panel.png` | Artifact reused; small path compatibility changes would be required. |
| 15 | `tests_draw_lec/draw_lec_v6.py` | Lifecycle LEC synthesis | Legacy per-cyclone phase CSVs | `LEC_total_v6.png` | Artifact reused; drawing primitives informed the maintained workflow. |
| 16 | `tests_draw_lec/draw_lec_eofs.py`, `tests_draw_lec/draw_lec_v6.py` | EOF synthesis panel | Phase EOF tables and a legacy result schema | `EOFs_panel.png` | The validated corrected Figure 16 reproduces this phase/EOF-loading definition with frozen matched inputs. |

No legacy scripts were copied into this repository. The maintained
`scripts/article_figures/` implementation already provides explicit inputs,
population assertions, deterministic EOF/cluster matching and provenance.
Copying the hard-coded legacy scripts would add a second executable workflow
without making the corrected analysis more reproducible.
