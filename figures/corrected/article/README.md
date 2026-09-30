# Corrected article figures

Figures 9–16 in this directory are the validated correction candidates. They
reproduce the archived article scripts with corrected LEC/EOF results, published
EOF identity matching, `pyEOF.pcs(s=2)` scaling, and four intense-cyclone clusters.
The legacy reproduction gate must pass before regeneration.

Figures 5–8 and their canonical matched phase EOF inputs remain frozen. Figures
1–4 remain as previously generated. Numerical products, the legacy gate and
provenance are in `results/corrected/article/validated_downstream/` and
`results/original/article/reproduction_gate/`. Before/after image diagnostics
are in `figures/comparison/article/`.

Regenerate Figures 9–16 with:

```bash
python -m scripts.article_figures.reproduce_downstream
python -m scripts.article_figures.build_validated_comparison
```

See `docs/technical/downstream_reproduction.md` for the scientific validation
and `results/corrected/article/validated_downstream/provenance.json` for hashes.
