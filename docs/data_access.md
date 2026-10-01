# Authoritative swell inputs

The machine-readable source of truth is
[`config/data_sources.toml`](../config/data_sources.toml). It records the SSH
alias, remote files, ignored local mirror, expected sizes and SHA-256 hashes.

## Access

1. Use the existing SSH alias `swell`.
2. The corrected production root is
   `/p1-swell/danilocs/lec_climatology_corrected_v2`.
3. The article data root is
   `/p1-swell/danilocs/paper_energy_patterns`.
4. If public-key/agent authentication is unavailable and `sshpass` is already
   installed, the fallback password file is `~/Documents/Mastr/senha.txt`.

The password file is external to this repository. Its contents must never be
printed, copied, committed, included in logs, or written to provenance. The
sync helper passes its path directly to `sshpass -f`; it does not read the
password itself. It does not install software or change SSH configuration.

## Local mirror

Run from the repository root:

```bash
python scripts/sync_swell_inputs.py
python scripts/sync_swell_inputs.py --check
```

The verified files are stored below
`data/external/swell/paper_energy_patterns/`, which is ignored by Git. A
download is accepted only if both byte size and SHA-256 match the pinned
values. Missing or mismatched inputs stop the workflow immediately.

The final article-style corrected figures and table can then be regenerated
with:

```bash
python -m scripts.article_figures.reproduce_downstream
python -m scripts.article_figures.build_article_results
python -m scripts.article_figures.build_validated_comparison
python -m scripts.article_figures.generate_corrected_article_table
```
