"""Publication-quality plotting primitives for the corrected article figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

BOXES = {
    "∂Az/∂t (finite diff.)": (-0.5, 0.5),
    "∂Kz/∂t (finite diff.)": (0.5, 0.5),
    "∂Ae/∂t (finite diff.)": (-0.5, -0.5),
    "∂Ke/∂t (finite diff.)": (0.5, -0.5),
}
BOX_LABELS = {
    "∂Az/∂t (finite diff.)": r"$\partial A_Z/\partial t$",
    "∂Kz/∂t (finite diff.)": r"$\partial K_Z/\partial t$",
    "∂Ae/∂t (finite diff.)": r"$\partial A_E/\partial t$",
    "∂Ke/∂t (finite diff.)": r"$\partial K_E/\partial t$",
}
ARROWS = {
    "Cz": ((-0.30, 0.50), (0.30, 0.50), (0.00, 0.66)),
    "Ca": ((-0.50, 0.30), (-0.50, -0.30), (-0.73, 0.00)),
    "Ck": ((0.50, -0.30), (0.50, 0.30), (0.73, 0.00)),
    "Ce": ((-0.30, -0.50), (0.30, -0.50), (0.00, -0.67)),
    "Gz": ((-0.50, 1.00), (-0.50, 0.70), (-0.50, 1.16)),
    "RKz": ((0.50, 1.00), (0.50, 0.70), (0.50, 1.16)),
    "Ge": ((-0.50, -1.00), (-0.50, -0.70), (-0.50, -1.10)),
    "RKe": ((0.50, -1.00), (0.50, -0.70), (0.50, -1.10)),
    "BAz": ((-1.00, 0.50), (-0.70, 0.50), (-0.88, 0.82)),
    "BAe": ((-1.00, -0.50), (-0.70, -0.50), (-0.88, -0.68)),
    "BKz": ((1.00, 0.50), (0.70, 0.50), (0.88, 0.82)),
    "BKe": ((1.00, -0.50), (0.70, -0.50), (0.88, -0.68)),
}
ARROW_LABELS = {
    "Cz": r"$C_Z$", "Ca": r"$C_A$", "Ck": r"$C_K$", "Ce": r"$C_E$",
    "Gz": r"$G_Z$", "Ge": r"$G_E$", "RKz": r"$R_{K_Z}$", "RKe": r"$R_{K_E}$",
    "BAz": r"$BA_Z$", "BAe": r"$BA_E$", "BKz": r"$BK_Z$", "BKe": r"$BK_E$",
}

BEFORE_COLOR = "#343434"
AFTER_COLOR = "#d62728"
COMPARE_OFFSET = 0.055


def save_pair(figure, stem: Path, *, dpi: int = 300) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(stem.with_suffix(".png"), dpi=dpi, bbox_inches="tight", facecolor="white")
    figure.savefig(stem.with_suffix(".pdf"), bbox_inches="tight", facecolor="white")
    plt.close(figure)


def _width(value: float, scale: str) -> float:
    if scale == "eof":
        return min(0.8 + 5.2 * abs(value), 5.5)
    return min(0.8 + 0.52 * abs(value), 5.5)


def draw_cycle(
    ax,
    values,
    *,
    title: str,
    uncertainty=None,
    color: str = "#4a4a45",
    scale: str = "terms",
    show_labels: bool = True,
) -> None:
    ax.set_xlim(-1.08, 1.08)
    ax.set_ylim(-1.26, 1.26)
    ax.set_aspect("equal")
    ax.axis("off")
    for term, (x, y) in BOXES.items():
        ax.add_patch(
            patches.Rectangle(
                (x - 0.20, y - 0.20), 0.40, 0.40,
                facecolor="#8ecae6", edgecolor="#36535f", linewidth=0.8,
            )
        )
        value = float(values.get(term, np.nan))
        text = f"{value:+.2f}"
        if uncertainty is not None and term in uncertainty:
            text += f"\n± {float(uncertainty[term]):.2f}"
        ax.text(x, y + 0.035, BOX_LABELS[term], ha="center", va="center", fontsize=7.5, fontweight="bold")
        ax.text(x, y - 0.075, text, ha="center", va="center", fontsize=6.8, color=("#2a6f3b" if value >= 0 else "#b3261e"), fontweight="bold")

    for term, (tail, head, label) in ARROWS.items():
        value = float(values.get(term, np.nan))
        if not np.isfinite(value):
            continue
        start, end = (tail, head) if value >= 0 else (head, tail)
        width = _width(value, scale)
        ax.annotate(
            "", xy=end, xytext=start,
            arrowprops=dict(
                facecolor=color, edgecolor=color, width=width,
                headwidth=max(3.2, width * 2.0), headlength=max(3.2, width * 2.0),
            ),
        )
        if show_labels:
            text = f"{ARROW_LABELS[term]}\n{value:+.2f}"
            if uncertainty is not None and term in uncertainty:
                text += f" ± {float(uncertainty[term]):.2f}"
            ax.text(label[0], label[1], text, ha="center", va="center", fontsize=6.7, fontweight="bold")
    ax.text(0, 0.06, title, ha="center", va="center", fontsize=9.5, fontweight="bold")


def _shift_arrow(point, tail, head, amount):
    if abs(tail[1] - head[1]) < 1e-9:
        return point[0], point[1] + amount
    return point[0] + amount, point[1]


def _format_value(value: float, uncertainty) -> str:
    text = f"{value:+.2f}"
    if uncertainty is not None and np.isfinite(uncertainty):
        text += f" ± {uncertainty:.2f}"
    return text


def draw_cycle_comparison(
    ax,
    before,
    after,
    *,
    title: str,
    before_uncertainty=None,
    after_uncertainty=None,
    scale: str = "terms",
    show_arrow_uncertainty: bool = False,
) -> None:
    """Four-box LEC with dark legacy arrows and red corrected arrows."""
    ax.set_xlim(-1.10, 1.10)
    ax.set_ylim(-1.29, 1.29)
    ax.set_aspect("equal")
    ax.axis("off")
    for term, (x, y) in BOXES.items():
        ax.add_patch(
            patches.Rectangle(
                (x - 0.20, y - 0.20), 0.40, 0.40,
                facecolor="#8ecae6", edgecolor="#36535f", linewidth=0.8,
            )
        )
        old = float(before.get(term, np.nan))
        new = float(after.get(term, np.nan))
        old_sd = None if before_uncertainty is None else float(before_uncertainty.get(term, np.nan))
        new_sd = None if after_uncertainty is None else float(after_uncertainty.get(term, np.nan))
        ax.text(x, y + 0.085, BOX_LABELS[term], ha="center", va="center", fontsize=7.2, fontweight="bold")
        ax.text(x, y - 0.015, _format_value(old, old_sd), ha="center", va="center",
                fontsize=6.2, color=BEFORE_COLOR, fontweight="bold")
        ax.text(x, y - 0.105, _format_value(new, new_sd), ha="center", va="center",
                fontsize=6.2, color=AFTER_COLOR, fontweight="bold")

    for term, (tail, head, label) in ARROWS.items():
        old = float(before.get(term, np.nan))
        new = float(after.get(term, np.nan))
        if not np.isfinite(old) or not np.isfinite(new):
            continue
        for value, color, offset in (
            (old, BEFORE_COLOR, -COMPARE_OFFSET),
            (new, AFTER_COLOR, COMPARE_OFFSET),
        ):
            start, end = (tail, head) if value >= 0 else (head, tail)
            start = _shift_arrow(start, tail, head, offset)
            end = _shift_arrow(end, tail, head, offset)
            width = _width(value, scale)
            ax.annotate(
                "", xy=end, xytext=start,
                arrowprops=dict(
                    facecolor=color, edgecolor=color, width=width,
                    headwidth=max(3.0, width * 2.0), headlength=max(3.0, width * 2.0),
                ),
            )
        old_sd = None if before_uncertainty is None else float(before_uncertainty.get(term, np.nan))
        new_sd = None if after_uncertainty is None else float(after_uncertainty.get(term, np.nan))
        if not show_arrow_uncertainty:
            old_sd = new_sd = None
        ax.text(label[0], label[1] + 0.045, ARROW_LABELS[term], ha="center", va="bottom",
                fontsize=6.3, fontweight="bold")
        ax.text(label[0], label[1] - 0.015, _format_value(old, old_sd), ha="center", va="top",
                fontsize=5.8, color=BEFORE_COLOR, fontweight="bold")
        ax.text(label[0], label[1] - 0.090, _format_value(new, new_sd), ha="center", va="top",
                fontsize=5.8, color=AFTER_COLOR, fontweight="bold")
    ax.text(0, 0.02, title, ha="center", va="center", fontsize=8.8, fontweight="bold")


def comparison_legend_handles():
    return [
        plt.Line2D([], [], color=BEFORE_COLOR, linewidth=3.2, label="before (legacy)"),
        plt.Line2D([], [], color=AFTER_COLOR, linewidth=3.2, label="after (corrected)"),
    ]


def draw_cycle_overlay(ax, series, *, title: str, scale: str) -> None:
    ax.set_xlim(-1.10, 1.10)
    ax.set_ylim(-1.25, 1.25)
    ax.set_aspect("equal")
    ax.axis("off")
    for term, (x, y) in BOXES.items():
        ax.add_patch(patches.Circle((x, y), 0.205, facecolor="#edf6f8", edgecolor="#9bb7bd", linewidth=0.8))
        ax.text(x, y + 0.02, BOX_LABELS[term], ha="center", va="center", fontsize=8, fontweight="bold")
    offsets = np.linspace(-0.09, 0.09, len(series))
    for offset, (label_name, values, color) in zip(offsets, series):
        for term, (tail, head, label) in ARROWS.items():
            value = float(values.get(term, np.nan))
            if not np.isfinite(value):
                continue
            dx, dy = (0, offset) if abs(tail[1] - head[1]) < 1e-8 else (offset, 0)
            start = (tail[0] + dx, tail[1] + dy)
            end = (head[0] + dx, head[1] + dy)
            if value < 0:
                start, end = end, start
            width = _width(value, scale) * 0.70
            ax.annotate(
                "", xy=end, xytext=start,
                arrowprops=dict(facecolor=color, edgecolor=color, width=width,
                                headwidth=max(2.8, width * 2), headlength=max(2.8, width * 2), alpha=0.95),
            )
        for term, (x, y) in BOXES.items():
            value = float(values.get(term, np.nan))
            symbol = "+" if value >= 0 else "-"
            ax.text(x + offset * 0.9, y - 0.11, symbol, color=color, fontsize=10, fontweight="bold", ha="center")
    for term, (_, _, label) in ARROWS.items():
        ax.text(
            label[0], label[1], ARROW_LABELS[term],
            ha="center", va="center", fontsize=7.5, fontweight="bold",
            color="#252525", bbox=dict(facecolor="white", edgecolor="none", alpha=0.82, pad=0.6),
            zorder=10,
        )
    if title:
        ax.text(0, 0.02, title, ha="center", va="center", fontsize=11, fontweight="bold")


def density_levels(density: np.ndarray, n: int = 10) -> np.ndarray:
    positive = density[density > 0]
    if not len(positive):
        return np.linspace(0, 1, n)
    low = np.quantile(positive, 0.30)
    high = np.quantile(positive, 0.995)
    if high <= low:
        high = positive.max()
    return np.linspace(low, high, n)


def map_axis(figure, position=111, extent=(-80, 180, -85, -15)):
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    ax = figure.add_subplot(position, projection=ccrs.PlateCarree())
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND, facecolor="#f0f0ed", edgecolor="black", linewidth=0.4, zorder=4)
    ax.coastlines(resolution="110m", linewidth=0.45, zorder=5)
    grid = ax.gridlines(draw_labels=True, linewidth=0.25, color="0.4", alpha=0.4, linestyle=":")
    grid.top_labels = False
    grid.right_labels = False
    grid.xlabel_style = {"size": 7}
    grid.ylabel_style = {"size": 7}
    return ax


def plot_density(ax, lon, lat, density, *, title: str, cmap="Spectral_r", levels=None):
    import cartopy.crs as ccrs

    levels = density_levels(density) if levels is None else levels
    contour = ax.contourf(lon, lat, density, levels=levels, cmap=cmap, extend="max", transform=ccrs.PlateCarree())
    ax.contour(lon, lat, density, levels=levels, colors="0.25", linewidths=0.18, alpha=0.45, transform=ccrs.PlateCarree())
    ax.set_title(title, fontsize=9, fontweight="bold", loc="left")
    return contour
