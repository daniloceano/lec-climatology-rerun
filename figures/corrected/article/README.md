# Corrected article figures

The 16 PNG/PDF pairs reproduce the layout of the final article figures with
the validated corrected 3,820-cyclone rerun. Figures 3–16 were recalculated;
Figures 1 and 2 are byte-identical to the publication because the track
reference and conceptual LEC diagram do not depend on corrected LEC values.

Every corrected PNG has the same pixel dimensions and panel composition as its
counterpart under `figures/original/article/`. Hashes, numerical tables and
generation provenance are stored under
`results/corrected/article/reproduction/`.

Regenerate with:

```bash
python scripts/sync_swell_inputs.py
python scripts/article_figures/generate_corrected_article.py
```
