# Figure 16: conflito bloqueante de definição

Conclusão **D — não resolvido** para o objeto efetivamente publicado. A definição
textual pretendida é **B**, com resolução por fase; a implementação original
inspecionada implementa **A**. Não é legítimo escolher silenciosamente entre elas.

1. Fonte prioritária: `sn-article_rev2.tex`, linhas 467–473, em
   `/Users/danilocoutodesouza/Documents/danilo_thesis_iag/manuscript_lec_climatology/submission_files-clim_dyn_rev2/LEC_climatology_clim_dyn_vCBG-2/`.
   O texto e caption dizem mean LEC de ciclones dos quatro grupos EOF(+); as cores
   representam fases do ciclo de vida. Isso exige memberships dos PCs totais e
   médias LEC por fase desses sistemas, não loadings nem uma única média total.
2. A imagem `figures/original/article/fig_16_eof_synthesis.png` foi inspecionada:
   quatro painéis EOF, quatro cores por fase, sem valores numéricos que permitam
   recuperar a variável de entrada. É idêntica byte a byte ao `EOFs_panel.png`
   incluído pelo TeX: SHA-256
   `6cf2260b76abb146429d35a9dee1159a57704c6e7a540c234c066a86cc4081f2`.
3. `tests_draw_lec/draw_lec_eofs.py`, na raiz do manuscrito: `load_eofs_data`
   lê `eofs.csv` de cada fase; `create_individual_eof_dataframes` junta a mesma
   posição/rank entre fases; `plot_lorenzcycletoolkit` passa esses loadings a
   `plot_period_means(..., "min_max")`. Não lê PCs, quantis ou memberships.
   Seu hash coincide com a proveniência corrected-only já existente.
4. O frozen source `3dc622ed0efb03cdf5ef0bf9a4a78a57ceef365d` tem cadeias
   distintas para `eof_analysis_with_track_id.py` (loadings/PCs) e
   `attribute_track_ids_to_eof_extremes.py` (membership); a primeira não é a
   média física da segunda. Os hashes das duas fontes Git estão em `provenance.json`.
5. Corrected-only: `generate_corrected_article.py:602`, `render_syntheses`, usa
   `eof_loadings_by_phase_raw.csv`/raw phase loadings (A). Comparison:
   `generate_article_comparison.py:254`, `fig16`, seleciona EOF(+) de PCs totais,
   calcula média de períodos por ciclone e depois média entre ciclones, e plota
   um único LEC por versão, sem separar as quatro fases (também não implementa
   integralmente a definição B do caption).

**São o mesmo objeto científico? NÃO.** A comparison atual é
**INVALID_AS_REPLACEMENT** tanto para o artefato de loadings sugerido pelo script
quanto para a síntese por fase pedida pelo caption. O corrected-only se aproxima
do objeto A, mas raw ranks não asseguram identidade dos EOFs corrigidos e A
contradiz a definição textual. **Nenhum está autorizado como substituto direto.**

Decisão necessária: o autor deve confirmar a definição científica da Figure 16
(assumindo explicitamente uma correção de caption ou de figura, se necessário) e
se a reprodução fiel do artefato ou do texto é a finalidade. Não foi gerada uma
terceira figura para tentar resolver a intenção.

Foi adicionado `scripts/article_figures/downstream_guards.py`. Os dois geradores
atuais e o gerador paired falham no início, antes de ler entradas/criar saídas, e
os três entry points de Figure 16 também falham quando chamados diretamente.
O comando dedicado `regenerate_phase_eofs.py` e os produtos das Figures 5–8
permanecem inalterados. A mensagem aponta o relatório e solicita revisão de
definição; não há flag para ignorar silenciosamente o conflito.
