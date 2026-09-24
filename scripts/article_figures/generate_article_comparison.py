#!/usr/bin/env python3
"""Compare the full published legacy climatology with the corrected rerun."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.article_figures.common import (  # noqa: E402
    EOF_TERMS,
    PHASES,
    assign_published_eof_extremes,
    first_track_rows,
    independent_eof_by_phase,
    independent_intense_pc_clusters,
    independent_total_eof,
    load_article_comparison_inputs,
    phase_statistics,
    primary_phase_rows,
    sha256_file,
    write_json,
)
from scripts.article_figures.generate import (  # noqa: E402
    add_region_boxes,
    cluster_summary,
    fig01,
    fig02,
    figure_stem,
)
from scripts.article_figures.generate_comparison import (  # noqa: E402
    _density_panels,
    _group_values,
    fig03,
    fig04,
    fig11,
    fig15,
    fig_eof,
    fig_eof_density,
)
from scripts.article_figures.plotting import (  # noqa: E402
    AFTER_COLOR,
    BEFORE_COLOR,
    comparison_legend_handles,
    draw_cycle,
    draw_cycle_comparison,
    map_axis,
    plot_density,
    save_pair,
)

FIGURES_NAME = "paper"
RESULTS_NAME = "article_comparison"

FIGURE_CAPTIONS = {
    "1": "Track density and the three genesis regions; this track-only reference is common to both datasets.",
    "2": "Reference four-box Lorenz Energy Cycle diagram; this conceptual panel is common to both datasets.",
    "3": "LEC term distributions from the full published legacy archive (upper half) and corrected rerun (lower half).",
    "4": "Primary-phase mean LEC. Dark arrows and values show the published legacy population; red shows the corrected population.",
    "5": "EOF 1 LEC loadings fitted independently to the published and corrected populations, then pattern-matched and sign-aligned.",
    "6": "EOF 2 LEC loadings fitted independently to the published and corrected populations, then pattern-matched and sign-aligned.",
    "7": "EOF 3 LEC loadings fitted independently to the published and corrected populations, then pattern-matched and sign-aligned.",
    "8": "EOF 4 LEC loadings fitted independently to the published and corrected populations, then pattern-matched and sign-aligned.",
    "9": "Positive total-lifecycle PC-extreme track densities: published population above and corrected population below.",
    "10": "Negative total-lifecycle PC-extreme track densities: published population above and corrected population below.",
    "11": "Genesis-region and seasonal composition of total-lifecycle PC extremes, published above and corrected below.",
    "12a": "Mean LEC of all intense cyclones in the published and corrected populations.",
    "12b": "Five intense-cyclone groups obtained from the first eight total-lifecycle PCs; corrected groups are centroid-matched to published groups.",
    "13": "Track densities of the five intense-cyclone PC groups, published above and corrected below.",
    "14": "Counts, maximum intensity, seasonality and genesis regions for the five intense-cyclone PC groups.",
    "15": "Primary-phase LEC synthesis, with the published population on the left and corrected population on the right.",
    "16a": "Mean LEC of cyclones assigned to the positive EOF 1 extreme, published on the left and corrected on the right.",
    "16b": "Mean LEC of cyclones assigned to the positive EOF 2 extreme, published on the left and corrected on the right.",
    "16c": "Mean LEC of cyclones assigned to the positive EOF 3 extreme, published on the left and corrected on the right.",
    "16d": "Mean LEC of cyclones assigned to the positive EOF 4 extreme, published on the left and corrected on the right.",
}


def git_head(project: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(project), "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def fig12(
    legacy: pd.DataFrame,
    corrected: pd.DataFrame,
    assignments: pd.DataFrame,
    all_intense_stem: Path,
    clusters_stem: Path,
) -> None:
    before = assignments[assignments["version"] == "before"]
    after = assignments[assignments["version"] == "after"]
    before_ids = set(before["track_id"].astype(int))
    after_ids = set(after["track_id"].astype(int))
    before_mean, before_std = _group_values(legacy, before_ids)
    after_mean, after_std = _group_values(corrected, after_ids)

    figure, ax = plt.subplots(figsize=(6.2, 6.4))
    draw_cycle_comparison(
        ax,
        before_mean,
        after_mean,
        before_uncertainty=before_std,
        after_uncertainty=after_std,
        title=f"All intense\nn {len(before_ids)} -> {len(after_ids)}",
        title_fontsize=9.4,
    )
    figure.legend(handles=comparison_legend_handles(), loc="lower center", ncol=2, frameon=False, fontsize=9)
    figure.suptitle("All intense cyclones: published versus corrected", fontsize=14, fontweight="bold")
    figure.subplots_adjust(left=0.04, right=0.96, bottom=0.12, top=0.90)
    save_pair(figure, all_intense_stem)

    figure, axes = plt.subplots(2, 3, figsize=(11.2, 7.8), gridspec_kw={"wspace": -0.08})
    for ax, cluster, tag in zip(axes.flat, range(1, 6), "ABCDE"):
        old_ids = set(before.loc[before["cluster"] == cluster, "track_id"].astype(int))
        new_ids = set(after.loc[after["cluster"] == cluster, "track_id"].astype(int))
        old_mean, old_std = _group_values(legacy, old_ids)
        new_mean, new_std = _group_values(corrected, new_ids)
        draw_cycle_comparison(
            ax,
            old_mean,
            new_mean,
            before_uncertainty=old_std,
            after_uncertainty=new_std,
            title=f"({tag}) Cluster {cluster}\nn {len(old_ids)} -> {len(new_ids)}",
        )
    axes.flat[-1].axis("off")
    figure.legend(handles=comparison_legend_handles(), loc="lower center", ncol=2, frameon=False, fontsize=9)
    figure.suptitle("Five intense-cyclone PC groups: published versus corrected", fontsize=14, fontweight="bold")
    figure.subplots_adjust(left=0.025, right=0.975, bottom=0.075, top=0.91, wspace=-0.08, hspace=0.10)
    save_pair(figure, clusters_stem)


def fig13(tracks: pd.DataFrame, assignments: pd.DataFrame, stem: Path) -> None:
    items = []
    for version in ("before", "after"):
        for cluster in range(1, 6):
            ids = set(
                assignments.loc[
                    (assignments["version"] == version) & (assignments["cluster"] == cluster),
                    "track_id",
                ].astype(int)
            )
            items.append((version, cluster, ids))
    blocks, levels = _density_panels(items, tracks, lon_bounds=(-80, 100))
    figure = plt.figure(figsize=(15.0, 5.0))
    contours = []
    for index, (version, cluster, ids, lon, lat, density) in enumerate(blocks):
        ax = map_axis(figure, (2, 5, index + 1), extent=(-80, 100, -85, -15))
        prefix = "Before" if version == "before" else "After"
        contours.append(
            plot_density(
                ax,
                lon,
                lat,
                density,
                title=f"{prefix}: cluster {cluster} (n={len(ids)})",
                levels=levels,
            )
        )
        add_region_boxes(ax, show_labels=False)
    figure.suptitle("Track density of five intense-cyclone PC groups", fontsize=13, fontweight="bold")
    figure.subplots_adjust(left=0.025, right=0.985, bottom=0.20, top=0.86, wspace=0.07, hspace=0.10)
    colorbar = figure.colorbar(contours[-1], ax=figure.axes, orientation="horizontal", pad=0.055, fraction=0.045)
    colorbar.set_label("Smoothed track points per month", fontsize=8)
    colorbar.ax.tick_params(labelsize=7, pad=2)
    save_pair(figure, stem)


def _cluster_row(axes, label: str, assignments: pd.DataFrame, tracks: pd.DataFrame, first: pd.DataFrame):
    maximum = tracks.groupby("track_id")["vor42"].max().rename("max_vor42")
    merged = assignments.merge(first[["track_id", "region", "season"]], on="track_id", how="left")
    merged = merged.merge(maximum, on="track_id", how="left")
    summary = cluster_summary(assignments, tracks, first)
    clusters = np.arange(1, 6)
    colors = plt.get_cmap("Set2").colors[:5]
    axes[0].bar(clusters, summary.set_index("cluster").loc[clusters, "n"], color=colors)
    axes[0].set_title(f"{label}: system count", fontsize=9, fontweight="bold", loc="left")
    data = [merged.loc[merged["cluster"] == cluster, "max_vor42"].dropna() for cluster in clusters]
    box = axes[1].boxplot(data, patch_artist=True, tick_labels=clusters, showfliers=True,
                          flierprops=dict(markersize=2, markerfacecolor="none"))
    for patch, color in zip(box["boxes"], colors):
        patch.set_facecolor(color)
    axes[1].set_title(f"{label}: maximum intensity", fontsize=9, fontweight="bold", loc="left")
    seasons = ["DJF", "MAM", "JJA", "SON"]
    regions = ["ARG", "LA-PLATA", "SE-BR"]
    for axis, values, categories, title in (
        (
            axes[2],
            summary.set_index("cluster")[[f"season_{value}_pct" for value in seasons]].loc[clusters].to_numpy(),
            seasons,
            f"{label}: seasonality",
        ),
        (
            axes[3],
            summary.set_index("cluster")[[f"region_{value}_pct" for value in regions]].loc[clusters].to_numpy(),
            regions,
            f"{label}: genesis regions",
        ),
    ):
        width = 0.8 / len(categories)
        for index, category in enumerate(categories):
            axis.bar(
                clusters - 0.4 + width / 2 + index * width,
                values[:, index],
                width,
                label=category,
                color=plt.get_cmap("Set2").colors[index],
            )
        axis.set_ylabel("Occurrence (%)", fontsize=7)
        axis.set_title(title, fontsize=9, fontweight="bold", loc="left")
        axis.legend(fontsize=5.8, frameon=False, ncol=2)
    for ax in axes:
        ax.set_xticks(clusters)
        ax.set_xlabel("Matched cluster", fontsize=7)
        ax.tick_params(labelsize=6.5)
        ax.grid(axis="y", alpha=0.2)
    return summary


def fig14(assignments: pd.DataFrame, tracks: pd.DataFrame, first: pd.DataFrame, stem: Path) -> pd.DataFrame:
    figure, axes = plt.subplots(2, 4, figsize=(13.0, 6.2))
    before = assignments[assignments["version"] == "before"].drop(columns="version")
    after = assignments[assignments["version"] == "after"].drop(columns="version")
    before_summary = _cluster_row(axes[0], "Before", before, tracks, first)
    after_summary = _cluster_row(axes[1], "After", after, tracks, first)
    before_summary.insert(0, "version", "before")
    after_summary.insert(0, "version", "after")
    figure.suptitle("Five intense-cyclone PC groups: published versus corrected", fontsize=13, fontweight="bold")
    figure.subplots_adjust(left=0.055, right=0.985, bottom=0.08, top=0.90, wspace=0.28, hspace=0.27)
    save_pair(figure, stem)
    return pd.concat([before_summary, after_summary], ignore_index=True)


def fig16(
    mode: int,
    legacy: pd.DataFrame,
    corrected: pd.DataFrame,
    assignments: pd.DataFrame,
    stem: Path,
) -> None:
    before_ids = set(
        assignments.loc[
            (assignments["version"] == "before")
            & (assignments["sign"] == "positive")
            & (assignments["dominant_eof"] == mode),
            "track_id",
        ].astype(int)
    )
    after_ids = set(
        assignments.loc[
            (assignments["version"] == "after")
            & (assignments["sign"] == "positive")
            & (assignments["dominant_eof"] == mode),
            "track_id",
        ].astype(int)
    )
    before_mean, before_std = _group_values(legacy, before_ids)
    after_mean, after_std = _group_values(corrected, after_ids)
    figure, axes = plt.subplots(1, 2, figsize=(10.8, 6.2), gridspec_kw={"wspace": -0.14})
    draw_cycle(
        axes[0], before_mean, uncertainty=before_std,
        title=f"Before - published\nn={len(before_ids)}", color=BEFORE_COLOR,
    )
    draw_cycle(
        axes[1], after_mean, uncertainty=after_std,
        title=f"After - corrected\nn={len(after_ids)}", color=AFTER_COLOR,
    )
    figure.suptitle(f"Mean LEC of positive EOF {mode} cyclones", fontsize=14, fontweight="bold")
    figure.subplots_adjust(left=0.025, right=0.975, bottom=0.06, top=0.90, wspace=-0.14)
    save_pair(figure, stem)


def write_report_markdown(path: Path, manifest: pd.DataFrame, provenance: dict, cluster_meta: dict) -> None:
    lines = [
        "# LEC climatology: published article versus corrected rerun",
        "",
        "This report separates the literal article comparison from the controlled paired sensitivity analysis. The before side uses the complete archived population and published analysis definition; the after side applies the same definitions to the validated corrected rerun.",
        "",
        "## Interpretation boundary",
        "",
        "- Before: **6,789 legacy cyclones and 25,000 archived lifecycle rows**.",
        "- After: **3,820 corrected cyclones and 15,829 archived lifecycle rows**.",
        "- Differences therefore combine the toolkit correction and the population change. They must not be interpreted as a purely paired correction effect.",
        "- The existing paired 3,820-cyclone report remains the controlled sensitivity analysis and is not overwritten.",
        "",
        "## Reproduction audit",
        "",
        f"- Published total EOF 1-4 variance reproduced from the legacy cache: **{', '.join(f'{value:.3f}%' for value in provenance['legacy_total_eof_variance_pct'][:4])}**.",
        f"- Primary legacy rows: **{provenance['legacy_primary_rows']:,}**; primary corrected rows: **{provenance['corrected_primary_rows']:,}**.",
        f"- Intense systems entering clustering: **{cluster_meta['eligible_legacy_cyclones']:,} before** and **{cluster_meta['eligible_corrected_cyclones']:,} after**.",
        "- Five K-means groups are fitted to the first eight total-lifecycle PC scores and corrected groups are matched to legacy centroids.",
        "- Figure 16 shows mean LECs of cyclones assigned to the positive EOF groups, not EOF loading diagrams.",
        "",
        "## Figures",
        "",
    ]
    for row in manifest.itertuples():
        relative = Path("..") / row.png
        lines.extend(
            [
                f"### Figure {row.figure_label}",
                "",
                f"![Figure {row.figure_label}]({relative.as_posix()})",
                "",
                f"*{row.caption}*",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-cache", type=Path, required=True)
    parser.add_argument("--corrected-cache", type=Path, required=True)
    parser.add_argument("--tracks", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--resume-after-13",
        action="store_true",
        help="reuse already generated Figures 1-13 after validating their files",
    )
    args = parser.parse_args()

    root = args.output_root.resolve()
    figures_dir = root / "figures" / FIGURES_NAME
    results_dir = root / "results" / RESULTS_NAME
    docs_dir = root / "docs"
    figures_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    legacy, corrected, tracks = load_article_comparison_inputs(
        args.legacy_cache, args.corrected_cache, args.tracks
    )
    legacy_primary = primary_phase_rows(legacy)
    corrected_primary = primary_phase_rows(corrected)
    stats = pd.concat(
        [
            phase_statistics(legacy_primary).assign(version="before"),
            phase_statistics(corrected_primary).assign(version="after"),
        ],
        ignore_index=True,
    )
    phase_loadings, phase_variance = independent_eof_by_phase(legacy_primary, corrected_primary)
    total_loadings, total_variance, total_scores = independent_total_eof(legacy, corrected)

    extreme_parts = []
    for version in ("before", "after"):
        scores = total_scores[total_scores["version"] == version].drop(columns="version")
        part = assign_published_eof_extremes(scores)
        part.insert(1, "version", version)
        extreme_parts.append(part)
    eof_assignments = pd.concat(extreme_parts, ignore_index=True)

    before_clusters, after_clusters, before_centers, after_centers, cluster_meta = (
        independent_intense_pc_clusters(total_scores, tracks, k=5, n_pcs=8)
    )
    cluster_assignments = pd.concat([before_clusters, after_clusters], ignore_index=True)
    first = first_track_rows(tracks)

    if args.resume_after_13:
        expected_partial = [
            *[sorted(figures_dir.glob(f"fig_{number:02d}_*.{suffix}")) for number in range(1, 12) for suffix in ("png", "pdf")],
            *[
                [figures_dir / f"fig_12{part}_{name}.{suffix}"]
                for part, name in (
                    ("a", "all_intense_lec_published_corrected"),
                    ("b", "five_intense_clusters_lec_published_corrected"),
                )
                for suffix in ("png", "pdf")
            ],
            *[sorted(figures_dir.glob(f"fig_13_*.{suffix}")) for suffix in ("png", "pdf")],
        ]
        missing = [str(paths[0]) if paths else "missing glob" for paths in expected_partial if len(paths) != 1 or not paths[0].is_file()]
        if missing:
            raise FileNotFoundError(f"cannot resume; incomplete Figures 1-13: {missing}")
    else:
        fig01(tracks, figure_stem(figures_dir, 1, "track_density"))
        fig02(figure_stem(figures_dir, 2, "lec_reference"))
        fig03(legacy, corrected, figure_stem(figures_dir, 3, "term_pdfs_published_corrected"))
        fig04(stats, figure_stem(figures_dir, 4, "phase_mean_lec_published_corrected"))
        for mode in range(1, 5):
            fig_eof(
                mode,
                phase_loadings,
                phase_variance,
                figure_stem(figures_dir, mode + 4, f"eof{mode}_lec_published_corrected"),
            )
        fig_eof_density("positive", eof_assignments, tracks, figure_stem(figures_dir, 9, "eof_positive_density_published_corrected"))
        fig_eof_density("negative", eof_assignments, tracks, figure_stem(figures_dir, 10, "eof_negative_density_published_corrected"))
        fig11(eof_assignments, first, figure_stem(figures_dir, 11, "eof_genesis_season_published_corrected"))
        fig12(
            legacy,
            corrected,
            cluster_assignments,
            figures_dir / "fig_12a_all_intense_lec_published_corrected",
            figures_dir / "fig_12b_five_intense_clusters_lec_published_corrected",
        )
        fig13(tracks, cluster_assignments, figure_stem(figures_dir, 13, "five_intense_groups_density_published_corrected"))
    cluster_stats = fig14(
        cluster_assignments,
        tracks,
        first,
        figure_stem(figures_dir, 14, "five_intense_groups_characteristics_published_corrected"),
    )
    fig15(stats, figure_stem(figures_dir, 15, "phase_synthesis_published_corrected"))
    for mode, suffix in zip(range(1, 5), "abcd"):
        fig16(
            mode,
            legacy,
            corrected,
            eof_assignments,
            figures_dir / f"fig_16{suffix}_eof{mode}_positive_group_lec_published_corrected",
        )

    stats.to_csv(results_dir / "phase_statistics.csv", index=False, float_format="%.8g")
    phase_loadings.to_csv(results_dir / "eof_loadings_by_phase.csv", index=False, float_format="%.8g")
    phase_variance.to_csv(results_dir / "eof_variance_by_phase.csv", index=False, float_format="%.8g")
    total_loadings.to_csv(results_dir / "eof_loadings_total.csv", index=False, float_format="%.8g")
    total_variance.to_csv(results_dir / "eof_variance_total.csv", index=False, float_format="%.8g")
    total_scores.to_csv(results_dir / "eof_scores_total.csv", index=False, float_format="%.8g")
    eof_assignments.to_csv(results_dir / "eof_extreme_assignments.csv", index=False, float_format="%.8g")
    cluster_assignments.to_csv(results_dir / "intense_pc_cluster_assignments.csv", index=False)
    center_columns = [f"PC{i}" for i in range(1, 9)]
    centers = pd.concat(
        [
            pd.DataFrame(before_centers, columns=center_columns).assign(version="before", cluster=np.arange(1, 6)),
            pd.DataFrame(after_centers, columns=center_columns).assign(version="after", cluster=np.arange(1, 6)),
        ],
        ignore_index=True,
    )
    centers.to_csv(results_dir / "intense_pc_cluster_centers.csv", index=False, float_format="%.8g")
    cluster_stats.to_csv(results_dir / "intense_pc_cluster_statistics.csv", index=False, float_format="%.8g")
    write_json(results_dir / "intense_pc_cluster_metadata.json", cluster_meta)

    figure_specs = []
    for number in range(1, 16):
        if number == 12:
            figure_specs.extend(
                [
                    ("12a", figures_dir / "fig_12a_all_intense_lec_published_corrected.png"),
                    ("12b", figures_dir / "fig_12b_five_intense_clusters_lec_published_corrected.png"),
                ]
            )
        else:
            figure_specs.append((str(number), sorted(figures_dir.glob(f"fig_{number:02d}_*.png"))[-1]))
    figure_specs.extend(
        [
            (f"16{suffix}", figures_dir / f"fig_16{suffix}_eof{mode}_positive_group_lec_published_corrected.png")
            for mode, suffix in zip(range(1, 5), "abcd")
        ]
    )
    manifest_rows = []
    for label, png in figure_specs:
        pdf = png.with_suffix(".pdf")
        manifest_rows.append(
            {
                "figure_label": label,
                "caption": FIGURE_CAPTIONS[label],
                "png": str(png.relative_to(root)),
                "pdf": str(pdf.relative_to(root)),
                "png_sha256": sha256_file(png),
                "pdf_sha256": sha256_file(pdf),
            }
        )
    manifest = pd.DataFrame(manifest_rows)
    manifest.to_csv(results_dir / "figure_manifest.csv", index=False)

    legacy_variance = total_variance[total_variance["version"] == "before"].sort_values("eof")
    provenance = {
        "workflow": "literal published-population versus corrected-population comparison of article Figures 1-16",
        "interpretation": "unpaired comparison; differences combine toolkit correction and population change",
        "repository_commit_before_generation": git_head(root),
        "legacy_source_repository": "https://github.com/daniloceano/energetic_patterns_cyclones_south_atlantic",
        "legacy_source_commit_audited": "3dc622ed0efb03cdf5ef0bf9a4a78a57ceef365d",
        "legacy_cache": str(args.legacy_cache.resolve()),
        "legacy_cache_sha256": sha256_file(args.legacy_cache),
        "corrected_cache": str(args.corrected_cache.resolve()),
        "corrected_cache_sha256": sha256_file(args.corrected_cache),
        "tracks": str(args.tracks.resolve()),
        "tracks_sha256": sha256_file(args.tracks),
        "legacy_cyclones": int(legacy["track_id"].nunique()),
        "legacy_rows": int(len(legacy)),
        "legacy_primary_rows": int(len(legacy_primary)),
        "corrected_cyclones": int(corrected["track_id"].nunique()),
        "corrected_rows": int(len(corrected)),
        "corrected_primary_rows": int(len(corrected_primary)),
        "legacy_total_eof_variance_pct": legacy_variance["explained_variance_pct"].tolist(),
        "clusters": 5,
        "cluster_features": "first eight aligned total-lifecycle PC scores",
        "figure_files": len(manifest),
        "paired_control_report": "docs/paired_control/lec_rerun_paired_control_report.pdf",
        "toolkit_commit": "d38cda7e37d8e8a3a937a5919640a94bef19e34a",
        "toolkit_correction_commit": "d07707767c2962fed0475ff4573e7d15a97f8c69",
    }
    write_json(results_dir / "provenance.json", provenance)
    write_report_markdown(
        docs_dir / "lec_climatology_article_before_after_report.md",
        manifest,
        provenance,
        cluster_meta,
    )
    print(
        json.dumps(
            {
                "figure_files": len(manifest),
                "legacy_cyclones": provenance["legacy_cyclones"],
                "corrected_cyclones": provenance["corrected_cyclones"],
                "output": str(root),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
