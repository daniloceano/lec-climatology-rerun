# Reprodução de Figures 9–16 — scripts originais como referência

Data: 2026-09-30. A decisão do autor nesta rodada resolve as ambiguidades da
auditoria científica anterior: quatro clusters, Figure 12A
com todos os sistemas e Figure 16 com loadings por fase. Não há decisões científicas
pendentes sobre esses pontos. O manuscrito, os originais e as Figures 5–8 foram
preservados. As Figures 9–16 em `corrected` e `comparison` foram substituídas
pelas versões validadas. A proveniência científica registra o commit-base
da reprodução; a integração Git posterior não altera os valores calculados.

Comando: `python -m scripts.article_figures.reproduce_downstream`.
Somente gate: adicionar `--legacy-only`. O script interrompe a execução na primeira
falha de reprodução; a etapa corrected só começa depois de todos os gates.

Os **novos** candidatos estão em `figures/corrected/article/`,
com tabelas em `results/corrected/article/`. As Figures 9–16 antigas nessa pasta foram substituídas por estes candidatos.
Figures 5–8 e seus inputs canônicos permanecem congelados. Resultados legacy novos estão
em `results/original/article/reproduction_gate/`; são evidências de reprodução,
não substitutos dos arquivos originais. Os painéis antigos da comparison foram
substituídos pelos pares publicado/corrigido correspondentes.

## RESUMO PARA ORQUESTRAÇÃO

### 1. Legacy reproduction gate

| Item | Reproduzido? | Evidência |
|---|---|---|
| PCs legacy | SIM | 6.789 × 8; erro máximo 2,21978e−12; escala derivada dos autovalores, sem fatores copiados |
| EOF +/- assignments | SIM | 5.409 tuplas; diferença simétrica zero |
| intense selection | SIM | exatamente os 679 IDs arquivados; threshold 10,353024 |
| 4-cluster assignments | SIM | zero diferenças; contagens 166/118/75/320; centroides diferem no máximo 4,23217e−13 |
| Figure 12 logic | SIM | 80 pares média/SD transcritos do PNG publicado, todos dentro de 0,005; maior erro 0,00499812 |
| Figure 13 logic | SIM | quatro campos NetCDF arquivados reproduzidos com diferença zero |
| Figure 14 logic | SIM | preprocessing original executado por AST; counts, intensidade, seasonality e genesis conferem |
| Figure 16 logic | SIM | funções originais montam loadings por fase/EOF; nenhuma seleção EOF(+) |

Adicionalmente: oito campos KDE de Figures 9–10 conferem com os NetCDFs originais,
erro máximo 4,65761e−12. Figure 11 confere com as instruções numéricas originais,
56 linhas de composição. A validação é numérica e de lógica, não identidade pixel
a pixel entre diferentes versões de Matplotlib. A Figure 12 publicada foi inspecionada;
a fixture `tests/fixtures/figure12_published_annotations.csv` contém todos os
16 termos visíveis em cada um dos cinco painéis, com média e SD.

### 2. Total EOF matching

|   Reference EOF |   Corrected raw rank |      Sign |   Pattern correlation |   EV legacy |   EV corrected |
|----------------:|---------------------:|----------:|----------------------:|------------:|---------------:|
|        1.000000 |             1.000000 |  1.000000 |              0.798217 |   28.303950 |      27.683925 |
|        2.000000 |             2.000000 | -1.000000 |              0.961399 |   11.017594 |      12.021767 |
|        3.000000 |             3.000000 |  1.000000 |              0.578515 |   10.925190 |      10.510169 |
|        4.000000 |             5.000000 |  1.000000 |              0.766757 |    8.187725 |       7.571698 |
|        5.000000 |             4.000000 | -1.000000 |              0.505205 |    7.409998 |       8.708047 |
|        6.000000 |             6.000000 | -1.000000 |              0.848460 |    5.855232 |       5.757871 |
|        7.000000 |             7.000000 |  1.000000 |              0.862387 |    5.236366 |       4.755310 |
|        8.000000 |             8.000000 |  1.000000 |              0.499771 |    4.362477 |       4.282008 |

Hungarian sobre −|correlação de Pearson| dos mesmos 24 termos, primeiros oito
modos, one-to-one; em seguida sign alignment à orientação do arquivo publicado.
Mesma permutação e mesmo sinal nos PCs e loadings. EV segue o raw rank.
As correlações de EOF3, EOF5 e EOF8 são moderadas/baixas; assignment não demonstra
identidade física. O arquivo `total_eof_mapping.csv` registra todos os campos,
incluindo os autovalores corrected.

### 3. PC convention

O script original normaliza anomalias com SD amostral, e `pyEOF.df_eof` executa
internamente `StandardScaler` (SD populacional). Se μ é o autovalor da matriz de
correlação amostral, λ = μ N/(N−1) = 24 × EV × N/(N−1).
Assim, `pcs(s=2) = PC_unit_sample × λ`, equivalente a
`PCA.transform(Z_pop) × sqrt(λ)`; `eofs(s=2) = V × sqrt(λ)`.
Cada versão calcula seus próprios autovalores. Não se copiam escalas legacy.

| pc   |   legacy SD |   corrected SD |
|:-----|------------:|---------------:|
| PC1  |    6.793949 |       6.645882 |
| PC2  |    2.644612 |       2.885979 |
| PC3  |    2.622432 |       2.523101 |
| PC4  |    1.965343 |       1.817683 |
| PC5  |    1.778661 |       2.090479 |
| PC6  |    1.405463 |       1.382251 |
| PC7  |    1.256913 |       1.141573 |
| PC8  |    1.047149 |       1.027951 |

Diferença máxima versus os PCs legacy arquivados: **2,219779915435538e−12**.
Código pyEOF instalado, metadata de scikit-learn e histórico conda são fontes
hashadas no manifest. A ordem de linhas para K-means reproduz a ordem do arquivo
PC legacy; no corrected, restringe essa ordem aos 3.820 IDs comuns. Isto evita
introduzir outra ordem de amostragem do gerador aleatório. Não houve tuning.

### 4. Figures 9–10

Quantis q90/q10 marginais nos oito PCs de toda a população de cada versão.
Inclui um sistema se qualquer PC ≥q90 ou ≤q10; dominante = `idxmax` no positivo,
`idxmin` no negativo, sobre todos os oito PCs. Depois exclui dominantes 5–8.
Empate: primeira coluna. Pode pertencer a ambos os sinais. O vencedor não precisa
ser o mesmo PC que cruzou seu quantil. Não foi substituído por máximo absoluto.

|   dominant_eof |   legacy + |   legacy − |   corrected + |   corrected − |
|---------------:|-----------:|-----------:|--------------:|--------------:|
|              1 |       1305 |       1334 |           748 |           661 |
|              2 |        433 |        600 |           319 |           343 |
|              3 |        375 |        642 |           261 |           286 |
|              4 |        337 |        383 |           180 |           175 |

Mapping: [1,2,3,5,4,6,7,8], sinais [+1,−1,+1,+1,−1,−1,+1,+1].
KDE: funções originais de `export_density_eof.py`, gaussiana haversine,
bandwidth 0,05 rad, ball_tree, grade 64×128, R=6369,345 km,
densidade = exp(logKDE) × n_rows × 10⁶/R² / num_time.
Unidade: posições de trajetória por 10⁶ km² por mês. Denominador: **505 meses**
comuns, inclusive caudas em janeiro de 2021, em ambas as versões.
Extensão original [−90,180,−15,−90] e mesmos boxes. Os campos numéricos de
densidade não são truncados.

Os limites superiores das barras de cor das Figures 9, 10 e 13 agora usam o
máximo de cada campo, arredondado a duas casas. Mantêm-se 13 intervalos para
os EOFs das Figures 9–10, exceto EOF4(+) com 10, e oito para cada grupo da
Figure 13. Os limites internos seguem passos de 0,5, 1 ou 2 quando isso cabe
no número original de intervalos; nos demais casos são uniformes. Somente o
valor mostrado acima do máximo arredondado é limitado visualmente; os campos
salvos em CSV/NetCDF retêm a precisão integral. O EOF3(+) da Figure 9 passa
de máximo 13,188339 para `vmax=13,19`, sem a antiga região branca.
Outputs: `fig_09_eof_positive_density` e `fig_10_eof_negative_density` (.png/.pdf)
no novo diretório de candidatos.

### 5. Figure 11

Usa o mesmo `eof_extreme_assignments.csv` dos mapas. Estação no primeiro registro
armazenado do track: DJF (12/1/2), MAM (3/4/5), JJA (6/7/8), SON (9/10/11).
Usa `region` original; não recalcula metadata. Boxes publicados:
SE-BR (−52,−38,−37,−23), LA-PLATA (−69,−38,−52,−23), ARG (−70,−55,−50,−39).
Percentuais dentro de cada EOF/sinal, categorias ARG/LA-PLATA/SE-BR e DJF/MAM/JJA/SON.
Valores legacy reproduzidos? **SIM**, comparados ao preprocessing original.
Exemplo corrected EOF3(+): SE-BR 52,4904%; DJF 49,0421%; JJA 4,2146%.
Output: `fig_11_eof_genesis_season` (.png/.pdf).

### 6. Intense selection

Threshold = **10,353024000000001**, percentil 90 dos máximos de `vor42` de
**6.789 tracks**; operador ≥. Confirmação dos 679 IDs legacy arquivados: **SIM**.
Confirmação dos 603 IDs corrected que satisfazem o mesmo critério: **SIM**.
`intense_ids.csv`, manifesto e hashes dos IDs dão a lista completa reproduzível.
Não foi usado q90 das 631.009 rows nem corrected-only q90.

### 7. Clustering

K=4; primeiros 8 PCs matched na convenção s=2; `StandardScaler` ajustado apenas
no subset intenso de cada versão; random_state=42; k-means++; Lloyd; max_iter=300;
tol=1e−4; **n_init='auto' = 1**, explicitado. scikit-learn da execução: **1.7.1**.
Ambiente antigo `data`: **1.4.2**, default auto confirmado no fonte e numa execução
real no seu Python: **zero diferenças** dos 679 labels arquivados.
O teste exigido com n_init=10 diverge em **311 sistemas** após matching de labels.
A escolha de auto decorre do ambiente recuperado, não de busca por parâmetros.

|   Legacy cluster |   Corrected raw cluster matched |   n legacy |   n corrected |   centroid distance |   assignment margin |
|-----------------:|--------------------------------:|-----------:|--------------:|--------------------:|--------------------:|
|         1.000000 |                        3.000000 | 166.000000 |    119.000000 |            1.896020 |            0.150828 |
|         2.000000 |                        2.000000 | 118.000000 |    103.000000 |            2.560793 |            0.150828 |
|         3.000000 |                        4.000000 |  75.000000 |    133.000000 |            1.680689 |            0.156826 |
|         4.000000 |                        1.000000 | 320.000000 |    248.000000 |            0.850759 |            0.594821 |

Matching Hungarian por distância euclidiana R⁸ entre centroides nos espaços de PCs
matched padronizados separadamente nos subsets intensos. Não há rescaling adicional.
`assignment margin` = aumento do custo total da melhor atribuição quando se proíbe
aquela correspondência. Margens ~0,15 para clusters 1–3 indicam ambiguidade de
associação; não equivalência física demonstrada. Matriz completa em
`cluster_distance_matrix.csv`. Labels exibidos 1–4 são identidades legacy.

### 8. Figure 12

12A: todos os **3.820 sistemas**, todas as fases/períodos do cache; média não
ponderada das médias por período e média dos SDs por período, como `plot_LEC_std.py`.
Legacy usou os 6.789 sistemas e nove nomes de período; corrected tem sete.

| term   |      mean |       std |
|:-------|----------:|----------:|
| Cz     |  0.091766 |  4.577506 |
| Ca     |  3.049126 |  4.918268 |
| Ck     | -1.520758 |  8.733037 |
| Ce     |  3.686186 |  4.490975 |
| Gz     | -0.396407 |  2.346683 |
| Ge     |  0.991358 |  2.527369 |
| RKz    |  7.766962 | 38.279507 |
| RKe    | -5.788396 |  9.017667 |

12B–E: **centroid × EOF(s=2) + mean confirmado**. A mean aqui é a climatologia
calculada pela média dos períodos de cada ciclone, depois média dos ciclones.
Não multiplica por SD físico adicional: preserva exatamente a matemática original,
ainda que não seja uma inversão usual de PCA. SD = desvio entre médias por ciclone
dos membros de cada cluster. Os centroides estão na escala PC original, após
inverse_transform do StandardScaler. Quatro grupos 119/103/133/248; nenhuma média
direta de membros substitui a reconstrução. Original renderer e montagem reutilizados.
Tabela `figure12_values.csv`; output `fig_12_intense_clusters_lec` (.png/.pdf).

### 9. Figure 13

Mesma KDE haversine/bandwidth 0,05/grade/unidade das funções originais; usa
`eof_export_density_clusters.py`. Normalização temporal: meses presentes na **união
dos tracks intensos de todos os quatro clusters**, 396 legacy / **375 corrected**.
Esse único denominador é compartilhado pelos quatro grupos de cada versão;
não é occupied months por grupo. Mesmos assignments da Figure 12? **SIM**,
com hashes por cluster em `figure_cluster_memberships.csv`.
Output `fig_13_intense_groups_density` (.png/.pdf); campos em `density_clusters_*.csv.gz`.

### 10. Figure 14

Mesmos assignments 12/13/14? **SIM**. Intensidade é máximo por track.
Counts 119/103/133/248; sazonalidade e distribuição de gênese em percentuais,
conforme o script (o rótulo original de gênese não explicita o símbolo %).

|   cluster |          n |   max_vor42_mean |   max_vor42_median |   season_DJF_pct |   season_MAM_pct |   season_JJA_pct |   season_SON_pct |   region_ARG_pct |   region_LA-PLATA_pct |   region_SE-BR_pct |
|----------:|-----------:|-----------------:|-------------------:|-----------------:|-----------------:|-----------------:|-----------------:|-----------------:|----------------------:|-------------------:|
|  1.000000 | 119.000000 |        11.509915 |          11.383970 |        16.806723 |        21.848739 |        41.176471 |        20.168067 |        42.016807 |             36.134454 |          21.848739 |
|  2.000000 | 103.000000 |        12.147619 |          11.803110 |        13.592233 |        16.504854 |        40.776699 |        29.126214 |        34.951456 |             43.689320 |          21.359223 |
|  3.000000 | 133.000000 |        11.636211 |          11.344360 |        27.067669 |        27.067669 |        25.563910 |        20.300752 |        43.609023 |             39.097744 |          17.293233 |
|  4.000000 | 248.000000 |        11.631800 |          11.434470 |        21.774194 |        21.774194 |        26.209677 |        30.241935 |        39.112903 |             37.903226 |          22.983871 |

Distribuições individuais de intensidade em `figure14_intensity.csv`;
output `fig_14_intense_groups_characteristics` (.png/.pdf).

### 11. Figure 16

Usa phase EOF loadings? **SIM**. Usa matched identities de Figures 5–8? **SIM**.
Valores por phase/reference EOF/term idênticos aos inputs canônicos de 5–8? **SIM**,
384 valores, teste de igualdade exata. Usa `read_phase_product` e o arquivo congelado
`results/comparison/article/phase_eof_matched/loadings.csv`; não recalcula nem
muda a orientação desses produtos. Renderiza usando `draw_lec_eofs.py`/
`draw_lec_v6.py`, normalização min_max original entre fases.
Tabela `figure16_loadings.csv`; output `fig_16_eof_synthesis` (.png/.pdf).
Figure 15 também foi regenerada com `draw_lec_v6.py`, médias corrected por fase,
normalização log original; tabela `figure15_phase_means.csv`.

### 12. Discrepâncias publicadas documentadas

| Tema | Texto/pressuposto conflitante | Comportamento reproduzido |
|---|---|---|
| EOF dominante | highest absolute PC | idxmax positivo / idxmin negativo, seleção marginal anterior, oito PCs |
| Quantidade de clusters | five em Methods/captions | quatro grupos arquivados e figuras; decisão fechada |
| Figure 16 | mean LEC dos grupos EOF(+) | síntese dos phase EOF loadings; decisão fechada |
| Figure 12A | média simples sugerida pelo rótulo All Systems Mean ± Std | média de médias por período e média dos SDs por período |
| Figure 12B–E | interpretação como médias observadas dos membros | centroid @ eofs(s=2) + média climatológica; SD dos membros |
| Figure 14 gênese | eixo Frequency by Genesis Region sem % | percentuais, não contagens |
| Exposição temporal | assumir período fixo idêntico para todos os mapas | EOFs: 505 meses; clusters: meses da união dos intensos, 396 → 375 |
| PCs normalizados | SD=1 | pcs(s=2), SD=λ; unidade e escala não intercambiáveis na dominância |
| n_init omitido | assumir default 10 | ambiente histórico 1.4.2 usa auto=1 e reproduz arquivo |
| Contornos de Figure 9 | renderer original com máximo fixo | o renderer atual usa o máximo observado e mantém o número de intervalos |

A tabela é documentação para a futura Correction; nenhum LaTeX foi editado.

### 13. Verificação atual

O gate legado registra oito checks aprovados em
`results/original/article/reproduction_gate/manifest.json`. As tabelas
canônicas de quatro clusters estão em `results/original/article/` e
`results/corrected/article/`; os CSVs com `version=before/after` estão em
`results/comparison/article/`. Os manifests e a proveniência registram os
hashes dos resultados e das figuras. A suíte atual é executada com
`python -m pytest -q`.

### 14. Resultados e figuras

As Figures 9–16 corrigidas estão diretamente em `figures/corrected/article/`.
Os oito painéis publicado/corrigido estão em `figures/comparison/article/`.
O `figure_manifest.csv` de cada família cobre as 16 figuras do artigo; o
`figure_manifest_09_16.csv` em corrected registra o subconjunto regenerado.
Os produtos de cinco clusters foram removidos. Figures 5–8 usam o produto
canônico de EOF por fase em `results/comparison/article/phase_eof_matched/`.
A Table 1 corrigida usa os 15.829 registros de período e está em
`tables/corrected/article/`, com estatísticas completas em
`results/corrected/article/`.

As limitações interpretativas dos modos e clusters, inclusive correlações
moderadas entre alguns padrões, permanecem descritas acima. O antigo vazio
de contorno em EOF3(+) foi resolvido pelo limite derivado dos dados.
