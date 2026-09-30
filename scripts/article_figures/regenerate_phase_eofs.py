#!/usr/bin/env python3
"""Regenerate only article Figures 5–8 and their matched phase EOF products."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.article_figures.common import PHASES, sha256_file, write_json
from scripts.article_figures.generate_comparison import fig_eof
from scripts.article_figures.generate_corrected_article import (
    DEFAULT_CONFIG, REPOSITORY, read_config, render_eof_diagrams,
    resolve_repo_path, validate_layout,
)
from scripts.article_figures.phase_eofs import (
    PRODUCT_DIRECTORY, compatibility_tables, load_pinned_phase_inputs,
    matched_phase_eofs, read_phase_product, write_phase_product,
)


def regenerate(config_path: Path = DEFAULT_CONFIG) -> None:
    root = REPOSITORY
    config = read_config(config_path)
    comparison = root / "results/comparison/article"
    reproduction = resolve_repo_path(config["article"]["corrected_results_root"])
    figures = resolve_repo_path(config["article"]["corrected_figure_root"])
    originals = resolve_repo_path(config["article"]["published_figure_root"])
    legacy_root = resolve_repo_path(config["article"]["legacy_source_root"])
    product = root / PRODUCT_DIRECTORY
    corrected_path = resolve_repo_path(config["inputs"]["corrected_cache"]["local"])
    legacy, corrected, sources = load_pinned_phase_inputs(root, corrected_path)
    provenance = json.loads((reproduction / "provenance.json").read_text())
    for filename in ("plot_LEC_eofs.py",):
        if sha256_file(legacy_root / filename) != provenance["legacy_source_hashes"][filename]:
            raise ValueError(f"frozen renderer hash mismatch: {filename}")

    loadings, variance, scores = matched_phase_eofs(legacy, corrected)
    # Existing comparison numbers are independently audited and must not move.
    old_loadings, old_variance = compatibility_tables(loadings, variance)
    for frame, name, tolerance in (
        (old_loadings, "eof_loadings_by_phase.csv", 5e-8),
        (old_variance, "eof_variance_by_phase.csv", 5e-7),
    ):
        expected = pd.read_csv(comparison / name)
        pd.testing.assert_frame_equal(frame, expected, check_dtype=False, atol=tolerance, rtol=0)

    comparison_manifest = pd.read_csv(comparison / "figure_manifest.csv", keep_default_na=False)
    corrected_manifest = pd.read_csv(reproduction / "figure_manifest.csv", keep_default_na=False)
    selected = comparison_manifest.figure_label.astype(str).isin(["5", "6", "7", "8"])
    updated_paths = {
        comparison / "figure_manifest.csv", reproduction / "figure_manifest.csv",
        reproduction / "provenance.json",
        *[reproduction / f"eof_{kind}_by_phase.csv" for kind in ("loadings", "variance", "scores")],
        reproduction / "eof_loadings_by_phase_raw.csv",
        reproduction / "eof_variance_by_phase_raw.csv",
    }
    for manifest, mask in ((comparison_manifest, selected), (corrected_manifest, corrected_manifest.figure.isin(range(5, 9)))):
        for row in manifest[mask].itertuples():
            updated_paths.update([root / row.png, root / row.pdf])
    frozen = {
        str(path.relative_to(root)): sha256_file(path)
        for folder in ("figures", "results", "tables")
        for path in (root / folder).rglob("*")
        if path.is_file() and path.suffix in {".csv", ".json", ".png", ".pdf", ".tex"}
        and path not in updated_paths and product not in path.parents
    }

    write_phase_product(root, loadings, variance)
    loadings, variance = read_phase_product(root)
    after_loadings = loadings[loadings.version.eq("after")].copy()
    after_variance = variance[variance.version.eq("after")].copy()
    after_loadings.to_csv(reproduction / "eof_loadings_by_phase.csv", index=False, float_format="%.8g")
    after_variance.to_csv(reproduction / "eof_variance_by_phase.csv", index=False, float_format="%.8g")
    scores.to_csv(reproduction / "eof_scores_by_phase.csv", index=False, float_format="%.8g")
    # Explicit raw snapshots document the frozen Figure 16 input convention.
    raw_loadings = after_loadings.assign(loading=after_loadings.loading * after_loadings.sign_alignment)
    raw_loadings = raw_loadings[["scope", "raw_rank", "term", "loading"]]
    raw_variance = after_variance[["scope", "raw_rank", "n", "explained_variance_pct"]]
    raw_loadings.to_csv(reproduction / "eof_loadings_by_phase_raw.csv", index=False, float_format="%.8g")
    raw_variance.to_csv(reproduction / "eof_variance_by_phase_raw.csv", index=False, float_format="%.8g")

    (root / "tmp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="phase-eofs-", dir=root / "tmp") as scratch:
        render_eof_diagrams(legacy_root, after_loadings, after_variance, figures, Path(scratch))
    corrected_rows = validate_layout(figures, originals, numbers=range(5, 9))
    for record in corrected_rows:
        index = corrected_manifest.index[corrected_manifest.figure.eq(record["figure"])].item()
        for key, value in record.items():
            corrected_manifest.loc[index, key] = value
    for index, row in comparison_manifest[selected].iterrows():
        mode = int(row.figure_label) - 4
        fig_eof(mode, loadings, variance, (root / row.png).with_suffix(""))
        for extension in ("png", "pdf"):
            comparison_manifest.loc[index, extension + "_sha256"] = sha256_file(root / row[extension])
        comparison_manifest.loc[index, "caption"] = (
            f"Published/reference EOF {mode}: independently fitted within each phase; "
            "corrected modes matched one-to-one across eight modes and sign-aligned. "
            "Corrected raw ranks and variance are recorded in phase_eof_matched/variance.csv."
        )
    for manifest, mask, directory in (
        (comparison_manifest, selected, comparison),
        (corrected_manifest, corrected_manifest.figure.isin(range(5, 9)), reproduction),
    ):
        manifest.loc[mask, "phase_eof_product"] = str(PRODUCT_DIRECTORY)
        manifest.loc[mask, "eof_identity"] = "reference_eof; raw_rank and sign_alignment in canonical variance.csv"
        manifest.to_csv(directory / "figure_manifest.csv", index=False)

    provenance["phase_eofs"] = {
        "figures": [5, 6, 7, 8], "source": str(PRODUCT_DIRECTORY),
        "identity": "reference_eof", "raw_rank": "corrected eigenvalue rank before matching",
        "scores": "reference_PC1–reference_PC8; jointly permuted and sign-aligned",
    }
    provenance["figure_16_phase_eofs"] = {
        "status": "frozen; not regenerated by the phase matching correction",
        "input": "eof_loadings_by_phase_raw.csv", "identity": "raw_rank",
    }
    write_json(reproduction / "provenance.json", provenance)

    consistency = []
    existing = pd.read_csv(comparison / "eof_loadings_by_phase.csv")
    existing_variance = pd.read_csv(comparison / "eof_variance_by_phase.csv")
    for phase in PHASES:
        for mode in range(1, 5):
            right = after_loadings.query("scope == @phase and reference_eof == @mode").set_index("term").loading
            # Compare serialized compatibility values, not display rounding.
            left = existing.query("scope == @phase and eof == @mode and version == 'after'").set_index("term").loading
            pd.testing.assert_series_equal(left, right, check_exact=True)
            ev = after_variance.query("scope == @phase and reference_eof == @mode").iloc[0]
            before_ev = existing_variance.query("scope == @phase and eof == @mode and version == 'after'").explained_variance_pct.item()
            assert before_ev == ev.explained_variance_pct
            consistency.append({"scope": phase, "reference_eof": mode, "corrected_raw_rank": int(ev.raw_rank),
                                "max_abs_loading_difference": 0.0, "explained_variance_difference_pct": 0.0})
    pd.DataFrame(consistency).to_csv(product / "consistency.csv", index=False)
    for relative, digest in frozen.items():
        if sha256_file(root / relative) != digest:
            raise ValueError(f"unrelated output changed: {relative}")
    write_json(product / "frozen_outputs.json", frozen)
    output_paths = [*updated_paths, product / "loadings.csv", product / "variance.csv", product / "consistency.csv", product / "frozen_outputs.json"]
    write_json(product / "provenance.json", {
        "method": "independent_eof_by_phase / align_eofs; separate eight-mode assignment per phase",
        "sources": sources, "reference_identity": "reference_eof", "raw_identity": "raw_rank",
        "source_code_sha256": {
            str(path.relative_to(root)): sha256_file(path)
            for path in [Path(__file__), *[
                root / "scripts/article_figures" / name for name in (
                    "common.py", "phase_eofs.py", "generate_comparison.py",
                    "generate_corrected_article.py", "generate_article_comparison.py",
                )
            ]]
        },
        "sign_alignment": "multiplier applied jointly to raw loadings and PCs",
        "csv_precision": "8 significant digits, matching existing article tables",
        "corrected_phase_scores": str((reproduction / "eof_scores_by_phase.csv").relative_to(root)),
        "frozen_output_count": len(frozen),
        "outputs": {str(path.relative_to(root)): sha256_file(path) for path in sorted(output_paths)},
    })
    print(f"Regenerated Figures 5–8 in both workflows; 16/16 panels match; {len(frozen)} unrelated files unchanged.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    regenerate(parser.parse_args().config)


if __name__ == "__main__":
    main()
