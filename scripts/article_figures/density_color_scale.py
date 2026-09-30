"""Publication-layout density maps with data-derived color limits.

The archived renderers supply the map decorations and layout conventions. Only
the color boundaries and the tiny visual overshoot caused by rounding change.
The underlying NetCDF and CSV density fields are never clipped.
"""
from __future__ import annotations

from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

COLORS = ['#AFC4DA', '#4471B2', '#B1DFA3', '#EFF9A6',
          '#FEEC9F', '#FDB567', '#F06744', '#C1274A']


def density_levels(maximum: float, intervals: int) -> np.ndarray:
    """Keep the old interval count; prefer 0.5, 1 or 2-unit steps."""
    if not np.isfinite(maximum) or maximum <= 0.1 or intervals < 1:
        raise ValueError('invalid density maximum or interval count')
    vmax = round(float(maximum), 2)
    if vmax <= 0.1:
        raise ValueError('density maximum rounds to the lower color limit')
    uniform = np.round(np.linspace(0.1, vmax, intervals + 1), 2)
    if intervals == 1:
        return uniform
    # Dynamic programming places interior boundaries on a half-unit grid.
    # The first and last steps absorb the exact 0.1 and rounded-vmax edges.
    target_step = (vmax - 0.1) / intervals
    max_index = int(np.floor((vmax - 0.01) * 2))
    history = []
    states = {0: (0.0, None)}
    for position in range(1, intervals):
        target = 0.1 + position * target_step
        following = {}
        for previous, (cost, _) in states.items():
            steps = range(1, max_index + 1) if previous == 0 else (1, 2, 4)
            for step in steps:
                index = step if previous == 0 else previous + step
                if index > max_index or (previous == 0 and index * 0.5 - 0.1 > 2):
                    continue
                value = index * 0.5
                trial = cost + (value - target) ** 2
                if index not in following or trial < following[index][0]:
                    following[index] = (trial, previous)
        if not following:
            break
        history.append(following)
        states = following
    if len(history) == intervals - 1:
        choices = [(cost + (vmax - index * 0.5 - target_step) ** 2, index)
                   for index, (cost, _) in states.items() if 0 < vmax - index * 0.5 <= 2]
        if choices:
            _, index = min(choices)
            interior = []
            for stage in reversed(history):
                interior.append(index * 0.5)
                index = stage[index][1]
            return np.array([0.1, *reversed(interior), vmax])
    if not np.all(np.diff(uniform) > 0):
        raise ValueError('rounded density limits cannot preserve the interval count')
    return uniform


def interval_count(figure: int, group: int) -> int:
    if figure == 9:
        return 10 if group == 4 else 13
    if figure in (10,):
        return 13
    if figure == 13:
        return 8
    raise ValueError((figure, group))


def show_color_limits(bar, levels: np.ndarray) -> None:
    """Show the measured upper boundary explicitly, even on crowded bars."""
    count = len(levels) - 1
    indices = np.unique(np.rint(np.linspace(0, count, min(6, count + 1))).astype(int))
    ticks = levels[indices]
    bar.set_ticks(ticks)
    bar.set_ticklabels([f'{value:.2f}' for value in ticks])


def render_eof_panel(directory: Path, output: Path, suffix: str, maxima: dict[int, float], renderer) -> None:
    """Use the archived four-map layout with each EOF's measured top level."""
    output.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), subplot_kw={'projection': ccrs.PlateCarree()})
    figure = 9 if suffix == 'q90' else 10
    for i, group in enumerate(range(1, 5)):
        with xr.open_dataset(directory / f'SAt_track_density_eof_{group}.0.nc') as ds:
            density = ds[f'EOF_{float(group)}'].load()
        levels = density_levels(maxima[group], interval_count(figure, group))
        visible = density.clip(max=float(levels[-1]))
        cmap = mcolors.LinearSegmentedColormap.from_list('', COLORS)
        norm = mpl.colors.BoundaryNorm(levels, cmap.N)
        row, col = divmod(i, 2)
        ax = axes[row, col]
        datacrs = ccrs.PlateCarree()
        ax.set_extent([-90, 180, -15, -90], crs=datacrs)
        cf = ax.contourf(density.lon, density.lat, visible, cmap=cmap, levels=levels, norm=norm, transform=datacrs)
        ax.contour(density.lon, density.lat, visible, levels=levels, norm=norm, colors='#383838',
                   linewidths=0.35, linestyles='dashed', transform=datacrs)
        ax.text(175, -25, f'({renderer.labels[i]}) EOF {group}', ha='right', va='bottom',
                fontsize=14, fontweight='bold', bbox=dict(boxstyle='round', facecolor='white'), zorder=101)
        ax.coastlines(zorder=1)
        ax.add_feature(cfeature.LAND, color='#595959', alpha=0.1)
        renderer.gridlines(ax)
        renderer.add_regions(ax)
        bar_ax = fig.add_axes([0.12 + col * 0.47, 0.55 + row * -0.27, 0.3, 0.015])
        bar = plt.colorbar(cf, cax=bar_ax, format='%g', orientation='horizontal')
        show_color_limits(bar, levels)
        bar.ax.tick_params(labelsize=10)
    plt.subplots_adjust(bottom=0.15, top=0.95, left=0.05, right=0.95, hspace=-0.5, wspace=0.1)
    fig.savefig(output / f'density_panel_{suffix}.png', bbox_inches='tight', dpi=300)
    plt.close(fig)


def render_cluster_panel(directory: Path, output: Path, maxima: dict[int, float], renderer) -> None:
    """Use the archived four-cluster layout with eight measured intervals each."""
    output.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(10, 8), subplot_kw={'projection': ccrs.PlateCarree()})
    for i, group in enumerate(range(1, 5)):
        with xr.open_dataset(directory / f'track_density_cluster_{group}.nc') as ds:
            density = ds[f'Cluster {group}'].load()
        levels = density_levels(maxima[group], interval_count(13, group))
        visible = density.clip(max=float(levels[-1]))
        cmap = mcolors.LinearSegmentedColormap.from_list('', COLORS)
        norm = mpl.colors.BoundaryNorm(levels, cmap.N)
        row, col = divmod(i, 2)
        ax = axes[row, col]
        datacrs = ccrs.PlateCarree()
        ax.set_extent([-90, 110, -15, -90], crs=datacrs)
        cf = ax.contourf(density.lon, density.lat, visible, cmap=cmap, levels=levels,
                         norm=norm, transform=datacrs)
        ax.contour(density.lon, density.lat, visible, levels=levels, norm=norm,
                   colors='#383838', linewidths=0.35, linestyles='dashed', transform=datacrs)
        ax.text(80, -30, f'({renderer.labels[i]}) cluster {group}', ha='right', va='bottom',
                fontsize=14, fontweight='bold', bbox=dict(boxstyle='round', facecolor='white'), zorder=101)
        ax.coastlines(zorder=1)
        ax.add_feature(cfeature.LAND, color='#595959', alpha=0.1)
        renderer.gridlines(ax)
        for bounds in renderer.regions.values():
            min_lon, min_lat, max_lon, max_lat = bounds[0]
            ax.plot([min_lon, max_lon, max_lon, min_lon, min_lon],
                    [min_lat, min_lat, max_lat, max_lat, min_lat],
                    color='black', linewidth=1.5, transform=datacrs, linestyle='--')
        bar = fig.colorbar(cf, orientation='horizontal', pad=0.08)
        show_color_limits(bar, levels)
        bar.ax.tick_params(labelsize=10)
    fig.tight_layout(h_pad=-12)
    fig.savefig(output / 'density_panel.png', bbox_inches='tight', dpi=300)
    plt.close(fig)
