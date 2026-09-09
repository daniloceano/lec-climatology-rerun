from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from scripts.lec_climatology_rerun.common import RunConfig, StateDB
from scripts.lec_climatology_rerun.validate_run import audit


def test_quick_audit_matches_manifest_state_and_result_directory(tmp_path: Path):
    config = RunConfig(
        run_root=str(tmp_path),
        paper_repo=str(tmp_path),
        toolkit_source=str(tmp_path / "source"),
        toolkit_worktree=str(tmp_path / "worktree"),
        keys_file=str(tmp_path / "keys"),
    )
    config.save()
    pd.DataFrame([{"track_id": "1"}]).to_csv(config.manifest, index=False)
    (tmp_path / "provenance.json").write_text(
        json.dumps({"population": {"selected_cyclones": 1, "sha256": "test"}})
    )
    (config.results_dir / "1_ERA5_track").mkdir()
    database = StateDB(config.db)
    database.add_cyclones(
        [{"track_id": "1", "n_timesteps": 2, "lifecycle_hours": 3}], set()
    )
    database.transition("1", "COMPLETE")
    database.close()

    result = audit(tmp_path, quick=True)
    assert result["states"] == {"COMPLETE": 1}
    assert result["deep_outputs_validated"] == 0
    assert result["validation_errors"] == []
