# Scripts

| Directory | Responsibility | Main entry point |
|---|---|---|
| `lec_climatology_rerun/` | Prepare, execute and validate the corrected server-side rerun | `pipeline.py`, `validate_run.py` |
| `article_figures/` | Produce the validated article results and figures | `reproduce_downstream.py` |
| `lec_rerun_comparison/` | Build the fixed-population paired control | `run_all.py` |
| `utils/` | Shared corrected-output readers and vertical conventions | imported modules |

Run article commands from the repository root. Sync and verify pinned external inputs with `python scripts/sync_swell_inputs.py`, then use the workflow in [article_figures/README.md](article_figures/README.md). The archived manuscript data and production rerun remain external to Git.
