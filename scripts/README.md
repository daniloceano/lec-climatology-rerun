# Scripts

| Directory | Responsibility | Main entry point |
|---|---|---|
| `lec_climatology_rerun/` | Prepare, execute, monitor and validate the corrected server-side rerun | `pipeline.py` and `validate_run.py` |
| `article_figures/` | Produce the canonical article before/after figures and report | `generate_article_comparison.py` |
| `lec_rerun_comparison/` | Build the fixed-population paired control | `run_all.py` |
| `utils/` | Shared corrected-output readers and vertical conventions | imported modules |

Run commands from the repository root so local imports and output paths resolve
consistently. Input data must be supplied explicitly; scripts must not embed
credentials or modify archived legacy products.

The article workflow owns `figures/paper/`, `results/article_comparison/` and
the canonical report in `docs/`. The paired workflow owns only the three
`paired_control/` destinations.
