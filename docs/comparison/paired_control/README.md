# Paired control

This directory contains the correction-only control report:

- `lec_rerun_paired_control_report.pdf` - shareable PDF;
- `lec_rerun_paired_control_report.md` - generated Markdown source.

Legacy and corrected values are paired on the same 3,820 cyclones and matched
lifecycle periods. Use this report to attribute changes to the
LorenzCycleToolKit correction while holding population fixed.

Do not use it as the main article comparison. The canonical report in the
parent `docs/` directory compares all 6,789 archived article cyclones with the
3,820 corrected reruns.

Regenerate with `scripts/lec_rerun_comparison/run_all.py`.
