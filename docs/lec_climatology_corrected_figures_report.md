# Corrected reproduction of the LEC climatology figures

This report recreates the 16 main figures of *Lorenz Energy Cycle Climatology for the Southwestern Atlantic Cyclones* using the validated LorenzCycleToolKit 2.0.0 rerun. It is a new corrected product; the published/legacy figures are not overwritten.

## Data lineage and scope

- Corrected population: **3,820 cyclones**.
- Primary lifecycle matrix: **15,280 cyclone-phase rows** (incipient, intensification, mature, decay).
- Secondary lifecycle periods remain preserved in the corrected cache but are excluded from these main-article panels, matching the four-phase scope.
- LEC terms derive from the pinned corrected toolkit; track maps and metadata derive from the frozen South Atlantic track dataset.
- All figures are exported as 300-dpi PNG and vector PDF.

## Updated numerical landmarks

| phase | Ca mean | Ck mean | Ce mean | EOF1 variance |
|---|---:|---:|---:|---:|
| incipient | 1.92 | 0.33 | 3.80 | 20.58% |
| intensification | 4.12 | -0.30 | 6.23 | 27.55% |
| mature | 3.67 | -2.43 | 4.55 | 26.30% |
| decay | 2.16 | -2.10 | 1.98 | 29.17% |

The total-lifecycle PC-extreme classification contains 1,205 positive and 1,264 negative assignments (a cyclone may occur once in each sign set because different PCs are assessed independently).

The intense-cyclone analysis uses the published 0.90 pointwise-vorticity quantile criterion and retains **1,486 corrected cyclones**. Four K-means groups are retained for direct structural comparability with the article.

| cluster | n | median maximum vorticity |
|---:|---:|---:|
| 1 | 745 | 9.60 |
| 2 | 421 | 10.61 |
| 3 | 193 | 9.86 |
| 4 | 127 | 11.01 |

## Figures

### Figure 1

![Figure 1](../figures/lec_climatology_corrected/fig_01_track_density.png)

*Track density of the South Atlantic cyclone database and the three coastal genesis regions used in the analysis.*

### Figure 2

![Figure 2](../figures/lec_climatology_corrected/fig_02_lec_reference.png)

*Reference Lorenz Energy Cycle diagram and the principal physical pathways discussed in the article.*

### Figure 3

![Figure 3](../figures/lec_climatology_corrected/fig_03_term_pdfs.png)

*Corrected probability-density functions of energy, conversion, boundary, pressure-work, generation/residual and budget terms.*

### Figure 4

![Figure 4](../figures/lec_climatology_corrected/fig_04_phase_mean_lec.png)

*Corrected mean Lorenz Energy Cycle by primary lifecycle phase; labels show mean plus or minus one sample standard deviation.*

### Figure 5

![Figure 5](../figures/lec_climatology_corrected/fig_05_eof1_lec.png)

*Corrected EOF 1 loadings on the Lorenz Energy Cycle by lifecycle phase.*

### Figure 6

![Figure 6](../figures/lec_climatology_corrected/fig_06_eof2_lec.png)

*Corrected EOF 2 loadings on the Lorenz Energy Cycle by lifecycle phase.*

### Figure 7

![Figure 7](../figures/lec_climatology_corrected/fig_07_eof3_lec.png)

*Corrected EOF 3 loadings on the Lorenz Energy Cycle by lifecycle phase.*

### Figure 8

![Figure 8](../figures/lec_climatology_corrected/fig_08_eof4_lec.png)

*Corrected EOF 4 loadings on the Lorenz Energy Cycle by lifecycle phase.*

### Figure 9

![Figure 9](../figures/lec_climatology_corrected/fig_09_eof_positive_density.png)

*Track densities for cyclones in the positive (upper-decile) extremes of total-lifecycle PCs 1-4.*

### Figure 10

![Figure 10](../figures/lec_climatology_corrected/fig_10_eof_negative_density.png)

*Track densities for cyclones in the negative (lower-decile) extremes of total-lifecycle PCs 1-4.*

### Figure 11

![Figure 11](../figures/lec_climatology_corrected/fig_11_eof_genesis_season.png)

*Genesis-region and seasonal composition of the positive and negative PC extremes.*

### Figure 12

![Figure 12](../figures/lec_climatology_corrected/fig_12_intense_group_lec.png)

*Corrected mean Lorenz Energy Cycle for the intense-cyclone subset and its four deterministic K-means groups.*

### Figure 13

![Figure 13](../figures/lec_climatology_corrected/fig_13_intense_group_density.png)

*Track densities of the four corrected intense-cyclone energy groups.*

### Figure 14

![Figure 14](../figures/lec_climatology_corrected/fig_14_intense_group_characteristics.png)

*Size, maximum intensity, seasonality and genesis-region composition of the corrected intense-cyclone groups.*

### Figure 15

![Figure 15](../figures/lec_climatology_corrected/fig_15_phase_synthesis.png)

*Synthesis of the corrected mean Lorenz Energy Cycle across the four primary lifecycle phases.*

### Figure 16

![Figure 16](../figures/lec_climatology_corrected/fig_16_eof_synthesis.png)

*Synthesis of corrected EOFs 1-4 across the four primary lifecycle phases.*

## Methodological notes

- EOFs are calculated from the correlation matrix of the 24 published LEC terms, separately by primary phase and for the cyclone-mean total lifecycle.
- EOF signs are oriented so that the largest-magnitude loading is positive; the sign itself has no physical meaning.
- Positive/negative EOF maps use upper/lower PC deciles and assign each selected cyclone to the most extreme of EOFs 1-4.
- Intense groups use the original six terms (Ck, Ca, Ke, Ge, BKe and BAe) across four phases without feature scaling. The implementation is deterministic (30 K-means++ restarts, seed 42).
- Density maps use a two-degree histogram followed by a Gaussian smoother; this replaces the legacy BallTree implementation while preserving the plotted scientific quantity and avoiding an unnecessary scikit-learn dependency.
