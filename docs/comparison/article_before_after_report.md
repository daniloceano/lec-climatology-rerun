# LEC climatology: published article versus corrected rerun

This report separates the literal article comparison from the controlled paired sensitivity analysis. The before side uses the complete archived population and published analysis definition; the after side applies the same definitions to the validated corrected rerun.

## Interpretation boundary

- Before: **6,789 legacy cyclones and 25,000 archived lifecycle rows**.
- After: **3,820 corrected cyclones and 15,829 archived lifecycle rows**.
- Differences therefore combine the toolkit correction and the population change. They must not be interpreted as a purely paired correction effect.
- The existing paired 3,820-cyclone report remains the controlled sensitivity analysis and is not overwritten.

## Reproduction audit

- Published total EOF 1-4 variance reproduced from the legacy cache: **28.304%, 11.018%, 10.925%, 8.188%**.
- Primary legacy rows: **22,464**; primary corrected rows: **15,280**.
- The validated intense-system selection contains **679 legacy** and **603 corrected** cyclones under the common track-level threshold.
- Four K-means groups are fitted to the first eight total-lifecycle PC scores; corrected groups are centroid-matched to legacy groups.
- Figure 16 reproduces the article's phase/EOF-loading synthesis using the frozen matched phase EOF inputs from Figures 5–8.

## Figures

### Figure 1

![Figure 1](../../figures/comparison/article/fig_01_track_density.png)

*Track density and the three genesis regions; this track-only reference is common to both datasets.*

### Figure 2

![Figure 2](../../figures/comparison/article/fig_02_lec_reference.png)

*Reference four-box Lorenz Energy Cycle diagram; this conceptual panel is common to both datasets.*

### Figure 3

![Figure 3](../../figures/comparison/article/fig_03_term_pdfs_published_corrected.png)

*LEC term distributions from the full published legacy archive (upper half) and corrected rerun (lower half).*

### Figure 4

![Figure 4](../../figures/comparison/article/fig_04_phase_mean_lec_published_corrected.png)

*Primary-phase mean LEC. Dark arrows and values show the published legacy population; red shows the corrected population.*

### Figure 5

![Figure 5](../../figures/comparison/article/fig_05_eof1_lec_published_corrected.png)

*EOF 1 LEC loadings fitted independently to the published and corrected populations, then pattern-matched and sign-aligned.*

### Figure 6

![Figure 6](../../figures/comparison/article/fig_06_eof2_lec_published_corrected.png)

*EOF 2 LEC loadings fitted independently to the published and corrected populations, then pattern-matched and sign-aligned.*

### Figure 7

![Figure 7](../../figures/comparison/article/fig_07_eof3_lec_published_corrected.png)

*EOF 3 LEC loadings fitted independently to the published and corrected populations, then pattern-matched and sign-aligned.*

### Figure 8

![Figure 8](../../figures/comparison/article/fig_08_eof4_lec_published_corrected.png)

*EOF 4 LEC loadings fitted independently to the published and corrected populations, then pattern-matched and sign-aligned.*

### Figure 9

![Figure 9](../../figures/comparison/article/fig_09_eof_positive_density_published_corrected.png)

*Positive total-lifecycle PC-extreme track densities: published on the left and corrected on the right.*

### Figure 10

![Figure 10](../../figures/comparison/article/fig_10_eof_negative_density_published_corrected.png)

*Negative total-lifecycle PC-extreme track densities: published on the left and corrected on the right.*

### Figure 11

![Figure 11](../../figures/comparison/article/fig_11_eof_genesis_season_published_corrected.png)

*Genesis-region and seasonal composition of total-lifecycle PC extremes, published on the left and corrected on the right.*

### Figure 12

![Figure 12](../../figures/comparison/article/fig_12_intense_clusters_lec_published_corrected.png)

*Mean LEC of all intense cyclones and four intense-cyclone groups, published on the left and corrected on the right.*

### Figure 13

![Figure 13](../../figures/comparison/article/fig_13_intense_groups_density_published_corrected.png)

*Track densities of the four intense-cyclone PC groups, published on the left and corrected on the right.*

### Figure 14

![Figure 14](../../figures/comparison/article/fig_14_intense_groups_characteristics_published_corrected.png)

*Counts, maximum intensity, seasonality and genesis regions for the four intense-cyclone PC groups.*

### Figure 15

![Figure 15](../../figures/comparison/article/fig_15_phase_synthesis_published_corrected.png)

*Primary-phase LEC synthesis, with the published population on the left and corrected population on the right.*

### Figure 16

![Figure 16](../../figures/comparison/article/fig_16_eof_synthesis_published_corrected.png)

*Phase/EOF-loading synthesis in the article layout, published on the left and corrected on the right.*
