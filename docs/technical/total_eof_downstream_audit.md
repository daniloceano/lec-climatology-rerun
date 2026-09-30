# Auditoria de total-lifecycle EOFs e produtos downstream

Registro histórico: as pendências e o diagnóstico abaixo precedem a reprodução
validada. O estado atual das Figures 9–16 está em
[`downstream_reproduction.md`](downstream_reproduction.md).

Data: 2026-09-30. Diagnóstico concluído; **os produtos atuais não são substitutos
cientificamente validados do artigo**. A consistência interna de uma permutação
não demonstra que a referência, escala dos PCs, população ou definição da figura
sejam as publicadas. Nenhum produto científico existente foi alterado.

O comando reproduzível é `python -m scripts.article_figures.audit_total_eof_downstream`.
Ele não refaz K-means, KDE, mapas ou figuras. Recalcula apenas os pequenos problemas
de autovalores e estatísticas tabulares, verifica hashes e lê assignments existentes.
Os arquivos externos usados são explicitamente nomeados em configuração,
proveniência ou scripts originais; nenhum diretório foi copiado. As fontes sem
pin prévio são identificadas como tal na nova proveniência, não promovidas a uma
referência publicada garantida. A Figure 16 e a Figure 12 originais foram vistas
além da inspeção do TeX e dos scripts.

## RESUMO PARA ORQUESTRAÇÃO

### 1. Estado geral

| Produto | Status | Evidência e alcance |
|---|---|---|
| Figures 9–10 | BLOCKED | Comparação alinha PCs à referência recalculada, que inverte 4 sinais publicados e altera a escala; corrected-only usa raw ranks; densidade comparison tem outra definição. |
| Figure 11 | BLOCKED | Tabelas reproduzem as barras atuais, mas herdam os memberships cientificamente divergentes de 9–10. |
| Figure 12 | BLOCKED | Threshold, 4 versus 5 clusters, população do painel A e reconstrução versus médias diretas divergem. |
| Figure 13 | BLOCKED | IDs coerentes com os clusters atuais; seleção, identidade publicada e normalização temporal não validadas. |
| Figure 14 | BLOCKED | Estatísticas atuais reproduzidas; mesmas limitações científicas dos clusters. |
| Figure 16 | BLOCKED | Caption e script original descrevem objetos distintos; comparison INVALID_AS_REPLACEMENT; geração impedida explicitamente. |

Populações confirmadas nos caches com hashes corretos: legacy **6.789 ciclones /
25.000 rows** e corrected **3.820 / 15.829**. Todos os 3.820 corrected IDs estão
no legacy; nenhum caso é perdido por valores faltantes na decomposição total.
São populações independentes para o ajuste, mesmo tendo interseção. Os tracks têm
**631.009 registros, 6.789 ciclones, 505 meses**, de 1979-01-01 até 2021-01-07;
os sete dias de janeiro de 2021 são caudas de trajetórias, não uma escolha nova
de período nesta auditoria.

`independent_total_eof` (`common.py:457`) faz exatamente
`groupby(track_id)[EOF_TERMS].mean()` sobre **todos** os períodos arquivados,
e depois correlation EOF sobre 24 termos padronizados com `ddof=1`. Cada período
contribui igualmente à média de seu ciclone, sem ponderação pela duração.

| version   | period            |   rows |   cyclones |
|:----------|:------------------|-------:|-----------:|
| before    | decay             |   6488 |       6488 |
| before    | decay 2           |   1119 |       1119 |
| before    | incipient         |   4587 |       4587 |
| before    | incipient 2       |      1 |          1 |
| before    | intensification   |   6642 |       6642 |
| before    | intensification 2 |    552 |        552 |
| before    | mature            |   4747 |       4747 |
| before    | mature 2          |    301 |        301 |
| before    | residual          |    563 |        563 |
| after     | decay             |   3820 |       3820 |
| after     | decay 2           |    183 |        183 |
| after     | incipient         |   3820 |       3820 |
| after     | intensification   |   3820 |       3820 |
| after     | intensification 2 |    183 |        183 |
| after     | mature            |   3820 |       3820 |
| after     | mature 2          |    183 |        183 |

**ARTICLE COMPARISON:** ajustes independentes 6.789 → 3.820; diferenças combinam
toolkit e população. **PAIRED CONTROL:** loader `load_comparison_inputs` restringe
ambos a 3.820 IDs e **15.280 rows**, quatro fases primárias. `paired_total_eof`
ajusta uma referência própria e `assign_eof_extremes` seleciona sobre quatro PCs.
Não é a mesma agregação ou regra de extremos da comparação literal. As tabelas
`paired_control_*` são um diagnóstico numérico separado do código paired, não
uma afirmação de que todo PDF antigo foi regenerado/revalidado.
Jaccard restrito aos IDs comuns NÃO é chamado paired control: preserva os
ajustes e thresholds independentes originais.

### 2. Total-lifecycle EOF mapping

**Sign abaixo = multiplicador do corrected raw mode para a orientação do arquivo
EOF publicado/arquivado**, não a orientação interna atualmente usada. EV em %.
A permutação usa Hungarian sobre `-abs(corrcoef)` dos mesmos 24 termos; é restrita
aos primeiros oito modos e one-to-one. Não foi investigado matching com ranks >8.

|   reference_eof |   corrected_raw_rank | rank_swap   |   Sign to published |   pattern_correlation |   ev_published |   ev_corrected |   max_absolute_loading_difference_published |
|----------------:|---------------------:|:------------|--------------------:|----------------------:|---------------:|---------------:|--------------------------------------------:|
|               1 |                    1 | False       |                   1 |              0.798217 |      28.303950 |      27.683925 |                                    1.304524 |
|               2 |                    2 | False       |                  -1 |              0.961399 |      11.017594 |      12.021767 |                                    0.186029 |
|               3 |                    3 | False       |                   1 |              0.578515 |      10.925190 |      10.510169 |                                    0.664495 |
|               4 |                    5 | True        |                   1 |              0.766757 |       8.187725 |       7.571698 |                                    0.402621 |
|               5 |                    4 | True        |                  -1 |              0.505205 |       7.409998 |       8.708047 |                                    0.651756 |
|               6 |                    6 | False       |                  -1 |              0.848460 |       5.855232 |       5.757871 |                                    0.314112 |
|               7 |                    7 | False       |                   1 |              0.862387 |       5.236366 |       4.755310 |                                    0.206826 |
|               8 |                    8 | False       |                   1 |              0.499771 |       4.362477 |       4.282008 |                                    0.590786 |

A referência atual difere da orientação arquivada pelo vetor
`[+1, -1, -1, +1, -1, -1, +1, +1]`. Para essa referência interna, os signs
corrected são `[+1, +1, -1, +1, +1, +1, +1, +1]`; para a orientação publicada,
`[+1, -1, +1, +1, -1, -1, +1, +1]`. As correlações absolutas entre loadings legacy
recalculados e arquivados são 1 a precisão numérica; há pequena diferença de
normalização dos loadings, preservada no CSV, sem efeito sobre o matching.
`compute_eof` escolhe como positivo o maior loading absoluto; essa convenção não
preserva por si só o sinal publicado. Não foi alterada, pois também alimenta
outras famílias de produtos.

Os modos **3 (0,579), 5 (0,505) e 8 (0,500)** têm correspondência moderada/baixa;
1 e 4 também não são idênticos (0,798 e 0,767). Não se impôs um cutoff inventado
nem se interpretou correlação como garantia de identidade física. `reference_eof`,
`raw_rank` e ambos os signs são separados na tabela de auditoria. Os produtos
antigos ainda têm `eof`/`matched_rank` e não explicitam esse duplo referencial.

### 3. Propagação para PCs

- Mesma permutation para loadings e PCs? **SIM**, na comparison e no paired;
  `[1,2,3,5,4,6,7,8]` na comparação literal, sem duplicar raw modes.
- Mesmo sign? **SIM**, incluindo PC3 multiplicado por −1 na referência atual.
- EV acompanha o raw mode? **SIM**: EOF4 usa EV de raw5 = 7,571698%; EOF5 usa
  EV de raw4 = 8,708047%.
- q90/q10 após alignment? **SIM** na comparison; **NÃO há alinhamento à referência**
  no corrected-only (`total_eof(raw)` em `generate_corrected_article.py`).
- Raw rank e reference identity separados? **Parcialmente**: comparison mantém
  `matched_rank` na variância; scores só se chamam PC1–PC8. Corrected-only usa
  raw ranks sob esses nomes. A auditoria agora explicita o significado.
- Inconsistências? **SIM**, mas não foi achado bug de permutation conjunta no
  `align_eofs`. A referência e a escala diferem do arquivo publicado, e os dois
  workflows usam convenções incompatíveis.

Os PCs arquivados, provenientes de `pyEOF.pcs(s=2)`, têm desvios-padrão
`[6.793949,2.644612,2.622432,1.965343,1.778661,1.405463,1.256913,1.047149]`;
os PCs atuais têm SD = 1. Restaurar só os signs deixa **3.157** diferenças
simétricas em tuplas `(track_id, sign, dominant_eof)` contra o arquivo original.
Restaurar signs E os fatores de escala arquivados reproduz exatamente seus
**5.409 assignments**. O produto atual tem **3.591 assignments** e **6.168**
diferenças simétricas. Isso não corresponde a 6.168 ciclones únicos.
A escala não altera um quantil marginal sob multiplicação positiva, mas altera
`idxmax/idxmin` entre PCs e, portanto, a identidade dominante.

### 4. Figures 9–10

Counts abaixo pertencem aos produtos **atuais da comparison**, com orientação
interna recalculada; não são apresentados como contagens publicadas validadas.
Jaccard = interseção/união dos conjuntos completos de IDs por grupo.

|   reference_eof |   before_q90_n |   after_q90_n |   before_q10_n |   after_q10_n |   Jaccard q90 |   Jaccard q10 |
|----------------:|---------------:|--------------:|---------------:|--------------:|--------------:|--------------:|
|        1.000000 |     437.000000 |    245.000000 |     492.000000 |    286.000000 |      0.403292 |      0.296667 |
|        2.000000 |     424.000000 |    224.000000 |     450.000000 |    260.000000 |      0.197782 |      0.411531 |
|        3.000000 |     424.000000 |    255.000000 |     430.000000 |    281.000000 |      0.212500 |      0.045588 |
|        4.000000 |     491.000000 |    262.000000 |     443.000000 |    203.000000 |      0.238487 |      0.053834 |

Quantis são recalculados **separadamente por PC e versão**, sobre toda sua
população de scores; nenhum threshold numérico publicado fixo é usado.
Seleciona-se qualquer PC ≥q90 ou ≤q10 dentre oito; dominante é `idxmax` para
positivo e `idxmin` para negativo sobre os oito, depois só se retêm identidades
1–4. Empates escolhem a primeira coluna. Um sistema pode aparecer nos dois signs
(**392 before, 238 after**), mas no máximo uma vez por sign. PC5–8 influenciam a
seleção e competição; seus counts finais iguais a zero significam exclusão após
a atribuição, não ausência de extremos marginais. A regra não exige que o PC
vencedor seja aquele que ultrapassou seu próprio quantil.

Há outro conflito de definição: o TeX, linha 233, diz maior **valor absoluto**;
o frozen script `attribute_track_ids_to_eof_extremes.py` usa os dois redutores
assinados descritos acima. O código atual reproduz essa regra de script, não o
texto de maneira literal. É necessária decisão do autor; não foi substituída
pela regra absoluta nesta rodada.

|   reference_eof |   archived_published_q90_n |   archived_published_q10_n |   corrected_only_raw_q90_n |   corrected_only_raw_q10_n |
|----------------:|---------------------------:|---------------------------:|---------------------------:|---------------------------:|
|        1.000000 |                1305.000000 |                1334.000000 |                 250.000000 |                 283.000000 |
|        2.000000 |                 433.000000 |                 600.000000 |                 230.000000 |                 257.000000 |
|        3.000000 |                 375.000000 |                 642.000000 |                 224.000000 |                 283.000000 |
|        4.000000 |                 337.000000 |                 383.000000 |                 218.000000 |                 233.000000 |

No subconjunto retido em ambas as versões: **111/678 positivos** e **195/644
negativos** mudam de dominante. Nos IDs comuns: **25** passam de exclusivamente
positivo a exclusivamente negativo e **34** no sentido contrário. Quem aparece
nos dois signs é excluído dessa definição de troca. Esses números já usam
alignment à referência interna; não são trocas causadas por sinal arbitrário
adicional do solver. Também não isolam toolkit de população/threshold.
Os testes invertem um raw mode de cada vez e recuperam exatamente todos os
assignments após alignment. Corrected-only versus comparison-after tem **2.056**
diferenças simétricas nas tuplas de assignments.

Os mapas da comparison usam `track_density`: histograma 2° + Gaussian filter
sigma=1,4, unidades pontos de trajetória/mês; normalizador = meses ocupados
**por grupo**. O artigo usa KDE haversine, bandwidth 0,05 rad, por 10⁶ km²/mês.
Na comparison q90 before os meses são 308/294/288/313; after 215/186/219/208.
Para q10: 331/295/305/305 → 231/216/222/182. O corrected-only usa 505 meses comuns
para os EOFs e KDE, mas também limita valores máximos às contour levels.
Não são mapas quantitativamente intercambiáveis. Nenhum mapa foi recalculado.

### 5. Figure 11

`generate_comparison.fig11` recebe exatamente os assignments de Figures 9–10;
`figure11_composition.csv` contém EOF × sign × região/estação × versão, n,
denominador e porcentagem, também para corrected-only (identidade raw).
Teste com captura das entradas de `_grouped_bars` reproduz os **oito painéis
categoriais** da comparison (oito chamadas, uma matriz de quatro EOFs em cada),
sem gravar figura. A tabela reproduz os valores do renderer atual; não prova
por si só o histórico pixel a pixel de uma imagem já existente. Os hashes dos
arquivos do manifest foram conferidos.

Maiores deltas atuais: EOF3(−) DJF **24,419 → 47,331% (+22,912 pp)** e JJA
**26,512 → 4,270% (−22,241 pp)**; EOF4(−) DJF **44,244 → 24,138% (−20,106 pp)**.
Gênese: EOF3(−) ARG **70,000 → 19,929% (−50,071 pp)**; EOF4(−) ARG
**27,765 → 73,892% (+46,126 pp)**, SE-BR **40,632 → 9,852% (−30,780 pp)**.
Não interpretar esses deltas como efeito isolado da correção científica.

O input de tracks não foi alterado. O arquivo processado não tem coluna `region`;
o workflow deriva primeira posição/estação a cada execução. As classificações
foram comparadas ao `region` do track original: **0 divergências/6.789**,
ARG=4.015, LA-PLATA=1.288, SE-BR=1.486, OTHER=0. Datas, IDs, vorticidade e latitude
coincidem; longitude difere no máximo 3,55e−15 por serialização. Estações são
DJF/MAM/JJA/SON pelo mês da gênese; boxes inclusivos (lon_min,lat_min,lon_max,lat_max):
SE-BR (−52,−38,−37,−23), LA-PLATA (−69,−38,−52,−23), ARG (−70,−55,−50,−39).
Não houve nova estimação de trajetórias nem alteração de metadata física.

### 6. Intense-cyclone selection

Variável: `vor42`, vorticidade central 850 hPa tal como arquivada. Intensidade de
cada sistema = máximo ao longo do track. TeX 235 e captions 408/422: máximo acima
do percentil 90. O script `eofs_kmeans_pcs.py` calcula q90 sobre **máximos por ID**
do arquivo de tracks inteiro (6.789 IDs), e seleciona `>=`. O percentil não é
um valor fixo textual publicado; é recalculado do input de tracks comum.

| definition                        | variable   |   threshold | operator   |   quantile |   threshold_population_n |   n_before |   n_after |   threshold_equal_cyclones |
|:----------------------------------|:-----------|------------:|:-----------|-----------:|-------------------------:|-----------:|----------:|---------------------------:|
| current_comparison_track_rows     | vor42      |    8.292780 | >          |   0.900000 |                   631009 |       1744 |      1486 |                          0 |
| published_script_all_track_maxima | vor42      |   10.353024 | >=         |   0.900000 |                     6789 |        679 |       603 |                          0 |
| TeX_strict_all_track_maxima       | vor42      |   10.353024 | >          |   0.900000 |                     6789 |        679 |       603 |                          0 |
| sensitivity_legacy_EOF_maxima     | vor42      |   10.353024 | >          |   0.900000 |                     6789 |        679 |       603 |                          0 |
| sensitivity_corrected_EOF_maxima  | vor42      |   11.138933 | >          |   0.900000 |                     3820 |        432 |       382 |                          0 |

Legacy implementado na comparison: q90 dos **631.009 registros** = **8,292780**;
corrected comparison usa exatamente o mesmo threshold/track population, mas o
critério é incorreto frente ao script de clustering original. Resulta em
**1.744 → 1.486** sistemas (1.065 e 883 adicionais ao critério por máximo).
Corrected-only usa o q90 dos 6.789 máximos = **10,353024**, retendo **603**.
Os **679** IDs dos clusters arquivados coincidem exatamente com a seleção por
máximo original. Nenhum máximo é igual ao threshold: `>`/`>=` não muda IDs aqui.

**Implementation == published definition? NÃO na comparison; SIM para a regra
por máximo no corrected-only**, mas persiste a decisão de manter população de
tracks comum ou recalcular q90 entre apenas 3.820 corrected. Esta segunda opção
é apenas sensibilidade: threshold **11,138933**, 382 corrected, não adotada.

### 7. Clustering / Figures 12–14

- Publicado no TeX, seção 402 e captions 408/422/430: **cinco**; entretanto
  discussão 480 diz quatro, Figure 12 original mostra quatro, script de montagem
  inclui quatro e assignments arquivados têm **166/118/75/320** sistemas
  (clusters originais 1–4 após +1). **Conflito bloqueante**, sem escolha automática.
- Comparison: **cinco**, usando primeiros **oito PCs totais em identidade da
  referência recalculada**, conjuntamente sign-aligned. Não lê arquivo antigo
  de quatro clusters para produzir os seus cinco.
- Corrected-only: **quatro**, oito PCs de raw rank, `StandardScaler` ajustado nos
  603 intensos, `KMeans(n_clusters=4, random_state=42, n_init=10)`.
- Script original: StandardScaler nos intensos; Elbow com `KMeans()` sem seed
  explícita para escolher K; ajuste final `random_state=42`, `n_init` omitido
  (default dependente da versão de sklearn, ambiente original não fixado).
- Comparison: K-means próprio, k-means++, 30 restarts, seeds **42..71**, até 300
  iterações, menor inertia; não aplica StandardScaler no subset intenso.
  PCs têm SD=1 na população completa, mas SD dos intensos before varia
  **0,796–0,949**, after **0,903–1,138**; isso não equivale ao script publicado.
- O label "raw cluster" da metadata da comparison já é ordenado por tamanho
  decrescente pelo helper; não é o label arbitrário original de sklearn.

Matching de clusters é **outra permutação**, feita em R⁸ dos PCs já alinhados,
usando distância euclidiana sem rescaling adicional e Hungarian one-to-one.
A unidade estatística é aproximadamente comparável na população completa,
mas as bases EOF não são idênticas e a padronização nos intensos diverge.
Não existe mapeamento demonstrado dos cinco legacy recalculados aos quatro
clusters efetivamente arquivados. "Reference cluster" abaixo significa apenas
legacy recalculado atual, **não identidade publicada validada**.

|   reference_cluster |   corrected_raw_cluster |   distance |   n_before |    n_after |
|--------------------:|------------------------:|-----------:|-----------:|-----------:|
|            1.000000 |                1.000000 |   0.594618 | 662.000000 | 647.000000 |
|            2.000000 |                2.000000 |   2.432421 | 332.000000 | 266.000000 |
|            3.000000 |                3.000000 |   1.397012 | 290.000000 | 229.000000 |
|            4.000000 |                4.000000 |   0.469343 | 248.000000 | 206.000000 |
|            5.000000 |                5.000000 |   1.633487 | 212.000000 | 138.000000 |

Os centroides foram recalculados a partir dos **assignments já salvos**, sem
refazer K-means, e conferem com os arquivos (erro compatível com CSV).
`cluster_centroid_differences.csv` e `cluster_distance_matrix.csv` contêm os oito
deltas por par e as 25 distâncias. O cluster 2 tem distância **2,432421** e prefere
individualmente raw1; a restrição global aloca raw2. Proibir o par 1→1 ou 2→2
piora o custo total somente **0,012059**: matching 1/2 ambíguo. Os demais gaps
são 1,198468 / 2,537080 / 1,525145. Distância curta não prova equivalência física.

### 8. Consistência Figures 12–14

| Pergunta | Comparison | Corrected-only / relação entre workflows |
|---|---|---|
| Mesma intense population em 12b/13/14? | SIM por versão | SIM dentro do workflow; NÃO entre workflows: 1.486 versus 603 |
| Mesmos cluster assignments em 12b/13/14? | SIM, teste de captura de IDs | SIM no código, quatro clusters; não matched aos publicados |
| Figure 12 memberships == Figure 13? | SIM para 12a união e 12b grupos | NÃO para 12a: usa todos os 3.820; SIM para 12b |
| Figure 13 memberships == Figure 14? | SIM | SIM |
| Matched labels em todas? | SIM aos legacy recalculados | NÃO, labels K-means raw (+1) |
| Algum artefato/cadeia de quatro clusters participa? | NÃO na geração independente de cinco | SIM: ramo corrected-only ativo, não apenas arquivo morto |

A Figure 12a da **comparison** é média de todos os intensos auditados (1.744/1.486),
com média dos períodos por ciclone antes da média do grupo; não mistura versões.
A Figure 12a **publicada** tem rótulo All Systems e Ca=0,80, Ck=−2,92, Ce=3,15:
o caption e script também especificam todos os sistemas. A corrected-only mantém
essa população completa (3.820; Ca=2,967781, Ck=−1,121792, Ce=4,112750).
A solicitação de testar 12a como "all intense" é satisfeita para a comparison,
mas não deve ser projetada como se fosse a definição publicada.

Na comparison 12a, Ca **1,479047→4,505103**, Ck **−5,948357→−2,177117**,
Ce **5,600107→5,692415**. O grupo de 603 intensos do corrected-only teria
Ca=5,471070 e Ce=6,864417, diferente de seu painel 12a efetivo.
Todas as médias/SD dos 24 termos por grupo estão em `figure12_lec_statistics.csv`.
Além da seleção, o script original de 12b calcula **centroides @ EOFs + média
global**, com SD dos membros; os dois workflows atuais calculam **médias diretas**
dos membros. Não são automaticamente o mesmo estimador. Revisão científica
necessária antes de escolher como corrigir.

Figure 13: todos os IDs dos assignments atuais existem nos tracks, ver hashes
por grupo em `figure12_14_membership_checks.csv` e `figure13_density_membership.csv`.
Comparison não lê NetCDF: gera arrays diretamente de tracks. Corrected-only grava
NetCDF em TemporaryDirectory nova; não há reutilização de NetCDF velho no código
inspecionado. Porém `--resume-after-13` da comparison apenas verifica presença
de figuras, sem amarrar hashes de memberships às imagens: **não há prova histórica
por ID de cada PNG**. Os manifests provam integridade dos PNGs, não essa vinculação.

Meses por cluster comparison: before **397/274/226/223/203**, after
**397/232/192/191/143**. Isso divide por meses ocupados de cada cluster e não por
uma exposição temporal comum. Corrected-only usa **375** meses para todos os
quatro grupos (união dos 603 intensos); grupos ocupam 118/133/245/99 meses.
O original de clusters usa a união dos tracks selecionados para todos os grupos;
esta não é a política da comparison. Janeiro/2021 está incluído no input atual.

Figure 14: n, média/mediana de intensidade, quartis/range para boxplots,
seasonality e genesis estão em `cluster_statistics_audit.csv`; os campos já
arquivados conferem nas duas cadeias. Comparação usa porcentagens para
season/genesis; o caption do artigo fala em contagem na gênese, outra diferença
a explicitar caso se pretenda substituição literal.

### 9. Figure 16

**O que representa a Figure 16 publicada?** O TeX pretende **B: mean LEC por fase
de grupos positivos dos PCs totais**; o script original implementa **A: síntese
de loadings de EOFs por fase/rank**. Conclusão científica final: **D — não resolvido**
devido ao conflito entre caption e implementação, não por ausência de busca.

Corrected-only atual = A, raw phase rank; comparison = média LEC total dos grupos
positivos atuais, um LEC por versão, sem quatro fases. **Mesmo objeto? NÃO.**
A comparison é **INVALID_AS_REPLACEMENT**; nenhum dos dois pode substituir
inequivocamente a figura publicada. Não foi "consertada" a definição.
Detalhes e cadeia de evidências em `figure16_definition_audit.md`.

Fontes prioritárias: TeX final 467–473; imagem original, byte-idêntica à do TeX;
`tests_draw_lec/draw_lec_eofs.py`; frozen EOF/extrêmes scripts; raw snapshots da
Figure 16 corrigida e assignments atuais. O hash da imagem original é
`6cf2260b76abb146429d35a9dee1159a57704c6e7a540c234c066a86cc4081f2`.

Foi adicionado guard explícito aos entry points de Figure 16 e aos três geradores
completos (comparison literal, corrected-only e paired), **antes de qualquer
escrita**. Falham com `BLOCKED Figure 16 / INVALID_AS_REPLACEMENT`. O gerador
dedicado de Figures 5–8 não foi alterado.

### 10. Problemas encontrados e correções feitas

| Problema | Impacto | Corrigido? | Arquivos alterados |
|---|---|---|---|
| Referência total atual inverte signs publicados 2/3/5/6 | 9–11 e interpretação downstream | Não; diagnóstico e teste xfail | novo audit e testes |
| PCs unitários versus escala publicada s=2 | Dominância e memberships mudam | Não; exige definição junto com regra dominante | novo audit e testes |
| Corrected-only usa raw ranks/signs | EOF3/4 e outros grupos incompatíveis | Não; depende da referência/escala final | novo audit e testes |
| q90 sobre registros na comparison | 1.744/1.486 em vez de 679/603 | Não, BLOCKING ISSUE | novo audit e teste xfail |
| TeX cinco versus imagens/scripts quatro | Identidade dos clusters não estabelecida | Não, NEEDS_AUTHOR_REVIEW | novo audit e teste xfail |
| Scaling e seed/defaults diferentes | Não reproduz clustering publicado | Não | relatório/audit |
| Matching de clusters 1/2 quase empatado | Identidade física incerta | Não | tabela de distâncias/gaps |
| 12a todos versus intensos; 12b reconstrução versus média | Objetos científicos distintos | Não | relatório/audit |
| Densidade/meses e falta de vínculo histórico de IDs | Mapas não intercambiáveis | Não | relatório/audit |
| Figure 16 semanticamente incompatível | Substituição enganosa | **SIM somente proteção fail-fast** | downstream_guards.py e 3 geradores, +12 linhas |

Nenhuma correção numérica foi propagada aos produtos: alterações de sinal apenas
isoladas não resolveriam escala, dominância ou definição; não se gerou um produto
parcial com aparência de validação científica.

### 11. Testes e validação

- `python -m scripts.article_figures.audit_total_eof_downstream`: **107 PASS,
  7 FAIL científicos e 5 BLOCKED de definição** em `consistency_checks.csv`.
  Exit 0 indica conclusão da coleta da auditoria, não aprovação científica.
- `python -m pytest -q tests/test_total_eof_downstream.py tests/test_article_figures.py tests/test_phase_eof_matching.py`:
  **35 passed, 3 xfailed**. Os xfails são explícitos e strict: orientação publicada,
  seleção de intensos e quatro clusters no corrected-only. Não são corrigidos
  nem mascarados como resultados científicos aprovados. Uma falha inicial no
  mock do teste de Figure 14 (coluna `version` duplicada) foi corrigida no teste.
- A/B: one-to-one e permutação/sign/EV conjunta, incluindo função total real.
  C: oito inversões raw arbitrárias sem mudança de memberships.
  D: assignments correspondem aos PCs de referência atuais.
  E/F: captura de features e k=5; matching adversarial não trivial one-to-one.
  G: captura dos IDs que 12/13/14 recebem, sem gerar mapas.
  H: entry points e geradores completos falham antes de acessar inputs/outputs.
- `git diff --check`: sem erros. `git status --short`: abaixo.
- **190/190 arquivos preexistentes** de figures/results/tables preservados,
  incluindo Figures 5–8, todos os mapas e downstream; também **155/155** do
  snapshot congelado da correção de phase EOFs. Nenhum output antigo alterado.
- Hashes dos inputs confirmados: legacy `7a24617e56595737075a8f9975dd0018069196292eab32fd8f5ba2a49e25a16d`;
  corrected `c5efb8242e83aaa85ebd39cc12d5630fc0f70608775a67d32821dc0097d8d4d3`;
  tracks `552a7a0f1218450834c6d34addbec6bc6dda18e1f2a3f21d663a71bccc636b1d`.
  Usou-se o mirror local configurado do swell; o antigo caminho de tracks em
  `paper_energy_patterns` já documentado com hash divergente não foi usado.
- Warnings: nenhuma validação visual de novos outputs (não houve novos outputs);
  falta provenance de ambiente sklearn original; imagens não carregam hashes de
  IDs; fortes conflitos científicos permanecem. Sem reexecução de clustering.

### 12. Arquivos alterados

Apenas três scripts existentes receberam imports/guards; demais arquivos abaixo
são novos. `common.py`, código phase e produtos existentes não foram alterados.
Logs auxiliares em `tmp/` são ignorados pelo Git e não são artefatos de entrega.

- `docs/technical/total_eof_downstream_audit.md`
- `scripts/article_figures/audit_total_eof_downstream.py`
- `scripts/article_figures/downstream_guards.py`
- `scripts/article_figures/generate_article_comparison.py`
- `scripts/article_figures/generate_corrected_article.py`
- `scripts/article_figures/generate_comparison.py`
- `tests/test_total_eof_downstream.py`
- `results/comparison/article/total_eof_audit/archived_cluster_counts.csv`
- `results/comparison/article/total_eof_audit/cluster_centroid_differences.csv`
- `results/comparison/article/total_eof_audit/cluster_distance_matrix.csv`
- `results/comparison/article/total_eof_audit/cluster_feature_scales.csv`
- `results/comparison/article/total_eof_audit/cluster_mapping.csv`
- `results/comparison/article/total_eof_audit/cluster_statistics_audit.csv`
- `results/comparison/article/total_eof_audit/consistency_checks.csv`
- `results/comparison/article/total_eof_audit/figure11_changes.csv`
- `results/comparison/article/total_eof_audit/figure11_composition.csv`
- `results/comparison/article/total_eof_audit/figure12_14_membership_checks.csv`
- `results/comparison/article/total_eof_audit/figure12_lec_statistics.csv`
- `results/comparison/article/total_eof_audit/figure13_density_membership.csv`
- `results/comparison/article/total_eof_audit/figure16_definition_audit.md`
- `results/comparison/article/total_eof_audit/frozen_outputs.json`
- `results/comparison/article/total_eof_audit/intense_selection_audit.csv`
- `results/comparison/article/total_eof_audit/legacy_assignment_sensitivity.csv`
- `results/comparison/article/total_eof_audit/paired_control_extreme_counts.csv`
- `results/comparison/article/total_eof_audit/paired_control_total_variance.csv`
- `results/comparison/article/total_eof_audit/pc_density_membership.csv`
- `results/comparison/article/total_eof_audit/pc_extreme_counts.csv`
- `results/comparison/article/total_eof_audit/pc_extreme_overlap.csv`
- `results/comparison/article/total_eof_audit/pc_membership_changes.csv`
- `results/comparison/article/total_eof_audit/pc_thresholds.csv`
- `results/comparison/article/total_eof_audit/population_periods.csv`
- `results/comparison/article/total_eof_audit/provenance.json`
- `results/comparison/article/total_eof_audit/total_eof_mapping.csv`

### 13. Pendências científicas

1. Fixar orientação e escala publicadas dos PCs totais; resolver maior valor
   absoluto no TeX versus `idxmax/idxmin` separado por sign no script.
2. Confirmar threshold de máximos por ciclone e sua população (tracks históricos
   comuns versus cada população); não manter q90 de registros como equivalente.
3. Resolver **cinco no TeX versus quatro nas figuras/assignments** e identificar
   a referência verdadeira de cada cluster; não reutilizar os quatro como cinco.
4. Fixar scaling, sklearn/n_init e política de reprodutibilidade do clustering.
5. Revisar correspondências EOF3/5/8 e ambiguidade cluster1/2; não aceitar
   automaticamente apenas porque Hungarian retornou uma permutação.
6. Decidir se 12a preserva "all systems" e se 12b usa reconstrução ou médias físicas.
7. Restaurar/definir KDE e exposição temporal comum antes de substituição literal
   de mapas, e incluir hashes de IDs nos manifests de nova geração.
8. Resolver Figure 16 entre caption e script, incluindo resolução por fase.

### 14. Git state

Estado inicial: clean. Branch `main`; HEAD
`213a6397b70dca5bd68d8345f6d34c742b83652b`. Sem reset, descarte, commit ou push.

```text
 M scripts/article_figures/generate_article_comparison.py
 M scripts/article_figures/generate_comparison.py
 M scripts/article_figures/generate_corrected_article.py
?? docs/technical/total_eof_downstream_audit.md
?? results/comparison/article/total_eof_audit/
?? scripts/article_figures/audit_total_eof_downstream.py
?? scripts/article_figures/downstream_guards.py
?? tests/test_total_eof_downstream.py
```

### 15. Recomendação do agente

Nenhuma Figure 9–14 atual deve entrar como substituta direta na Correction.
Tabelas internas e propagação conjunta são utilizáveis como diagnóstico.
Figures 9–11 precisam da referência/escala/regra de extremos publicadas.
Figures 12–14 precisam resolver threshold, K, identidade e estimador LEC.
Mapas precisam da definição e exposição temporal compatíveis.
Figure 16 permanece BLOCKED; comparison INVALID_AS_REPLACEMENT.
Próximo passo mínimo: decisão do autor sobre os conflitos, antes de regenerar.
Preservar a baseline já validada das Figures 5–8.
