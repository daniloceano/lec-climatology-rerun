#!/usr/bin/env python3
"""Recreate Figures 1-16 of the LEC climatology article with corrected data.

The workflow preserves the visual/scientific roles of the published figures,
but all LEC-dependent quantities are recomputed from the validated 3,820-case
LorenzCycleToolKit 2.0.0 rerun. Legacy figures are never overwritten.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import gaussian_kde  # noqa: E402

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.article_figures.common import (  # noqa: E402
    BOUNDARY_TERMS,
    CLUSTER_TERMS,
    CONVERSION_TERMS,
    ENERGY_TERMS,
    EOF_TERMS,
    GENERATION_TERMS,
    PHASES,
    PHASE_COLORS,
    PRESSURE_TERMS,
    REGIONS,
    TENDENCY_TERMS,
    assign_eof_extremes,
    eof_by_phase,
    first_track_rows,
    intense_clusters,
    load_inputs,
    phase_statistics,
    sha256_file,
    total_eof,
    track_density,
    write_json,
)
from scripts.article_figures.captions import FIGURE_CAPTIONS  # noqa: E402
from scripts.article_figures.plotting import (  # noqa: E402
    ARROWS,
    BOXES,
    draw_cycle,
    draw_cycle_overlay,
    map_axis,
    plot_density,
    save_pair,
)

def git_head(project: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(project), "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def figure_stem(figures_dir: Path, number: int, name: str) -> Path:
    return figures_dir / f"fig_{number:02d}_{name}"


def add_region_boxes(ax, *, show_labels: bool = True) -> None:
    import cartopy.crs as ccrs

    label_positions = {
        "SE-BR": (-41.0, -25.0),
        "LA-PLATA": (-66.5, -25.0),
        "ARG": (-67.5, -42.0),
    }
    for name, (lon_min, lat_min, lon_max, lat_max) in REGIONS.items():
        ax.add_patch(
            patches.Rectangle(
                (lon_min, lat_min), lon_max - lon_min, lat_max - lat_min,
                fill=False, edgecolor="black", linewidth=1.0, linestyle="--",
                transform=ccrs.PlateCarree(), zorder=7,
            )
        )
        if show_labels:
            x, y = label_positions[name]
            ax.text(
                x, y, name,
                ha="left", va="center", fontsize=5.7, fontweight="bold",
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.75, pad=1),
                transform=ccrs.PlateCarree(), zorder=8,
            )


def fig01(tracks: pd.DataFrame, stem: Path) -> None:
    lon, lat, density = track_density(tracks)
    figure = plt.figure(figsize=(7.2, 3.2))
    ax = map_axis(figure, 111)
    contour = plot_density(ax, lon, lat, density, title="South Atlantic cyclone track density")
    add_region_boxes(ax)
    colorbar = figure.colorbar(contour, ax=ax, orientation="horizontal", pad=0.08, fraction=0.08)
    colorbar.set_label("Smoothed track points per month", fontsize=8)
    colorbar.ax.tick_params(labelsize=7)
    save_pair(figure, stem)


def fig02(stem: Path) -> None:
    figure, ax = plt.subplots(figsize=(6.2, 6.2))
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.18, 1.18)
    ax.set_aspect("equal")
    ax.axis("off")
    for term, (x, y) in BOXES.items():
        ax.add_patch(patches.Rectangle((x - 0.20, y - 0.20), 0.40, 0.40,
                                       facecolor="#8ecae6", edgecolor="#36535f", linewidth=1.0))
        short = term.replace(" (finite diff.)", "")
        ax.text(x, y, short, ha="center", va="center", fontsize=10, fontweight="bold")
    colors = {"Ca": "#8d008d", "Ce": "#8d008d", "Ck": "#008000", "Ge": "#ef1d1d"}
    for term, (tail, head, label) in ARROWS.items():
        color = colors.get(term, "#55524c")
        width = 5.0 if term in colors else 3.4
        ax.annotate("", xy=head, xytext=tail,
                    arrowprops=dict(facecolor=color, edgecolor=color, width=width,
                                    headwidth=width * 2.2, headlength=width * 2.2))
        ax.text(label[0], label[1], term, ha="center", va="center", fontsize=9, fontweight="bold")
    ax.text(-0.78, -0.02, "Baroclinic\nconversion", color="#8d008d", ha="right", va="center",
            fontsize=10, fontweight="bold")
    ax.text(0.78, -0.02, "Barotropic\nconversion", color="#008000", ha="left", va="center",
            fontsize=10, fontweight="bold")
    ax.text(-0.50, -1.14, "Diabatic generation", color="#ef1d1d", ha="center", va="top",
            fontsize=10, fontweight="bold")
    ax.set_title("Lorenz Energy Cycle reference diagram", fontsize=13, fontweight="bold", pad=8)
    save_pair(figure, stem)


def _kde(ax, values: pd.Series, *, label: str, color: str, scale: float = 1.0) -> None:
    clean = pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
    if not len(clean):
        return
    clean = clean / scale
    low, high = np.quantile(clean, [0.01, 0.99])
    clipped = np.clip(clean, low, high)
    if np.allclose(clipped.std(), 0):
        return
    grid = np.linspace(low, high, 240)
    density = gaussian_kde(clipped, bw_method="scott")(grid)
    ax.plot(grid, density, color=color, linewidth=1.35, label=label)


def fig03(cache: pd.DataFrame, stem: Path) -> None:
    groups = [
        ("(A) Energy terms", ENERGY_TERMS, 1e6, "MJ m$^{-2}$"),
        ("(B) Conversion terms", CONVERSION_TERMS, 1.0, "W m$^{-2}$"),
        ("(C) Boundary terms", BOUNDARY_TERMS, 1.0, "W m$^{-2}$"),
        ("(D) Pressure-work terms", PRESSURE_TERMS, 1.0, "W m$^{-2}$"),
        ("(E) Generation/residual terms", GENERATION_TERMS, 1.0, "W m$^{-2}$"),
        ("(F) Budget terms", TENDENCY_TERMS, 1.0, "W m$^{-2}$"),
    ]
    colors = plt.get_cmap("tab10").colors
    figure, axes = plt.subplots(2, 3, figsize=(10.4, 6.2))
    for ax, (title, terms, scale, unit) in zip(axes.flat, groups):
        for index, term in enumerate(terms):
            _kde(ax, cache[term], label=term.replace(" (finite diff.)", ""),
                 color=colors[index % len(colors)], scale=scale)
        if scale == 1.0:
            ax.axvline(0, color="0.45", linestyle="--", linewidth=0.7)
        ax.set_title(title, fontsize=10, fontweight="bold", loc="left")
        ax.set_xlabel(unit, fontsize=8)
        ax.set_ylabel("Density", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(alpha=0.18, linewidth=0.4)
        ax.legend(fontsize=6.4, frameon=False, ncol=2 if len(terms) > 4 else 1)
    figure.suptitle("Corrected LEC term distributions - primary lifecycle phases", fontsize=13, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.96))
    save_pair(figure, stem)


def _phase_series(stats: pd.DataFrame, phase: str, field: str) -> pd.Series:
    return stats[stats["phase"] == phase].set_index("term")[field]


def fig04(stats: pd.DataFrame, stem: Path) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(8.0, 8.9))
    for ax, phase, tag in zip(axes.flat, PHASES, "ABCD"):
        draw_cycle(
            ax, _phase_series(stats, phase, "mean"),
            uncertainty=_phase_series(stats, phase, "std"),
            title=f"({tag}) {phase}", color="#4a4a45", scale="terms",
        )
    figure.suptitle("Corrected Lorenz Energy Cycle by lifecycle phase\nmean ± sample standard deviation", fontsize=14, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.95))
    save_pair(figure, stem)


def fig_eof(
    mode: int,
    loadings: pd.DataFrame,
    variance: pd.DataFrame,
    stem: Path,
) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(8.0, 8.9))
    for ax, phase, tag in zip(axes.flat, PHASES, "ABCD"):
        values = loadings[(loadings["scope"] == phase) & (loadings["eof"] == mode)].set_index("term")["loading"]
        var = variance[(variance["scope"] == phase) & (variance["eof"] == mode)]["explained_variance_pct"].iloc[0]
        draw_cycle(ax, values, title=f"({tag}) EOF {mode}\n{phase}\nExp. var.: {var:.2f}%",
                   color="#4a4a45", scale="eof")
    figure.suptitle(f"Corrected EOF {mode} loadings by lifecycle phase", fontsize=14, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.96))
    save_pair(figure, stem)


def fig_eof_density(
    sign: str,
    assignments: pd.DataFrame,
    tracks: pd.DataFrame,
    stem: Path,
) -> None:
    subset = assignments[assignments["sign"] == sign]
    figure = plt.figure(figsize=(10.0, 5.7))
    contours = []
    for mode, position, tag in zip(range(1, 5), (221, 222, 223, 224), "ABCD"):
        ids = set(subset.loc[subset["dominant_eof"] == mode, "track_id"].astype(int))
        block = tracks[tracks["track_id"].isin(ids)]
        lon, lat, density = track_density(block)
        ax = map_axis(figure, position)
        contours.append(plot_density(ax, lon, lat, density, title=f"({tag}) EOF {mode} (n={len(ids)})"))
        add_region_boxes(ax)
    figure.suptitle(f"Track density - {sign} total-lifecycle PC extremes", fontsize=13, fontweight="bold")
    figure.subplots_adjust(left=0.04, right=0.96, bottom=0.08, top=0.90, wspace=0.10, hspace=0.22)
    colorbar = figure.colorbar(contours[-1], ax=figure.axes, orientation="horizontal", pad=0.07, fraction=0.05)
    colorbar.set_label("Smoothed track points per month", fontsize=8)
    save_pair(figure, stem)


def _percentage_table(frame: pd.DataFrame, category: str, order: list[str]) -> np.ndarray:
    result = np.zeros((4, len(order)), dtype=float)
    for mode in range(1, 5):
        block = frame[frame["dominant_eof"] == mode]
        if len(block):
            counts = block[category].value_counts(normalize=True)
            result[mode - 1] = [100 * counts.get(item, 0.0) for item in order]
    return result


def _grouped_bars(ax, values: np.ndarray, labels: list[str], title: str) -> None:
    x = np.arange(1, 5)
    width = 0.8 / len(labels)
    colors = plt.get_cmap("Set2").colors
    for index, label in enumerate(labels):
        ax.bar(x - 0.4 + width / 2 + index * width, values[:, index], width,
               label=label, color=colors[index])
    ax.set_xticks(x)
    ax.set_xlabel("EOF", fontsize=8)
    ax.set_ylabel("Occurrence (%)", fontsize=8)
    ax.set_title(title, fontsize=9, fontweight="bold", loc="left")
    ax.tick_params(labelsize=7)
    ax.grid(axis="y", alpha=0.2)
    ax.legend(fontsize=6.5, frameon=False, ncol=2)


def fig11(assignments: pd.DataFrame, first: pd.DataFrame, stem: Path) -> None:
    merged = assignments.merge(first[["track_id", "region", "season"]], on="track_id", how="left")
    region_order = ["ARG", "LA-PLATA", "SE-BR"]
    season_order = ["DJF", "MAM", "JJA", "SON"]
    figure, axes = plt.subplots(2, 2, figsize=(9.2, 6.4))
    for row, sign in enumerate(("positive", "negative")):
        block = merged[merged["sign"] == sign]
        symbol = "+" if sign == "positive" else "-"
        _grouped_bars(axes[row, 0], _percentage_table(block, "region", region_order),
                      region_order, f"({'A' if row == 0 else 'C'}) Genesis proportion - EOF({symbol})")
        _grouped_bars(axes[row, 1], _percentage_table(block, "season", season_order),
                      season_order, f"({'B' if row == 0 else 'D'}) Seasonal occurrences - EOF({symbol})")
    figure.suptitle("Corrected total-lifecycle EOF extremes", fontsize=13, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.95))
    save_pair(figure, stem)


def group_phase_stats(cache: pd.DataFrame, ids: set[int]) -> pd.DataFrame:
    return phase_statistics(cache[cache["track_id"].isin(ids)])


def fig12(cache: pd.DataFrame, assignments: pd.DataFrame, stem: Path) -> None:
    all_ids = set(assignments["track_id"].astype(int))
    groups = [("All intense systems", all_ids)] + [
        (f"Cluster {cluster}", set(assignments.loc[assignments["cluster"] == cluster, "track_id"].astype(int)))
        for cluster in range(1, 5)
    ]
    figure, axes = plt.subplots(2, 3, figsize=(11.0, 7.4))
    for ax, (label, ids), tag in zip(axes.flat, groups, "ABCDE"):
        stats = group_phase_stats(cache, ids)
        values = cache[cache["track_id"].isin(ids)].groupby("track_id")[EOF_TERMS].mean().mean()
        std = cache[cache["track_id"].isin(ids)].groupby("track_id")[EOF_TERMS].mean().std(ddof=1)
        draw_cycle(ax, values, uncertainty=std, title=f"({tag}) {label}\n(n={len(ids)})", scale="terms")
    axes.flat[-1].axis("off")
    figure.suptitle("Corrected LEC groups among intense cyclones", fontsize=14, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.95))
    save_pair(figure, stem)


def fig13(tracks: pd.DataFrame, assignments: pd.DataFrame, stem: Path) -> None:
    figure = plt.figure(figsize=(10.0, 5.7))
    contours = []
    for cluster, position, tag in zip(range(1, 5), (221, 222, 223, 224), "ABCD"):
        ids = set(assignments.loc[assignments["cluster"] == cluster, "track_id"].astype(int))
        block = tracks[tracks["track_id"].isin(ids)]
        lon, lat, density = track_density(block, lon_bounds=(-80, 100))
        ax = map_axis(figure, position, extent=(-80, 100, -85, -15))
        contours.append(plot_density(ax, lon, lat, density, title=f"({tag}) Cluster {cluster} (n={len(ids)})"))
        add_region_boxes(ax)
    figure.suptitle("Track density of corrected intense-cyclone groups", fontsize=13, fontweight="bold")
    figure.subplots_adjust(left=0.04, right=0.96, bottom=0.08, top=0.90, wspace=0.10, hspace=0.22)
    colorbar = figure.colorbar(contours[-1], ax=figure.axes, orientation="horizontal", pad=0.07, fraction=0.05)
    colorbar.set_label("Smoothed track points per month", fontsize=8)
    save_pair(figure, stem)


def cluster_summary(assignments: pd.DataFrame, tracks: pd.DataFrame, first: pd.DataFrame) -> pd.DataFrame:
    maximum = tracks.groupby("track_id")["vor42"].max().rename("max_vor42")
    merged = assignments.merge(first[["track_id", "region", "season"]], on="track_id", how="left")
    merged = merged.merge(maximum, on="track_id", how="left")
    rows: list[dict] = []
    for cluster, block in merged.groupby("cluster"):
        row = {
            "cluster": int(cluster),
            "n": int(len(block)),
            "max_vor42_mean": float(block["max_vor42"].mean()),
            "max_vor42_median": float(block["max_vor42"].median()),
        }
        for category in ["DJF", "MAM", "JJA", "SON"]:
            row[f"season_{category}_pct"] = float(100 * (block["season"] == category).mean())
        for category in ["ARG", "LA-PLATA", "SE-BR"]:
            row[f"region_{category}_pct"] = float(100 * (block["region"] == category).mean())
        rows.append(row)
    return pd.DataFrame(rows)


def fig14(assignments: pd.DataFrame, tracks: pd.DataFrame, first: pd.DataFrame, stem: Path) -> pd.DataFrame:
    maximum = tracks.groupby("track_id")["vor42"].max().rename("max_vor42")
    merged = assignments.merge(first[["track_id", "region", "season"]], on="track_id", how="left")
    merged = merged.merge(maximum, on="track_id", how="left")
    summary = cluster_summary(assignments, tracks, first)
    figure, axes = plt.subplots(2, 2, figsize=(9.2, 6.4))
    clusters = np.arange(1, 5)
    colors = plt.get_cmap("Set2").colors[:4]
    axes[0, 0].bar(clusters, summary.set_index("cluster").loc[clusters, "n"], color=colors)
    for x, value in zip(clusters, summary.set_index("cluster").loc[clusters, "n"]):
        axes[0, 0].text(x, value, str(int(value)), ha="center", va="bottom", fontsize=8, fontweight="bold")
    axes[0, 0].set_title("(A) Count of systems", fontsize=10, fontweight="bold", loc="left")
    axes[0, 0].set_ylabel("Number of systems", fontsize=8)

    data = [merged.loc[merged["cluster"] == cluster, "max_vor42"].dropna() for cluster in clusters]
    bp = axes[0, 1].boxplot(data, patch_artist=True, labels=clusters, showfliers=True,
                            flierprops=dict(markersize=2, markerfacecolor="none"))
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
    axes[0, 1].set_title("(B) Maximum intensity", fontsize=10, fontweight="bold", loc="left")
    axes[0, 1].set_ylabel(r"Maximum $\zeta_{850}$ ($10^{-5}$ s$^{-1}$)", fontsize=8)

    seasons = ["DJF", "MAM", "JJA", "SON"]
    regions = ["ARG", "LA-PLATA", "SE-BR"]
    _grouped_bars(
        axes[1, 0], summary.set_index("cluster")[[f"season_{x}_pct" for x in seasons]].loc[clusters].to_numpy(),
        seasons, "(C) Seasonality of systems",
    )
    _grouped_bars(
        axes[1, 1], summary.set_index("cluster")[[f"region_{x}_pct" for x in regions]].loc[clusters].to_numpy(),
        regions, "(D) Genesis-region distribution",
    )
    for ax in axes.flat:
        ax.set_xticks(clusters)
        ax.set_xlabel("Cluster", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(axis="y", alpha=0.2)
    figure.suptitle("Corrected intense-cyclone group characteristics", fontsize=13, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.95))
    save_pair(figure, stem)
    return summary


def fig15(stats: pd.DataFrame, stem: Path) -> None:
    series = [
        (phase, _phase_series(stats, phase, "mean"), PHASE_COLORS[phase]) for phase in PHASES
    ]
    figure, ax = plt.subplots(figsize=(7.2, 7.2))
    draw_cycle_overlay(ax, series, title="", scale="terms")
    handles = [plt.Line2D([], [], color=PHASE_COLORS[p], linewidth=4, label=p) for p in PHASES]
    figure.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=8)
    figure.suptitle("Corrected phase-mean synthesis", fontsize=14, fontweight="bold", y=0.97)
    figure.tight_layout(rect=(0, 0.05, 1, 0.95))
    save_pair(figure, stem)


def fig16(loadings: pd.DataFrame, variance: pd.DataFrame, stem: Path) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(9.5, 9.5))
    for ax, mode in zip(axes.flat, range(1, 5)):
        series = []
        labels = []
        for phase in PHASES:
            values = loadings[(loadings["scope"] == phase) & (loadings["eof"] == mode)].set_index("term")["loading"]
            series.append((phase, values, PHASE_COLORS[phase]))
            var = variance[(variance["scope"] == phase) & (variance["eof"] == mode)]["explained_variance_pct"].iloc[0]
            labels.append(f"{phase} {var:.1f}%")
        draw_cycle_overlay(ax, series, title=f"EOF {mode}", scale="eof")
    handles = [plt.Line2D([], [], color=PHASE_COLORS[p], linewidth=4, label=p) for p in PHASES]
    figure.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=9)
    figure.suptitle("Corrected EOF synthesis by lifecycle phase", fontsize=14, fontweight="bold")
    figure.tight_layout(rect=(0, 0.05, 1, 0.96))
    save_pair(figure, stem)


def write_report_markdown(
    path: Path,
    cache: pd.DataFrame,
    stats: pd.DataFrame,
    variance: pd.DataFrame,
    assignments: pd.DataFrame,
    cluster_meta: dict,
    cluster_stats: pd.DataFrame,
) -> None:
    values = stats.pivot(index="phase", columns="term", values="mean")
    eof1 = variance[variance["eof"] == 1].set_index("scope")["explained_variance_pct"]
    lines = [
        "# Corrected reproduction of the LEC climatology figures",
        "",
        "This report recreates the 16 main figures of *Lorenz Energy Cycle Climatology for the Southwestern Atlantic Cyclones* using the validated LorenzCycleToolKit 2.0.0 rerun. It is a new corrected product; the published/legacy figures are not overwritten.",
        "",
        "## Data lineage and scope",
        "",
        f"- Corrected population: **{cache['track_id'].nunique():,} cyclones**.",
        f"- Primary lifecycle matrix: **{len(cache):,} cyclone-phase rows** ({', '.join(PHASES)}).",
        "- Secondary lifecycle periods remain preserved in the corrected cache but are excluded from these main-article panels, matching the four-phase scope.",
        "- LEC terms derive from the pinned corrected toolkit; track maps and metadata derive from the frozen South Atlantic track dataset.",
        "- All figures are exported as 300-dpi PNG and vector PDF.",
        "",
        "## Updated numerical landmarks",
        "",
        "| phase | Ca mean | Ck mean | Ce mean | EOF1 variance |",
        "|---|---:|---:|---:|---:|",
    ]
    for phase in PHASES:
        lines.append(
            f"| {phase} | {values.loc[phase, 'Ca']:.2f} | {values.loc[phase, 'Ck']:.2f} | "
            f"{values.loc[phase, 'Ce']:.2f} | {eof1.loc[phase]:.2f}% |"
        )
    lines.extend(
        [
            "",
            f"The total-lifecycle PC-extreme classification contains {len(assignments[assignments['sign']=='positive']):,} positive and {len(assignments[assignments['sign']=='negative']):,} negative assignments (a cyclone may occur once in each sign set because different PCs are assessed independently).",
            "",
            f"The intense-cyclone analysis uses the published 0.90 pointwise-vorticity quantile criterion and retains **{cluster_meta['eligible_corrected_cyclones']:,} corrected cyclones**. Four K-means groups are retained for direct structural comparability with the article.",
            "",
            "| cluster | n | median maximum vorticity |",
            "|---:|---:|---:|",
        ]
    )
    for row in cluster_stats.sort_values("cluster").itertuples():
        lines.append(f"| {row.cluster} | {row.n} | {row.max_vor42_median:.2f} |")
    lines.extend(["", "## Figures", ""])
    for number in range(1, 17):
        png = sorted(path.parents[2].joinpath("figures", "paired_control", "article_style").glob(f"fig_{number:02d}_*.png"))[0]
        relative = Path("..") / ".." / "figures" / "paired_control" / "article_style" / png.name
        lines.extend(
            [
                f"### Figure {number}",
                "",
                f"![Figure {number}]({relative.as_posix()})",
                "",
                f"*{FIGURE_CAPTIONS[number]}*",
                "",
            ]
        )
    lines.extend(
        [
            "## Methodological notes",
            "",
            "- EOFs are calculated from the correlation matrix of the 24 published LEC terms, separately by primary phase and for the cyclone-mean total lifecycle.",
            "- EOF signs are oriented so that the largest-magnitude loading is positive; the sign itself has no physical meaning.",
            "- Positive/negative EOF maps use upper/lower PC deciles and assign each selected cyclone to the most extreme of EOFs 1-4.",
            "- Intense groups use the original six terms (Ck, Ca, Ke, Ge, BKe and BAe) across four phases without feature scaling. The implementation is deterministic (30 K-means++ restarts, seed 42).",
            "- Density maps use a two-degree histogram followed by a Gaussian smoother; this replaces the legacy BallTree implementation while preserving the plotted scientific quantity and avoiding an unnecessary scikit-learn dependency.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corrected-cache", type=Path, required=True)
    parser.add_argument("--tracks", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    root = args.output_root.resolve()
    figures_dir = root / "figures" / "paired_control" / "article_style"
    results_dir = root / "results" / "paired_control" / "article_style"
    docs_dir = root / "docs"
    figures_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    cache, tracks = load_inputs(args.corrected_cache, args.tracks)
    stats = phase_statistics(cache)
    phase_loadings, phase_variance, phase_scores = eof_by_phase(cache)
    total_loadings, total_variance, total_scores = total_eof(cache)
    assignments = assign_eof_extremes(total_scores)
    first = first_track_rows(tracks)
    cluster_assignments, cluster_centers, cluster_meta = intense_clusters(cache, tracks, k=4)

    fig01(tracks, figure_stem(figures_dir, 1, "track_density"))
    fig02(figure_stem(figures_dir, 2, "lec_reference"))
    fig03(cache, figure_stem(figures_dir, 3, "term_pdfs"))
    fig04(stats, figure_stem(figures_dir, 4, "phase_mean_lec"))
    for mode in range(1, 5):
        fig_eof(mode, phase_loadings, phase_variance,
                figure_stem(figures_dir, mode + 4, f"eof{mode}_lec"))
    fig_eof_density("positive", assignments, tracks, figure_stem(figures_dir, 9, "eof_positive_density"))
    fig_eof_density("negative", assignments, tracks, figure_stem(figures_dir, 10, "eof_negative_density"))
    fig11(assignments, first, figure_stem(figures_dir, 11, "eof_genesis_season"))
    fig12(cache, cluster_assignments, figure_stem(figures_dir, 12, "intense_group_lec"))
    fig13(tracks, cluster_assignments, figure_stem(figures_dir, 13, "intense_group_density"))
    cluster_stats = fig14(cluster_assignments, tracks, first,
                          figure_stem(figures_dir, 14, "intense_group_characteristics"))
    fig15(stats, figure_stem(figures_dir, 15, "phase_synthesis"))
    fig16(phase_loadings, phase_variance, figure_stem(figures_dir, 16, "eof_synthesis"))

    stats.to_csv(results_dir / "phase_statistics.csv", index=False, float_format="%.8g")
    phase_loadings.to_csv(results_dir / "eof_loadings_by_phase.csv", index=False, float_format="%.8g")
    phase_variance.to_csv(results_dir / "eof_variance_by_phase.csv", index=False, float_format="%.8g")
    phase_scores.to_csv(results_dir / "eof_scores_by_phase.csv", index=False, float_format="%.8g")
    total_loadings.to_csv(results_dir / "eof_loadings_total.csv", index=False, float_format="%.8g")
    total_variance.to_csv(results_dir / "eof_variance_total.csv", index=False, float_format="%.8g")
    total_scores.to_csv(results_dir / "eof_scores_total.csv", index=False, float_format="%.8g")
    assignments.to_csv(results_dir / "eof_extreme_assignments.csv", index=False, float_format="%.8g")
    cluster_assignments.to_csv(results_dir / "intense_cluster_assignments.csv", index=False)
    pd.DataFrame(cluster_centers).to_csv(results_dir / "intense_cluster_centers.csv", index=False, float_format="%.8g")
    cluster_stats.to_csv(results_dir / "intense_cluster_statistics.csv", index=False, float_format="%.8g")
    write_json(results_dir / "intense_cluster_metadata.json", cluster_meta)

    manifest_rows = []
    for number in range(1, 17):
        png = sorted(figures_dir.glob(f"fig_{number:02d}_*.png"))[0]
        pdf = png.with_suffix(".pdf")
        manifest_rows.append(
            {
                "figure": number,
                "caption": FIGURE_CAPTIONS[number],
                "png": str(png.relative_to(root)),
                "pdf": str(pdf.relative_to(root)),
                "png_sha256": sha256_file(png),
                "pdf_sha256": sha256_file(pdf),
            }
        )
    pd.DataFrame(manifest_rows).to_csv(results_dir / "figure_manifest.csv", index=False)

    provenance = {
        "workflow": "corrected reproduction of article Figures 1-16",
        "repository_commit_before_generation": git_head(root),
        "corrected_cache": str(args.corrected_cache.resolve()),
        "corrected_cache_sha256": sha256_file(args.corrected_cache),
        "tracks": str(args.tracks.resolve()),
        "tracks_sha256": sha256_file(args.tracks),
        "corrected_cyclones": int(cache["track_id"].nunique()),
        "primary_phase_rows": int(len(cache)),
        "phases": PHASES,
        "toolkit_commit": "d38cda7e37d8e8a3a937a5919640a94bef19e34a",
        "toolkit_correction_commit": "d07707767c2962fed0475ff4573e7d15a97f8c69",
        "figure_count": 16,
        "notes": "Secondary lifecycle periods are retained upstream but excluded from the four-phase main-article reproduction.",
    }
    write_json(results_dir / "provenance.json", provenance)
    write_report_markdown(
        docs_dir / "paired_control" / "lec_climatology_paired_article_style_report.md",
        cache, stats, phase_variance, assignments, cluster_meta, cluster_stats,
    )
    print(json.dumps({"figures": 16, "cyclones": 3820, "output": str(root)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
