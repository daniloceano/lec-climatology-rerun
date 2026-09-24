#!/usr/bin/env python3
"""Recreate the article figures as paired legacy-versus-corrected comparisons."""

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
    BOUNDARY_TERMS,
    CONVERSION_TERMS,
    ENERGY_TERMS,
    EOF_TERMS,
    GENERATION_TERMS,
    PHASES,
    PHASE_COLORS,
    PRESSURE_TERMS,
    TENDENCY_TERMS,
    assign_eof_extremes,
    first_track_rows,
    load_comparison_inputs,
    paired_eof_by_phase,
    paired_intense_clusters,
    paired_total_eof,
    phase_statistics,
    sha256_file,
    track_density,
    write_json,
)
from scripts.article_figures.generate import (  # noqa: E402
    _grouped_bars,
    _kde,
    _percentage_table,
    add_region_boxes,
    cluster_summary,
    fig01,
    fig02,
    figure_stem,
)
from scripts.article_figures.plotting import (  # noqa: E402
    comparison_legend_handles,
    density_levels,
    draw_cycle_comparison,
    draw_cycle_overlay,
    map_axis,
    plot_density,
    save_pair,
)

FIGURE_CAPTIONS = {
    "1": "Track density and the three genesis regions; this track-only reference is common to both versions.",
    "2": "Reference four-box Lorenz Energy Cycle diagram; this conceptual panel is common to both versions.",
    "3": "LEC term probability densities: legacy before values are dashed and corrected after values are solid.",
    "4": "Phase-mean LEC: dark arrows and values are before; red arrows and values are after.",
    "5": "EOF 1 LEC loadings before and after, after matching modes and aligning their signs.",
    "6": "EOF 2 LEC loadings before and after, after matching modes and aligning their signs.",
    "7": "EOF 3 LEC loadings before and after, after matching modes and aligning their signs.",
    "8": "EOF 4 LEC loadings before and after, after matching modes and aligning their signs.",
    "9": "Positive PC-extreme track densities with before on the upper row and after on the lower row.",
    "10": "Negative PC-extreme track densities with before on the upper row and after on the lower row.",
    "11": "Genesis-region and seasonal composition of PC extremes, before above and after below.",
    "12": "Intense-cyclone LEC groups with dark before arrows and red after arrows; corrected groups are centroid-matched.",
    "13": "Track densities of intense-cyclone groups, before above and centroid-matched after groups below.",
    "14": "Intense-group counts, intensity, seasonality and genesis regions, before above and after below.",
    "15": "Lifecycle synthesis shown side by side: before on the left and after on the right.",
    "16a": "EOF 1 lifecycle synthesis, before on the left and matched/sign-aligned after on the right.",
    "16b": "EOF 2 lifecycle synthesis, before on the left and matched/sign-aligned after on the right.",
    "16c": "EOF 3 lifecycle synthesis, before on the left and matched/sign-aligned after on the right.",
    "16d": "EOF 4 lifecycle synthesis, before on the left and matched/sign-aligned after on the right.",
}


def git_head(project: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(project), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _phase_series(stats: pd.DataFrame, version: str, phase: str, field: str) -> pd.Series:
    return stats[(stats["version"] == version) & (stats["phase"] == phase)].set_index("term")[field]


def fig03(legacy: pd.DataFrame, corrected: pd.DataFrame, stem: Path) -> None:
    groups = [
        ("(A) Energy terms", ENERGY_TERMS, 1e6, "MJ m$^{-2}$"),
        ("(B) Conversion terms", CONVERSION_TERMS, 1.0, "W m$^{-2}$"),
        ("(C) Boundary terms", BOUNDARY_TERMS, 1.0, "W m$^{-2}$"),
        ("(D) Pressure-work terms", PRESSURE_TERMS, 1.0, "W m$^{-2}$"),
        ("(E) Generation/residual terms", GENERATION_TERMS, 1.0, "W m$^{-2}$"),
        ("(F) Budget terms", TENDENCY_TERMS, 1.0, "W m$^{-2}$"),
    ]
    colors = plt.get_cmap("tab10").colors
    figure, axes = plt.subplots(2, 3, figsize=(10.8, 6.5))
    for ax, (title, terms, scale, unit) in zip(axes.flat, groups):
        for index, term in enumerate(terms):
            color = colors[index % len(colors)]
            _kde(ax, legacy[term], label="_nolegend_", color=color, scale=scale)
            ax.lines[-1].set_linestyle("--")
            _kde(ax, corrected[term], label=term.replace(" (finite diff.)", ""), color=color, scale=scale)
        if scale == 1.0:
            ax.axvline(0, color="0.45", linestyle=":", linewidth=0.7)
        ax.set_title(title, fontsize=10, fontweight="bold", loc="left")
        ax.set_xlabel(unit, fontsize=8)
        ax.set_ylabel("Density", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(alpha=0.18, linewidth=0.4)
        term_legend = ax.legend(fontsize=6.1, frameon=False, ncol=2 if len(terms) > 4 else 1, loc="upper right")
        ax.add_artist(term_legend)
        ax.legend(
            handles=[
                plt.Line2D([], [], color="0.25", linestyle="--", label="before"),
                plt.Line2D([], [], color="0.25", linestyle="-", label="after"),
            ],
            fontsize=6.2, frameon=False, loc="upper left",
        )
    figure.suptitle("LEC term distributions before and after the toolkit correction", fontsize=13, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.96))
    save_pair(figure, stem)


def fig04(stats: pd.DataFrame, stem: Path) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(8.4, 9.2))
    for ax, phase, tag in zip(axes.flat, PHASES, "ABCD"):
        draw_cycle_comparison(
            ax,
            _phase_series(stats, "before", phase, "mean"),
            _phase_series(stats, "after", phase, "mean"),
            before_uncertainty=_phase_series(stats, "before", phase, "std"),
            after_uncertainty=_phase_series(stats, "after", phase, "std"),
            title=f"({tag}) {phase}",
        )
    figure.legend(handles=comparison_legend_handles(), loc="lower center", ncol=2, frameon=False, fontsize=9)
    figure.suptitle("Phase-mean Lorenz Energy Cycle before and after\nmean ± sample standard deviation", fontsize=14, fontweight="bold")
    figure.tight_layout(rect=(0, 0.045, 1, 0.94))
    save_pair(figure, stem)


def _eof_series(loadings: pd.DataFrame, version: str, phase: str, mode: int) -> pd.Series:
    return loadings[
        (loadings["version"] == version)
        & (loadings["scope"] == phase)
        & (loadings["eof"] == mode)
    ].set_index("term")["loading"]


def fig_eof(mode: int, loadings: pd.DataFrame, variance: pd.DataFrame, stem: Path) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(8.4, 9.2))
    for ax, phase, tag in zip(axes.flat, PHASES, "ABCD"):
        before_var = variance[
            (variance["scope"] == phase) & (variance["eof"] == mode) & (variance["version"] == "before")
        ]["explained_variance_pct"].iloc[0]
        after_row = variance[
            (variance["scope"] == phase) & (variance["eof"] == mode) & (variance["version"] == "after")
        ].iloc[0]
        rank = int(after_row["matched_rank"])
        rank_text = "" if rank == mode else f"; after rank {rank}"
        draw_cycle_comparison(
            ax,
            _eof_series(loadings, "before", phase, mode),
            _eof_series(loadings, "after", phase, mode),
            title=f"({tag}) EOF {mode} - {phase}\nvariance {before_var:.1f}% → {after_row['explained_variance_pct']:.1f}%{rank_text}",
            scale="eof",
        )
    figure.legend(handles=comparison_legend_handles(), loc="lower center", ncol=2, frameon=False, fontsize=9)
    figure.suptitle(f"EOF {mode} loadings before and after", fontsize=14, fontweight="bold")
    figure.tight_layout(rect=(0, 0.045, 1, 0.96))
    save_pair(figure, stem)


def _density_panels(items, tracks, *, lon_bounds=(-80.0, 180.0)):
    blocks = []
    for version, category, ids in items:
        block = tracks[tracks["track_id"].isin(ids)]
        lon, lat, density = track_density(block, lon_bounds=lon_bounds)
        blocks.append((version, category, ids, lon, lat, density))
    levels = density_levels(np.concatenate([item[-1].ravel() for item in blocks]))
    return blocks, levels


def fig_eof_density(sign: str, assignments: pd.DataFrame, tracks: pd.DataFrame, stem: Path) -> None:
    items = []
    for version in ("before", "after"):
        subset = assignments[(assignments["version"] == version) & (assignments["sign"] == sign)]
        for mode in range(1, 5):
            ids = set(subset.loc[subset["dominant_eof"] == mode, "track_id"].astype(int))
            items.append((version, mode, ids))
    blocks, levels = _density_panels(items, tracks)
    figure = plt.figure(figsize=(13.0, 6.3))
    contours = []
    for index, (version, mode, ids, lon, lat, density) in enumerate(blocks):
        ax = map_axis(figure, 241 + index)
        prefix = "Before" if version == "before" else "After"
        contours.append(plot_density(ax, lon, lat, density, title=f"{prefix}: EOF {mode} (n={len(ids)})", levels=levels))
        add_region_boxes(ax)
    figure.suptitle(f"Track density - {sign} total-lifecycle PC extremes", fontsize=13, fontweight="bold")
    figure.subplots_adjust(left=0.035, right=0.975, bottom=0.12, top=0.90, wspace=0.10, hspace=0.28)
    colorbar = figure.colorbar(contours[-1], ax=figure.axes, orientation="horizontal", pad=0.08, fraction=0.045)
    colorbar.set_label("Smoothed track points per month", fontsize=8)
    save_pair(figure, stem)


def fig11(assignments: pd.DataFrame, first: pd.DataFrame, stem: Path) -> None:
    merged = assignments.merge(first[["track_id", "region", "season"]], on="track_id", how="left")
    region_order = ["ARG", "LA-PLATA", "SE-BR"]
    season_order = ["DJF", "MAM", "JJA", "SON"]
    figure, axes = plt.subplots(4, 2, figsize=(9.5, 11.2))
    for version_index, version in enumerate(("before", "after")):
        label = "Before" if version == "before" else "After"
        for sign_index, sign in enumerate(("positive", "negative")):
            row = 2 * version_index + sign_index
            block = merged[(merged["version"] == version) & (merged["sign"] == sign)]
            sign_label = "+" if sign == "positive" else "-"
            _grouped_bars(axes[row, 0], _percentage_table(block, "region", region_order), region_order, f"{label}: genesis regions - EOF({sign_label})")
            _grouped_bars(axes[row, 1], _percentage_table(block, "season", season_order), season_order, f"{label}: seasonal occurrence - EOF({sign_label})")
    figure.suptitle("Genesis and seasonal composition of total-lifecycle EOF extremes", fontsize=13, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.95))
    save_pair(figure, stem)


def _group_values(cache: pd.DataFrame, ids: set[int]):
    block = cache[cache["track_id"].isin(ids)].groupby("track_id")[EOF_TERMS].mean()
    return block.mean(), block.std(ddof=1)


def fig12(
    legacy: pd.DataFrame,
    corrected: pd.DataFrame,
    legacy_assignments: pd.DataFrame,
    corrected_assignments: pd.DataFrame,
    stem: Path,
) -> None:
    all_ids = set(legacy_assignments["track_id"].astype(int))
    groups = [("All intense systems", all_ids, all_ids)]
    for cluster in range(1, 5):
        old_ids = set(legacy_assignments.loc[legacy_assignments["cluster"] == cluster, "track_id"].astype(int))
        new_ids = set(corrected_assignments.loc[corrected_assignments["cluster"] == cluster, "track_id"].astype(int))
        groups.append((f"Matched cluster {cluster}", old_ids, new_ids))
    figure, axes = plt.subplots(2, 3, figsize=(11.2, 7.7))
    for ax, (label, old_ids, new_ids), tag in zip(axes.flat, groups, "ABCDE"):
        old_mean, old_std = _group_values(legacy, old_ids)
        new_mean, new_std = _group_values(corrected, new_ids)
        draw_cycle_comparison(
            ax, old_mean, new_mean,
            before_uncertainty=old_std, after_uncertainty=new_std,
            title=f"({tag}) {label}\n(n={len(old_ids)} → {len(new_ids)})",
        )
    axes.flat[-1].axis("off")
    figure.legend(handles=comparison_legend_handles(), loc="lower center", ncol=2, frameon=False, fontsize=9)
    figure.suptitle("Intense-cyclone LEC groups before and after", fontsize=14, fontweight="bold")
    figure.tight_layout(rect=(0, 0.05, 1, 0.95))
    save_pair(figure, stem)


def fig13(tracks: pd.DataFrame, assignments: pd.DataFrame, stem: Path) -> None:
    items = []
    for version in ("before", "after"):
        for cluster in range(1, 5):
            ids = set(assignments.loc[(assignments["version"] == version) & (assignments["cluster"] == cluster), "track_id"].astype(int))
            items.append((version, cluster, ids))
    blocks, levels = _density_panels(items, tracks, lon_bounds=(-80, 100))
    figure = plt.figure(figsize=(13.0, 6.3))
    contours = []
    for index, (version, cluster, ids, lon, lat, density) in enumerate(blocks):
        ax = map_axis(figure, 241 + index, extent=(-80, 100, -85, -15))
        prefix = "Before" if version == "before" else "After"
        contours.append(plot_density(ax, lon, lat, density, title=f"{prefix}: cluster {cluster} (n={len(ids)})", levels=levels))
        add_region_boxes(ax)
    figure.suptitle("Track density of matched intense-cyclone groups", fontsize=13, fontweight="bold")
    figure.subplots_adjust(left=0.035, right=0.975, bottom=0.12, top=0.90, wspace=0.10, hspace=0.28)
    colorbar = figure.colorbar(contours[-1], ax=figure.axes, orientation="horizontal", pad=0.08, fraction=0.045)
    colorbar.set_label("Smoothed track points per month", fontsize=8)
    save_pair(figure, stem)


def _cluster_row(axes, version: str, assignments: pd.DataFrame, tracks: pd.DataFrame, first: pd.DataFrame):
    maximum = tracks.groupby("track_id")["vor42"].max().rename("max_vor42")
    merged = assignments.merge(first[["track_id", "region", "season"]], on="track_id", how="left").merge(maximum, on="track_id", how="left")
    summary = cluster_summary(assignments, tracks, first)
    clusters = np.arange(1, 5)
    colors = plt.get_cmap("Set2").colors[:4]
    axes[0].bar(clusters, summary.set_index("cluster").loc[clusters, "n"], color=colors)
    axes[0].set_title(f"{version}: system count", fontsize=9, fontweight="bold", loc="left")
    data = [merged.loc[merged["cluster"] == cluster, "max_vor42"].dropna() for cluster in clusters]
    bp = axes[1].boxplot(data, patch_artist=True, labels=clusters, showfliers=True, flierprops=dict(markersize=2, markerfacecolor="none"))
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
    axes[1].set_title(f"{version}: maximum intensity", fontsize=9, fontweight="bold", loc="left")
    seasons = ["DJF", "MAM", "JJA", "SON"]
    regions = ["ARG", "LA-PLATA", "SE-BR"]
    _grouped_bars(axes[2], summary.set_index("cluster")[[f"season_{x}_pct" for x in seasons]].loc[clusters].to_numpy(), seasons, f"{version}: seasonality")
    _grouped_bars(axes[3], summary.set_index("cluster")[[f"region_{x}_pct" for x in regions]].loc[clusters].to_numpy(), regions, f"{version}: genesis regions")
    for ax in axes:
        ax.set_xticks(clusters)
        ax.set_xlabel("Matched cluster", fontsize=7)
        ax.tick_params(labelsize=6.5)
        ax.grid(axis="y", alpha=0.2)
    return summary


def fig14(assignments: pd.DataFrame, tracks: pd.DataFrame, first: pd.DataFrame, stem: Path):
    figure, axes = plt.subplots(2, 4, figsize=(13.0, 6.3))
    legacy_assignments = assignments[assignments["version"] == "before"].drop(columns="version")
    corrected_assignments = assignments[assignments["version"] == "after"].drop(columns="version")
    before_summary = _cluster_row(axes[0], "Before", legacy_assignments, tracks, first)
    after_summary = _cluster_row(axes[1], "After", corrected_assignments, tracks, first)
    before_summary.insert(0, "version", "before")
    after_summary.insert(0, "version", "after")
    figure.suptitle("Matched intense-cyclone group characteristics before and after", fontsize=13, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.95))
    save_pair(figure, stem)
    return pd.concat([before_summary, after_summary], ignore_index=True)


def fig15(stats: pd.DataFrame, stem: Path) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(12.0, 6.2))
    for ax, version, title in zip(axes, ("before", "after"), ("Before - legacy", "After - corrected")):
        series = [(phase, _phase_series(stats, version, phase, "mean"), PHASE_COLORS[phase]) for phase in PHASES]
        draw_cycle_overlay(ax, series, title=title, scale="terms")
    handles = [plt.Line2D([], [], color=PHASE_COLORS[p], linewidth=4, label=p) for p in PHASES]
    figure.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=9)
    figure.suptitle("Phase-mean LEC synthesis: before versus after", fontsize=14, fontweight="bold")
    figure.tight_layout(rect=(0, 0.06, 1, 0.95))
    save_pair(figure, stem)


def fig16(mode: int, loadings: pd.DataFrame, stem: Path) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(12.0, 6.2))
    for ax, version, title in zip(axes, ("before", "after"), ("Before - legacy", "After - corrected")):
        series = [(phase, _eof_series(loadings, version, phase, mode), PHASE_COLORS[phase]) for phase in PHASES]
        draw_cycle_overlay(ax, series, title=title, scale="eof")
    handles = [plt.Line2D([], [], color=PHASE_COLORS[p], linewidth=4, label=p) for p in PHASES]
    figure.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=9)
    figure.suptitle(f"EOF {mode} synthesis: before versus matched/sign-aligned after", fontsize=14, fontweight="bold")
    figure.tight_layout(rect=(0, 0.06, 1, 0.95))
    save_pair(figure, stem)


def write_report_markdown(path: Path, manifest: pd.DataFrame, provenance: dict, cluster_meta: dict) -> None:
    lines = [
        "# LEC climatology figures - before versus after",
        "",
        "This report compares the legacy article results directly with the corrected LorenzCycleToolKit 2.0.0 rerun. Both versions use the same 3,820 cyclones and the same 15,280 primary cyclone-phase rows.",
        "",
        "## Comparison rules",
        "",
        "- Dashed lines are before and solid lines are after in Figure 3.",
        "- Dark arrows/values are before and red arrows/values are after in four-box LEC diagrams.",
        "- Figures 9, 10, 11, 13 and 14 place before above and after below.",
        "- Figure 15 places before and after side by side.",
        "- Figure 16 is split into one 1x2 comparison for each EOF.",
        "- Corrected EOFs are matched one-to-one to legacy EOFs by maximum absolute loading-pattern correlation and then sign-aligned.",
        "- Corrected intense groups are matched to legacy groups by minimum standardized centroid distance.",
        "",
        "## Data lineage",
        "",
        f"- Paired cyclones: **{provenance['paired_cyclones']:,}**.",
        f"- Primary paired rows per version: **{provenance['primary_phase_rows_per_version']:,}**.",
        f"- Paired intense cyclones: **{cluster_meta['eligible_paired_cyclones']:,}**.",
        "- Secondary lifecycle periods remain preserved upstream but are outside this four-phase report.",
        "",
        "## Figures",
        "",
    ]
    for row in manifest.itertuples():
        relative = Path("..") / row.png
        lines.extend([f"### Figure {row.figure_label}", "", f"![Figure {row.figure_label}]({relative.as_posix()})", "", f"*{row.caption}*", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-cache", type=Path, required=True)
    parser.add_argument("--corrected-cache", type=Path, required=True)
    parser.add_argument("--tracks", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.output_root.resolve()
    figures_dir = root / "figures" / "lec_climatology_corrected"
    results_dir = root / "results" / "lec_climatology_corrected"
    docs_dir = root / "docs"
    figures_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    legacy, corrected, tracks = load_comparison_inputs(args.legacy_cache, args.corrected_cache, args.tracks)
    stats = pd.concat([
        phase_statistics(legacy).assign(version="before"),
        phase_statistics(corrected).assign(version="after"),
    ], ignore_index=True)
    phase_loadings, phase_variance = paired_eof_by_phase(legacy, corrected)
    total_loadings, total_variance, total_scores = paired_total_eof(legacy, corrected)
    extreme_parts = []
    for version in ("before", "after"):
        part = assign_eof_extremes(total_scores[total_scores["version"] == version].drop(columns="version"))
        part.insert(1, "version", version)
        extreme_parts.append(part)
    eof_assignments = pd.concat(extreme_parts, ignore_index=True)
    first = first_track_rows(tracks)
    legacy_clusters, corrected_clusters, legacy_centers, corrected_centers, cluster_meta = paired_intense_clusters(
        legacy, corrected, tracks
    )
    cluster_assignments = pd.concat([legacy_clusters, corrected_clusters], ignore_index=True)

    fig01(tracks, figure_stem(figures_dir, 1, "track_density"))
    fig02(figure_stem(figures_dir, 2, "lec_reference"))
    fig03(legacy, corrected, figure_stem(figures_dir, 3, "term_pdfs_before_after"))
    fig04(stats, figure_stem(figures_dir, 4, "phase_mean_lec_before_after"))
    for mode in range(1, 5):
        fig_eof(mode, phase_loadings, phase_variance, figure_stem(figures_dir, mode + 4, f"eof{mode}_lec_before_after"))
    fig_eof_density("positive", eof_assignments, tracks, figure_stem(figures_dir, 9, "eof_positive_density_before_after"))
    fig_eof_density("negative", eof_assignments, tracks, figure_stem(figures_dir, 10, "eof_negative_density_before_after"))
    fig11(eof_assignments, first, figure_stem(figures_dir, 11, "eof_genesis_season_before_after"))
    fig12(legacy, corrected, legacy_clusters, corrected_clusters, figure_stem(figures_dir, 12, "intense_group_lec_before_after"))
    fig13(tracks, cluster_assignments, figure_stem(figures_dir, 13, "intense_group_density_before_after"))
    cluster_stats = fig14(cluster_assignments, tracks, first, figure_stem(figures_dir, 14, "intense_group_characteristics_before_after"))
    fig15(stats, figure_stem(figures_dir, 15, "phase_synthesis_before_after"))
    suffixes = "abcd"
    for mode, suffix in zip(range(1, 5), suffixes):
        fig16(mode, phase_loadings, figures_dir / f"fig_16{suffix}_eof{mode}_synthesis_before_after")

    stats.to_csv(results_dir / "phase_statistics.csv", index=False, float_format="%.8g")
    phase_loadings.to_csv(results_dir / "eof_loadings_by_phase.csv", index=False, float_format="%.8g")
    phase_variance.to_csv(results_dir / "eof_variance_by_phase.csv", index=False, float_format="%.8g")
    total_loadings.to_csv(results_dir / "eof_loadings_total.csv", index=False, float_format="%.8g")
    total_variance.to_csv(results_dir / "eof_variance_total.csv", index=False, float_format="%.8g")
    total_scores.to_csv(results_dir / "eof_scores_total.csv", index=False, float_format="%.8g")
    eof_assignments.to_csv(results_dir / "eof_extreme_assignments.csv", index=False, float_format="%.8g")
    cluster_assignments.to_csv(results_dir / "intense_cluster_assignments.csv", index=False)
    centers = pd.concat([
        pd.DataFrame(legacy_centers).assign(version="before", cluster=np.arange(1, 5)),
        pd.DataFrame(corrected_centers).assign(version="after", cluster=np.arange(1, 5)),
    ], ignore_index=True)
    centers.to_csv(results_dir / "intense_cluster_centers.csv", index=False, float_format="%.8g")
    cluster_stats.to_csv(results_dir / "intense_cluster_statistics.csv", index=False, float_format="%.8g")
    write_json(results_dir / "intense_cluster_metadata.json", cluster_meta)

    figure_specs = [(str(number), sorted(figures_dir.glob(f"fig_{number:02d}_*.png"))[-1]) for number in range(1, 16)]
    figure_specs.extend(
        [(f"16{suffix}", figures_dir / f"fig_16{suffix}_eof{mode}_synthesis_before_after.png") for mode, suffix in zip(range(1, 5), suffixes)]
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
    provenance = {
        "workflow": "paired before-versus-after reproduction of article Figures 1-16",
        "repository_commit_before_generation": git_head(root),
        "legacy_cache": str(args.legacy_cache.resolve()),
        "legacy_cache_sha256": sha256_file(args.legacy_cache),
        "corrected_cache": str(args.corrected_cache.resolve()),
        "corrected_cache_sha256": sha256_file(args.corrected_cache),
        "tracks": str(args.tracks.resolve()),
        "tracks_sha256": sha256_file(args.tracks),
        "paired_cyclones": 3820,
        "primary_phase_rows_per_version": 15280,
        "figure_files": len(manifest),
        "toolkit_commit": "d38cda7e37d8e8a3a937a5919640a94bef19e34a",
        "toolkit_correction_commit": "d07707767c2962fed0475ff4573e7d15a97f8c69",
        "notes": "Legacy and corrected analyses use identical cyclone-phase keys; EOFs and clusters are explicitly matched.",
    }
    write_json(results_dir / "provenance.json", provenance)
    write_report_markdown(docs_dir / "lec_climatology_corrected_figures_report.md", manifest, provenance, cluster_meta)
    print(json.dumps({"figure_files": len(manifest), "paired_cyclones": 3820, "output": str(root)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
