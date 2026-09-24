# Documentation

## Canonical article comparison

| Artifact | Purpose |
|---|---|
| `lec_climatology_article_before_after_report.pdf` | Shareable final report: full archived article population versus validated corrected rerun |
| `lec_climatology_article_before_after_report.md` | Markdown source with links to every paper figure |

The canonical comparison uses 6,789 legacy cyclones and 3,820 corrected
cyclones. Its differences combine the toolkit correction and population
change.

## Paired control

`paired_control/` contains the correction-only diagnostic report. Both sides
use the same 3,820 cyclones, so it is scientifically useful but must not be
presented as the literal article-population comparison.

## Technical records

`technical/` contains the production audit and the migration record from
`paper_energy_patterns`. These are provenance documents, not current result
reports.

The removed `lec_climatology_corrected_figures_report` represented an earlier
paired figure workflow and is retained only in Git history to prevent it from
being mistaken for the article comparison.
