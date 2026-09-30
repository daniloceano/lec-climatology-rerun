#!/usr/bin/env python3
"""Render the 16 article figures in the publication layout with corrected data."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
import xarray as xr  # noqa: E402
from PIL import Image  # noqa: E402
from sklearn.cluster import KMeans  # noqa: E402
from sklearn.neighbors import KernelDensity  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY))

from scripts.article_figures.downstream_guards import require_resolved_figure16

from scripts.article_figures.common import (  # noqa: E402
    BOUNDARY_TERMS,
    CONVERSION_TERMS,
    ENERGY_TERMS,
    EOF_TERMS,
    GENERATION_TERMS,
    PHASES,
    PRESSURE_TERMS,
    TENDENCY_TERMS,
    assign_published_eof_extremes,
    eof_by_phase,
    first_track_rows,
    load_inputs,
    phase_statistics,
    sha256_file,
    total_eof,
)
from scripts.article_figures.legacy_source import load_definitions  # noqa: E402
from scripts.article_figures.phase_eofs import (  # noqa: E402
    load_pinned_phase_inputs, matched_phase_eofs, read_phase_product, write_phase_product,
)


DEFAULT_CONFIG = REPOSITORY / "config" / "data_sources.toml"
FIGURE_NAMES = {
    1: "fig_01_track_density.png",
    2: "fig_02_lec_reference.png",
    3: "fig_03_term_pdfs.png",
    4: "fig_04_phase_mean_lec.png",
    5: "fig_05_eof1_lec.png",
    6: "fig_06_eof2_lec.png",
    7: "fig_07_eof3_lec.png",
    8: "fig_08_eof4_lec.png",
    9: "fig_09_eof_positive_density.png",
    10: "fig_10_eof_negative_density.png",
    11: "fig_11_eof_genesis_season.png",
    12: "fig_12_intense_clusters_lec.png",
    13: "fig_13_intense_groups_density.png",
    14: "fig_14_intense_groups_characteristics.png",
    15: "fig_15_phase_synthesis.png",
    16: "fig_16_eof_synthesis.png",
}


def git_head() -> str:
    return subprocess.check_output(
        ["git", "-C", str(REPOSITORY), "rev-parse", "HEAD"], text=True
    ).strip()


def read_config(path: Path) -> dict:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def resolve_repo_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else REPOSITORY / path


def verify_input(path: Path, specification: dict) -> None:
    if not path.is_file():
        raise FileNotFoundError(
            f"missing authoritative input {path}; run scripts/sync_swell_inputs.py"
        )
    if path.stat().st_size != specification["size_bytes"]:
        raise ValueError(f"unexpected byte size for {path}")
    actual = sha256_file(path)
    if actual != specification["sha256"]:
        raise ValueError(f"unexpected SHA-256 for {path}: {actual}")


def raw_corrected_cache(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    missing = sorted({"track_id", "period", "phase", *EOF_TERMS} - set(frame.columns))
    if missing:
        raise ValueError(f"corrected cache misses columns: {missing}")
    frame["track_id"] = pd.to_numeric(frame["track_id"], errors="raise").astype("int64")
    if len(frame) != 15829 or frame["track_id"].nunique() != 3820:
        raise ValueError(
            f"expected 15,829 corrected rows for 3,820 cyclones; got "
            f"{len(frame):,} rows for {frame['track_id'].nunique():,} cyclones"
        )
    return frame


def save_raster_pdf(png: Path) -> Path:
    pdf = png.with_suffix(".pdf")
    with Image.open(png) as image:
        image.convert("RGB").save(pdf, "PDF", resolution=300.0)
    return pdf


def render_term_pdfs(cache: pd.DataFrame, output: Path) -> None:
    groups = [
        ("Energy Terms", ENERGY_TERMS, (0, 1e6), "upper right"),
        ("Conversion Terms", CONVERSION_TERMS, (-10, 10), "upper right"),
        ("Boundary Terms", BOUNDARY_TERMS, (-15, 15), "upper right"),
        ("Pressure Work Terms", PRESSURE_TERMS, (-10, 10), "upper right"),
        ("Generation/Residual Terms", GENERATION_TERMS, (-20, 10), "best"),
        ("Budget Terms", TENDENCY_TERMS, (-5, 5), "best"),
    ]
    colors = ["#3B95BF", "#87BF4B", "#BFAB37", "#BF3D3B", "#873e23", "#A13BF0"]
    mean_data = cache.groupby("track_id", sort=True)[EOF_TERMS].mean()
    figure, axes = plt.subplots(2, 3, figsize=(12, 8))
    for index, (title, terms, limits, legend_position) in enumerate(groups):
        ax = axes[index // 3, index % 3]
        for term_index, term in enumerate(terms):
            values = mean_data[term].dropna().copy()
            scale_by_ten = "Kz" in term or term == "BΦZ"
            if scale_by_ten:
                values = values / 10
            label = term if "∂" not in term else term.split("(finite diff.)")[0]
            if scale_by_ten:
                label += "*"
            sns.kdeplot(
                x=values,
                label=label,
                ax=ax,
                bw_adjust=0.5,
                fill=False,
                color=colors[term_index],
                linewidth=2,
                alpha=0.8,
            )
        ax.set_xlim(limits)
        if title != "Energy Terms":
            ax.axvline(0, color="gray", linestyle="--", linewidth=1, zorder=0)
        ax.legend(fontsize=12, loc=legend_position)
        ax.set_title(f"({chr(65 + index)}) {title}", fontsize=16)
        ax.tick_params(axis="both", which="major", labelsize=12)
        ax.set_xlabel("")
        ax.set_ylabel("")
    plt.tight_layout()
    figure.savefig(output, bbox_inches="tight")
    plt.close(figure)


def assemble_panel(
    image_files: list[Path],
    output: Path,
    *,
    figsize: tuple[float, float],
    grid: tuple[int, int],
    label_y: float,
    cluster_panel: bool = False,
    show_labels: bool = True,
) -> None:
    images = [Image.open(path) for path in image_files]
    try:
        figure, axes = plt.subplots(*grid, figsize=figsize)
        flat = np.asarray(axes).flatten()
        for ax, image, label in zip(flat, images, ["(A)", "(B)", "(C)", "(D)", "(E)"]):
            ax.imshow(image)
            ax.axis("off")
            if cluster_panel and label == "(A)":
                ax.add_patch(
                    patches.Rectangle(
                        (0.4, 0.4), 0.2, 0.2, linewidth=2,
                        edgecolor="white", facecolor="white", transform=ax.transAxes,
                    )
                )
            if show_labels:
                ax.text(
                    0.5, label_y, label, transform=ax.transAxes, fontsize=16,
                    ha="center", va="center", color="black", fontweight="bold",
                )
            if cluster_panel and label == "(A)":
                ax.text(
                    0.5, 0.47, "All Systems\nMean ± Std", transform=ax.transAxes,
                    fontsize=8, ha="center", va="center", color="black", fontweight="bold",
                )
        for ax in flat[len(images):]:
            ax.axis("off")
        plt.tight_layout()
        figure.savefig(output)
        plt.close(figure)
    finally:
        for image in images:
            image.close()


def patch_eof_box_renderer(module) -> None:
    def plot_boxes(ax, data, positions, size):
        for term, pos in positions.items():
            value = data[term]
            color = "#386641" if value >= 0 else "#ae2012"
            ax.add_patch(
                patches.Rectangle(
                    (pos[0] - size / 2, pos[1] - size / 2), size, size,
                    fill=True, color="skyblue", ec="black",
                    linewidth=0.5 * abs(value),
                )
            )
            ax.text(
                pos[0], pos[1] + 0.07, term, ha="center", va="center",
                fontsize=16, color="black", fontweight="bold",
            )
            ax.text(
                pos[0], pos[1] - 0.05, f"{value:.2f}", ha="center", va="center",
                fontsize=16, color=color, fontweight="bold",
            )

    module._call_plot.__globals__["plot_boxes"] = plot_boxes


def render_phase_and_eof_diagrams(
    legacy_root: Path,
    primary: pd.DataFrame,
    stats: pd.DataFrame,
    loadings: pd.DataFrame,
    variance: pd.DataFrame,
    figures: Path,
    scratch: Path,
) -> tuple[object, object]:
    lec_std = load_definitions(legacy_root / "plot_LEC_std.py", skip_imports={"pdfs"})

    mean = stats.pivot(index="phase", columns="term", values="mean").reindex(PHASES)
    std = stats.pivot(index="phase", columns="term", values="std").reindex(PHASES)
    phase_dir = scratch / "phase"
    lec_std.plot_lorenzcycletoolkit_with_std(mean, std, str(phase_dir))
    phase_images = [phase_dir / "LEC_std" / f"LEC_{phase}.png" for phase in PHASES]
    assemble_panel(
        phase_images, figures / FIGURE_NAMES[4], figsize=(10, 10),
        grid=(2, 2), label_y=0.55,
    )

    render_eof_diagrams(legacy_root, loadings, variance, figures, scratch)
    return lec_std, mean


def render_eof_diagrams(
    legacy_root: Path, loadings: pd.DataFrame, variance: pd.DataFrame,
    figures: Path, scratch: Path,
) -> None:
    """Figures 5–8 only; input identities must already be reference-matched.

    Frozen publication renderer receives a temporary zero-based variance view.
    Raw ranks/signs remain explicit in the source tables and figure manifest.
    """
    for frame in (loadings, variance):
        if not {"reference_eof", "raw_rank", "sign_alignment"}.issubset(frame.columns) or "eof" in frame:
            raise ValueError("Figures 5–8 require reference-matched EOF tables")
        if not frame.version.eq("after").all():
            raise ValueError("corrected-only renderer requires the after view")
    lec_eof = load_definitions(legacy_root / "plot_LEC_eofs.py")
    patch_eof_box_renderer(lec_eof)
    eof_dir = scratch / "eof"
    eof_dir.mkdir(parents=True, exist_ok=True)
    variance_table = variance.pivot(index="scope", columns="reference_eof", values="explained_variance_pct")
    # The frozen renderer uses zero-based EOF column labels internally even
    # though its displayed titles and output filenames are one-based.
    variance_table.columns = variance_table.columns.astype(int) - 1
    for mode in range(1, 5):
        table = (
            loadings[loadings["reference_eof"] == mode]
            .pivot(index="scope", columns="term", values="loading")
            .reindex(PHASES)
        )
        lec_eof.plot_lorenzcycletoolkit_eof(table, variance_table, mode - 1, str(eof_dir))
        images = [eof_dir / f"LEC_EOF{mode}_{phase}.png" for phase in PHASES]
        assemble_panel(
            images, figures / FIGURE_NAMES[mode + 4], figsize=(10, 10),
            grid=(2, 2), label_y=0.60,
        )


def compute_haversine_density(tracks: pd.DataFrame, months: int):
    k = 64
    longitude = np.linspace(-180, 180, 2 * k)
    latitude = np.linspace(-87.863, 87.863, k)
    tx, ty = np.meshgrid(longitude, latitude)
    mesh = np.vstack((ty.ravel(), tx.ravel())).T * np.pi / 180.0
    positions = tracks[["lat vor", "lon vor"]].dropna().to_numpy() * np.pi / 180.0
    if not len(positions):
        raise ValueError("cannot compute density for an empty track group")
    kde = KernelDensity(
        bandwidth=0.05, metric="haversine", kernel="gaussian", algorithm="ball_tree"
    ).fit(positions)
    values = np.exp(kde.score_samples(mesh)).reshape((k, 2 * k))
    radius_km = 6369345.0 * 1e-3
    density = values * len(positions) * (1 / radius_km**2) * 1e6 / months
    return density, longitude, latitude


def render_density_maps(
    legacy_root: Path,
    assignments: pd.DataFrame,
    clusters: pd.DataFrame,
    tracks: pd.DataFrame,
    figures: Path,
    scratch: Path,
) -> None:
    eof_renderer = load_definitions(legacy_root / "map_density_eof.py")
    cluster_renderer = load_definitions(legacy_root / "map_density_intense.py")
    eof_months = tracks["date"].dt.to_period("M").nunique()
    for sign, suffix, figure_number in (
        ("positive", "q90", 9),
        ("negative", "q10", 10),
    ):
        density_dir = scratch / f"density_{suffix}"
        density_dir.mkdir(parents=True)
        selected = assignments[assignments["sign"] == sign]
        for mode in range(1, 5):
            ids = set(selected.loc[selected["dominant_eof"] == mode, "track_id"].astype(int))
            density, longitude, latitude = compute_haversine_density(
                tracks[tracks["track_id"].isin(ids)], eof_months
            )
            # The article used fixed contour bounds. Corrected extrema above
            # the last bound belong to the top color class rather than an
            # unfilled over-range hole.
            top_level = {
                "q90": {1: 18, 2: 9, 3: 9, 4: 5.5},
                "q10": {1: 25, 2: 10, 3: 10, 4: 10},
            }[suffix][mode]
            density = np.minimum(density, top_level)
            data = xr.DataArray(
                density,
                coords={"lon": longitude, "lat": latitude},
                dims=["lat", "lon"],
                name=f"EOF_{float(mode)}",
            )
            data.to_netcdf(density_dir / f"SAt_track_density_eof_{mode}.nc")
        output_dir = scratch / f"panel_{suffix}"
        eof_renderer.generate_density_panel(str(density_dir), str(output_dir), suffix)
        shutil.copy2(output_dir / f"density_panel_{suffix}.png", figures / FIGURE_NAMES[figure_number])

    cluster_tracks = tracks[tracks["track_id"].isin(clusters["track_id"])].copy()
    cluster_months = cluster_tracks["date"].dt.to_period("M").nunique()
    density_dir = scratch / "density_clusters"
    density_dir.mkdir(parents=True)
    for cluster in range(1, 5):
        ids = set(clusters.loc[clusters["cluster"] == cluster, "track_id"].astype(int))
        density, longitude, latitude = compute_haversine_density(
            tracks[tracks["track_id"].isin(ids)], cluster_months
        )
        data = xr.DataArray(
            density,
            coords={"lon": longitude, "lat": latitude},
            dims=["lat", "lon"],
            name=f"Cluster {cluster}",
        )
        data.to_netcdf(density_dir / f"track_density_cluster_{cluster}.nc")
    output_dir = scratch / "panel_clusters"
    cluster_renderer.generate_density_panel(str(density_dir), str(output_dir))
    shutil.copy2(output_dir / "density_panel.png", figures / FIGURE_NAMES[13])


def render_eof_statistics(
    assignments: pd.DataFrame, first: pd.DataFrame, output: Path
) -> None:
    sns.set_context("notebook", font_scale=1.5)
    sns.set_style("whitegrid")
    season_colors = {"JJA": "#5975A4", "MAM": "#CC8963", "DJF": "#B55D60", "SON": "#5F9E6E"}
    data = {}
    for sign, suffix in (("positive", "q90"), ("negative", "q10")):
        merged = assignments[assignments["sign"] == sign].merge(
            first[["track_id", "region", "season"]], on="track_id", how="left"
        )
        region_counts = merged.groupby(["dominant_eof", "region"]).size().reset_index(name="count")
        region_counts["proportion"] = 100 * region_counts["count"] / region_counts.groupby("dominant_eof")["count"].transform("sum")
        proportion = (
            region_counts.pivot(index="dominant_eof", columns="region", values="proportion")
            .reindex(index=range(1, 5), columns=["ARG", "LA-PLATA", "SE-BR"])
            .fillna(0)
        )
        seasonal = merged.groupby(["dominant_eof", "season"]).size().reset_index(name="count")
        seasonal["season"] = pd.Categorical(
            seasonal["season"], categories=["DJF", "MAM", "JJA", "SON"], ordered=True
        )
        seasonal["frequency"] = 100 * seasonal["count"] / seasonal.groupby("dominant_eof")["count"].transform("sum")
        data[suffix] = (proportion, seasonal)

    figure, axes = plt.subplots(2, 2, figsize=(18, 12))
    for row, suffix in enumerate(("q90", "q10")):
        proportion, seasonal = data[suffix]
        melted = proportion.reset_index().melt(
            id_vars="dominant_eof", var_name="region", value_name="proportion"
        )
        sns.barplot(
            data=melted, x="dominant_eof", y="proportion", hue="region",
            palette="deep", ax=axes[row, 0],
        )
        label = "EOF(+)" if suffix == "q90" else "EOF(-)"
        axes[row, 0].set_title(
            f"({chr(65 + row * 2)}) Genesis Proportion - {label}",
            fontsize=20, fontweight="bold",
        )
        axes[row, 0].set_xlabel("EOF", fontsize=18)
        axes[row, 0].set_ylabel("Proportion (%)", fontsize=18)
        axes[row, 0].tick_params(axis="both", labelsize=16)
        sns.barplot(
            data=seasonal, x="dominant_eof", y="frequency", hue="season",
            palette=season_colors, ax=axes[row, 1],
        )
        axes[row, 1].set_title(
            f"({chr(66 + row * 2)}) Seasonal Occurrences - {label}",
            fontsize=20, fontweight="bold",
        )
        axes[row, 1].set_xlabel("EOF", fontsize=18)
        axes[row, 1].set_ylabel("Frequency (%)", fontsize=18)
        axes[row, 1].tick_params(axis="both", labelsize=16)
        if row == 1:
            axes[row, 0].legend(
                title=None, fontsize=14, bbox_to_anchor=(0.2, -0.15), loc="upper left", ncol=3
            )
            axes[row, 1].legend(
                title=None, fontsize=14, bbox_to_anchor=(0.2, -0.15), loc="upper left", ncol=4
            )
        else:
            axes[row, 0].legend_.remove()
            axes[row, 1].legend_.remove()
    plt.tight_layout()
    figure.savefig(output, dpi=300)
    plt.close(figure)


def article_clusters(
    total_scores: pd.DataFrame, tracks: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    maximum = tracks.groupby("track_id")["vor42"].max()
    threshold = float(maximum.quantile(0.90))
    intense_ids = set(maximum[maximum >= threshold].index.astype(int))
    columns = [f"PC{mode}" for mode in range(1, 9)]
    selected = total_scores[total_scores["track_id"].isin(intense_ids)].copy()
    scaler = StandardScaler()
    standardized = scaler.fit_transform(selected[columns])
    model = KMeans(n_clusters=4, random_state=42, n_init=10)
    selected["cluster"] = model.fit_predict(standardized) + 1
    assignments = selected[["track_id", "cluster"]].copy()
    centers = pd.DataFrame(scaler.inverse_transform(model.cluster_centers_), columns=columns)
    centers.insert(0, "cluster", range(1, 5))
    metadata = {
        "method": "article PC clustering: StandardScaler + KMeans",
        "maximum_vorticity_quantile": 0.90,
        "maximum_vorticity_threshold": threshold,
        "corrected_intense_cyclones": int(len(assignments)),
        "clusters": 4,
        "random_state": 42,
        "n_init": 10,
        "inertia": float(model.inertia_),
        "features": columns,
    }
    return assignments, centers, metadata


def cluster_statistics(
    clusters: pd.DataFrame, tracks: pd.DataFrame, first: pd.DataFrame
) -> pd.DataFrame:
    maximum = tracks.groupby("track_id")["vor42"].max().rename("max_vor42")
    merged = clusters.merge(first[["track_id", "region", "season"]], on="track_id").merge(
        maximum, on="track_id"
    )
    rows = []
    for cluster, block in merged.groupby("cluster"):
        row = {
            "cluster": int(cluster),
            "n": int(len(block)),
            "max_vor42_mean": float(block["max_vor42"].mean()),
            "max_vor42_median": float(block["max_vor42"].median()),
        }
        for season in ["DJF", "MAM", "JJA", "SON"]:
            row[f"season_{season}_pct"] = float(100 * (block["season"] == season).mean())
        for region in ["ARG", "LA-PLATA", "SE-BR"]:
            row[f"region_{region}_pct"] = float(100 * (block["region"] == region).mean())
        rows.append(row)
    return pd.DataFrame(rows).sort_values("cluster")


def render_cluster_lecs(
    lec_std,
    cache: pd.DataFrame,
    clusters: pd.DataFrame,
    output: Path,
    scratch: Path,
) -> None:
    per_track = cache.groupby("track_id", sort=True)[EOF_TERMS].mean()
    all_mean = per_track.mean().to_frame().T
    all_mean.index = ["total"]
    all_std = per_track.std(ddof=1).to_frame().T
    all_std.index = ["total"]
    all_dir = scratch / "cluster_all"
    lec_std.plot_lorenzcycletoolkit_with_std(all_mean, all_std, str(all_dir))

    means = []
    deviations = []
    for cluster in range(1, 5):
        ids = clusters.loc[clusters["cluster"] == cluster, "track_id"]
        block = per_track.loc[per_track.index.intersection(ids)]
        means.append(block.mean().rename(f"Cluster {cluster}"))
        deviations.append(block.std(ddof=1).rename(f"Cluster {cluster}"))
    cluster_dir = scratch / "cluster_groups"
    lec_std.plot_lorenzcycletoolkit_with_std(
        pd.DataFrame(means), pd.DataFrame(deviations), str(cluster_dir)
    )
    images = [all_dir / "LEC_std" / "LEC_total.png"] + [
        cluster_dir / "LEC_std" / f"LEC_Cluster {cluster}.png" for cluster in range(1, 5)
    ]
    assemble_panel(
        images, output, figsize=(15, 10), grid=(2, 3),
        label_y=0.55, cluster_panel=True,
    )


def render_cluster_statistics(
    clusters: pd.DataFrame,
    tracks: pd.DataFrame,
    first: pd.DataFrame,
    output: Path,
) -> pd.DataFrame:
    sns.set_context("notebook", font_scale=1.5)
    sns.set_style("whitegrid")
    season_colors = {"JJA": "#5975A4", "MAM": "#CC8963", "DJF": "#B55D60", "SON": "#5F9E6E"}
    region_colors = {
        "ARG": season_colors["JJA"], "LA-PLATA": season_colors["MAM"],
        "SE-BR": season_colors["SON"],
    }
    maximum = tracks.groupby("track_id")["vor42"].max().rename("vor42")
    merged = clusters.merge(first[["track_id", "region", "season"]], on="track_id").merge(
        maximum, on="track_id"
    )
    counts = merged["cluster"].value_counts().sort_index().reindex(range(1, 5), fill_value=0)
    seasonal = merged.groupby(["cluster", "season"]).size().unstack(fill_value=0)
    seasonal = seasonal.reindex(index=range(1, 5), columns=["DJF", "JJA", "MAM", "SON"], fill_value=0)
    seasonal = seasonal.div(seasonal.sum(axis=1), axis=0) * 100
    genesis = merged.groupby(["cluster", "region"]).size().unstack(fill_value=0)
    genesis = genesis.reindex(index=range(1, 5), columns=["ARG", "LA-PLATA", "SE-BR"], fill_value=0)
    genesis = genesis.div(genesis.sum(axis=1), axis=0) * 100

    figure, axes = plt.subplots(2, 2, figsize=(18, 12))
    sns.barplot(x=counts.index, y=counts.values, ax=axes[0, 0], palette="deep")
    axes[0, 0].set_title("(A) Count of Systems", fontsize=20, fontweight="bold")
    for index, value in enumerate(counts.values):
        axes[0, 0].text(index, value + 2, str(value), ha="center", fontsize=16, fontweight="bold")
    axes[0, 0].set_xlabel("Cluster", fontsize=18)
    axes[0, 0].set_ylabel("Number of Systems", fontsize=18)
    axes[0, 0].tick_params(axis="both", labelsize=16)

    sns.boxplot(data=merged, x="cluster", y="vor42", ax=axes[0, 1], palette="deep")
    axes[0, 1].set_title("(B) Maximum Intensity", fontsize=20, fontweight="bold")
    axes[0, 1].set_xlabel("Cluster", fontsize=18)
    axes[0, 1].set_ylabel(r"Maximum $\zeta_{850}$ ($-10^{-5}$ s$^{-1}$)", fontsize=18)
    axes[0, 1].tick_params(axis="both", labelsize=16)

    seasonal.plot(kind="bar", ax=axes[1, 0], color=season_colors)
    axes[1, 0].set_title("(C) Seasonality of Systems", fontsize=20, fontweight="bold")
    axes[1, 0].set_xlabel("Cluster", fontsize=18)
    axes[1, 0].set_ylabel("Frequency of Occurrence (%)", fontsize=18)
    axes[1, 0].tick_params(axis="x", labelsize=16, rotation=0)
    axes[1, 0].tick_params(axis="y", labelsize=16)
    axes[1, 0].legend(title=False, fontsize=14, title_fontsize=14, ncol=2)

    genesis.plot(
        kind="bar", ax=axes[1, 1],
        color=[region_colors.get(region, "gray") for region in genesis.columns],
    )
    axes[1, 1].set_title("(D) Genesis Region Distribution", fontsize=20, fontweight="bold")
    axes[1, 1].set_xlabel("Cluster", fontsize=18)
    axes[1, 1].set_ylabel("Frequency by Genesis Region", fontsize=18)
    axes[1, 1].tick_params(axis="x", labelsize=16, rotation=0)
    axes[1, 1].tick_params(axis="y", labelsize=16)
    axes[1, 1].legend(title=False, fontsize=14, title_fontsize=14, ncol=2)
    plt.tight_layout()
    figure.savefig(output, dpi=300)
    plt.close(figure)
    return cluster_statistics(clusters, tracks, first)


def render_syntheses(
    legacy_root: Path,
    phase_means: pd.DataFrame,
    loadings: pd.DataFrame,
    figures: Path,
    scratch: Path,
) -> None:
    require_resolved_figure16()
    draw = load_definitions(legacy_root / "tests_draw_lec" / "draw_lec_v6.py")
    total_dir = scratch / "synthesis"
    draw.plot_lorenzcycletoolkit(phase_means, str(total_dir), normalization_type="log")
    shutil.copy2(total_dir / "draw_LEC" / "LEC_total_v6.png", figures / FIGURE_NAMES[15])

    eof_images = []
    eof_dir = scratch / "synthesis_eofs"
    eof_dir.mkdir(parents=True)
    for mode in range(1, 5):
        table = (
            loadings[loadings["eof"] == mode]
            .pivot(index="scope", columns="term", values="loading")
            .reindex(PHASES)
            .apply(pd.to_numeric, errors="raise")
        )
        draw.plot_period_means(table, "min_max")
        plt.text(
            0.51, 0.9, f"EOF {mode}", transform=plt.gcf().transFigure,
            fontsize=20, ha="center", va="center", fontweight="bold",
        )
        path = eof_dir / f"LEC_eof_{mode}.png"
        plt.savefig(path)
        plt.close()
        eof_images.append(path)
    assemble_panel(
        eof_images, figures / FIGURE_NAMES[16], figsize=(9.5, 9.5),
        grid=(2, 2), label_y=0.5, show_labels=False,
    )


def validate_layout(figures: Path, originals: Path, numbers=None) -> list[dict]:
    rows = []
    for number, filename in FIGURE_NAMES.items():
        if numbers is not None and number not in numbers:
            continue
        corrected = figures / filename
        original = originals / filename
        if not corrected.is_file() or not original.is_file():
            raise FileNotFoundError(f"missing figure pair for Figure {number}")
        with Image.open(original) as before:
            target_size = before.size
        with Image.open(corrected) as after:
            if after.size != target_size:
                difference = (after.width - target_size[0], after.height - target_size[1])
                # Matplotlib's tight-bbox rounding varies by one or two pixels
                # between patch releases. Remove only that outer raster edge;
                # scientific content and axes geometry are left untouched.
                if not (0 <= difference[0] <= 2 and 0 <= difference[1] <= 2):
                    raise ValueError(
                        f"Figure {number} layout dimensions differ: {after.size} != {target_size}"
                    )
                left = difference[0] // 2
                top = difference[1] // 2
                cropped = after.crop(
                    (left, top, left + target_size[0], top + target_size[1])
                )
                cropped.save(corrected)
        with Image.open(corrected) as after, Image.open(original) as before:
            if after.size != before.size:
                raise ValueError(f"Figure {number} dimension normalization failed")
            dimensions = f"{after.width}x{after.height}"
        pdf = save_raster_pdf(corrected)
        rows.append(
            {
                "figure": number,
                "png": str(corrected.relative_to(REPOSITORY)),
                "pdf": str(pdf.relative_to(REPOSITORY)),
                "dimensions_px": dimensions,
                "layout_dimensions_match_article": True,
                "png_sha256": sha256_file(corrected),
                "pdf_sha256": sha256_file(pdf),
                "published_png_sha256": sha256_file(original),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    require_resolved_figure16()
    config = read_config(args.config)

    cache_path = resolve_repo_path(config["inputs"]["corrected_cache"]["local"])
    tracks_path = resolve_repo_path(config["inputs"]["tracks"]["local"])
    verify_input(cache_path, config["inputs"]["corrected_cache"])
    verify_input(tracks_path, config["inputs"]["tracks"])
    legacy_root = resolve_repo_path(config["article"]["legacy_source_root"])
    if not legacy_root.is_dir():
        raise FileNotFoundError(f"missing frozen manuscript source: {legacy_root}")

    originals = resolve_repo_path(config["article"]["published_figure_root"])
    figures = resolve_repo_path(config["article"]["corrected_figure_root"])
    results = resolve_repo_path(config["article"]["corrected_results_root"])
    figures.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    raw = raw_corrected_cache(cache_path)
    primary, tracks = load_inputs(cache_path, tracks_path)
    stats = phase_statistics(primary)
    raw_phase_loadings, raw_phase_variance, _ = eof_by_phase(primary)
    legacy, corrected, _ = load_pinned_phase_inputs(REPOSITORY, cache_path)
    loadings, variance, phase_scores = matched_phase_eofs(legacy, corrected)
    write_phase_product(REPOSITORY, loadings, variance)
    loadings, variance = read_phase_product(REPOSITORY)
    loadings = loadings[loadings.version.eq("after")].copy()
    variance = variance[variance.version.eq("after")].copy()
    total_loadings, total_variance, total_scores = total_eof(raw)
    assignments = assign_published_eof_extremes(total_scores, n_modes=8, keep_modes=4)
    clusters, cluster_centers, cluster_metadata = article_clusters(total_scores, tracks)
    first = first_track_rows(tracks)

    # Figures 1-2 do not depend on corrected LEC quantities.
    for number in (1, 2):
        shutil.copy2(originals / FIGURE_NAMES[number], figures / FIGURE_NAMES[number])
    render_term_pdfs(raw, figures / FIGURE_NAMES[3])

    (REPOSITORY / "tmp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="corrected-article-", dir=REPOSITORY / "tmp") as temporary:
        scratch = Path(temporary)
        lec_std, phase_means = render_phase_and_eof_diagrams(
            legacy_root, primary, stats, loadings, variance, figures, scratch
        )
        render_density_maps(
            legacy_root, assignments, clusters, tracks, figures, scratch
        )
        render_eof_statistics(assignments, first, figures / FIGURE_NAMES[11])
        render_cluster_lecs(
            lec_std, raw, clusters, figures / FIGURE_NAMES[12], scratch
        )
        cluster_stats = render_cluster_statistics(
            clusters, tracks, first, figures / FIGURE_NAMES[14]
        )
        # Figure 16 deliberately retains its raw-phase definition.
        render_syntheses(legacy_root, phase_means, raw_phase_loadings, figures, scratch)

    manifest = validate_layout(figures, originals)
    pd.DataFrame(manifest).to_csv(results / "figure_manifest.csv", index=False)
    stats.to_csv(results / "phase_statistics.csv", index=False, float_format="%.8g")
    loadings.to_csv(results / "eof_loadings_by_phase.csv", index=False, float_format="%.8g")
    variance.to_csv(results / "eof_variance_by_phase.csv", index=False, float_format="%.8g")
    phase_scores.to_csv(results / "eof_scores_by_phase.csv", index=False, float_format="%.8g")
    raw_phase_loadings.rename(columns={"eof": "raw_rank"}).to_csv(
        results / "eof_loadings_by_phase_raw.csv", index=False, float_format="%.8g"
    )
    raw_phase_variance.rename(columns={"eof": "raw_rank"}).to_csv(
        results / "eof_variance_by_phase_raw.csv", index=False, float_format="%.8g"
    )
    total_loadings.to_csv(results / "eof_loadings_total.csv", index=False, float_format="%.8g")
    total_variance.to_csv(results / "eof_variance_total.csv", index=False, float_format="%.8g")
    total_scores.to_csv(results / "eof_scores_total.csv", index=False, float_format="%.8g")
    assignments.to_csv(results / "eof_extreme_assignments.csv", index=False, float_format="%.8g")
    clusters.to_csv(results / "intense_pc_cluster_assignments.csv", index=False)
    cluster_centers.to_csv(results / "intense_pc_cluster_centers.csv", index=False, float_format="%.8g")
    cluster_stats.to_csv(results / "intense_pc_cluster_statistics.csv", index=False, float_format="%.8g")
    (results / "intense_pc_cluster_metadata.json").write_text(
        json.dumps(cluster_metadata, indent=2, sort_keys=True) + "\n"
    )

    provenance = {
        "workflow": "corrected article reproduction with frozen publication layout",
        "phase_eofs": "Figures 5–8 use results/comparison/article/phase_eof_matched; reference_eof is the published identity, raw_rank is the corrected eigenvalue rank",
        "figure_16_phase_eofs": "raw phase loadings, preserved independently from Figures 5–8 matching",
        "repository_commit_before_generation": git_head(),
        "corrected_cache": config["inputs"]["corrected_cache"],
        "tracks": config["inputs"]["tracks"],
        "legacy_source_root": str(legacy_root),
        "legacy_source_hashes": {
            name: sha256_file(legacy_root / name)
            for name in [
                "pdfs.py", "plot_LEC_std.py", "plot_LEC_eofs.py",
                "map_density_eof.py", "map_density_intense.py",
                "eof_cyclone_statistics_q10_q90.py", "eof_cluster_statistics.py",
                "tests_draw_lec/draw_lec_v6.py", "tests_draw_lec/draw_lec_eofs.py",
            ]
        },
        "corrected_cyclones": int(primary["track_id"].nunique()),
        "corrected_lifecycle_rows": int(len(raw)),
        "primary_phase_rows": int(len(primary)),
        "figure_count": 16,
        "pixel_dimensions_match_published_article": True,
        "figures_1_and_2": "copied byte-for-byte because they contain no corrected LEC quantities",
        "figures_3_to_16": "publication renderers/layout with corrected cache and authoritative tracks",
        "credentials": "not read, copied, logged, or included",
    }
    (results / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                "figures": 16,
                "corrected_cyclones": 3820,
                "figure_directory": str(figures),
                "results_directory": str(results),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
