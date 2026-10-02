"""Rebuild supplementary Figures S1–S4 from the published workflows.

The archived submission PNGs are copied without modification. Corrected
figures use validated total EOF identities, four-cluster assignments and
corrected per-timestep Ck. Run after the article products are validated.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from pyproj import Geod
from PIL import Image

from scripts.article_figures.common import sha256_file
from scripts.article_figures.build_validated_comparison import make_pair

ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT = Path('/Users/danilocoutodesouza/Documents/danilo_thesis_iag/manuscript_lec_climatology')
SUBMISSION = MANUSCRIPT / 'submission_files-clim_dyn_rev2/LEC_climatology_clim_dyn_vCBG-2'
ARCHIVE = ROOT.parent / 'energetic_patterns_cyclones_south_atlantic/tracks_SAt_filtered'
TRACKS = ARCHIVE / 'tracks_SAt_filtered_with_periods.csv'
ENERGETICS = ARCHIVE / 'tracks_SAt_filtered_with_energetics.csv'
CORRECTED_CK = ROOT / 'tmp/supplementary/ck_corrected.csv'
REMOTE_HASHES = ROOT / 'tmp/supplementary/remote_sha256.txt'
NAMES = {
    'S1': 'panel_2x2_metrics_q90_vs_q10.png',
    'S2': 'duration.png',
    'S3': 'intense_systems_PCs_stacked_pcs.png',
    'S4': 'ck_decay_phase_median_iqr.png',
}
ORIGINAL_SCRIPTS = {
    'S1': MANUSCRIPT / 'eof_cyclone_statistics_q10_q90.py',
    'S2': MANUSCRIPT / 'eof_cluster_statistics.py',
    'S3': MANUSCRIPT / 'playground.py',
    'S4': MANUSCRIPT / 'check_decay_phase.py',
}
COLORS = {'EOF(+)': '#B55D60', 'EOF(-)': '#5975A4'}
PC_COLS = [f'PC{i}' for i in range(1, 5)]
WGS84 = Geod(ellps='WGS84')


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, float_format='%.17g')


def track_metrics(tracks: pd.DataFrame, ids: set[int]) -> pd.DataFrame:
    frame = tracks[tracks.track_id.isin(ids)]
    rows = []
    for track_id, group in frame.groupby('track_id', sort=True):
        ordered = group.sort_values('date')
        latitudes = ordered['lat vor'].to_numpy()
        longitudes = ordered['lon vor'].to_numpy()
        times = ordered.date.to_numpy()
        # The source uses geopy.geodesic (WGS84) for each adjacent pair.
        # PROJ's WGS84 inverse solves the same ellipsoidal geodesic in a batch.
        if len(ordered) > 1:
            _, _, meters = WGS84.inv(longitudes[:-1], latitudes[:-1],
                                     longitudes[1:], latitudes[1:])
            hours = np.diff(times) / np.timedelta64(1, 'h')
            speeds = np.where(hours > 0, meters / 1000 / hours, 0)
        else:
            speeds = []
        rows.append(dict(track_id=track_id, max_intensity=group.vor42.max(),
                         duration=(group.date.max() - group.date.min()).total_seconds() / 86400,
                         mean_speed=np.mean(speeds) if len(speeds) else np.nan))
    if set(frame.track_id) != ids:
        raise ValueError('some EOF-assigned cyclones are absent from archived tracks')
    return pd.DataFrame(rows)


def render_s1(frame: pd.DataFrame, output: Path) -> None:
    sns.set_context('notebook', font_scale=1.5)
    sns.set_style('whitegrid')
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    counts = frame.groupby(['dominant_eof', 'q']).size().rename('cyclone_count').reset_index()
    columns = [('cyclone_count', counts), ('max_intensity', frame),
               ('duration', frame), ('mean_speed', frame.dropna(subset=['mean_speed']))]
    for index, (variable, data) in enumerate(columns):
        ax = axes[index // 2, index % 2]
        if index == 0:
            sns.barplot(data=data, x='dominant_eof', y=variable, hue='q',
                        hue_order=['EOF(+)', 'EOF(-)'], palette=COLORS, ax=ax)
            for patch in ax.patches:
                height = patch.get_height()
                if np.isfinite(height) and height > 0:
                    ax.annotate(str(int(height)), (patch.get_x() + patch.get_width()/2, height),
                                ha='center', va='bottom', fontsize=14, fontweight='bold')
        else:
            sns.boxplot(data=data, x='dominant_eof', y=variable, hue='q',
                        hue_order=['EOF(+)', 'EOF(-)'], palette=COLORS, ax=ax)
        ax.set_title(f'({chr(65 + index)}) {variable.replace("_", " ").title()} EOF(+) vs EOF(-)',
                     fontsize=20, fontweight='bold')
        ax.set_xlabel('EOF', fontsize=18)
        ax.set_ylabel(variable.replace('_', ' ').title(), fontsize=18)
        ax.tick_params(axis='both', labelsize=16)
        if index == 0:
            ax.legend(title=None, fontsize=14, loc='upper right')
        else:
            legend = ax.get_legend()
            if legend is not None:
                legend.remove()
    fig.tight_layout()
    fig.savefig(output, dpi=300)
    plt.close(fig)


def render_s2(frame: pd.DataFrame, output: Path) -> None:
    plt.rcdefaults()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=frame, x='cluster', y='duration', hue='cluster',
                palette='tab20', dodge=False, ax=ax)
    ax.set_title('(E) Average Duration of Systems', fontsize=20, fontweight='bold')
    ax.set_xlabel('Cluster', fontsize=18)
    ax.set_ylabel('Average Duration (days)', fontsize=18)
    ax.tick_params(axis='both', labelsize=16)
    ax.legend(title='cluster', fontsize=14)
    fig.tight_layout()
    fig.savefig(output, dpi=300)
    plt.close(fig)


def render_s3(frame: pd.DataFrame, output: Path) -> None:
    plt.rcdefaults()
    fig, ax = plt.subplots(figsize=(15, 8))
    frame[PC_COLS].plot(kind='bar', stacked=True, ax=ax, width=1,
                        color=['#5975A4', '#CC8963', '#B55D60', '#5F9E6E'])
    ax.set_title('PC1 to PC4 Time Series – Cyclones with ζ_central > q99')
    ax.set_xlabel('Cyclones')
    ax.set_ylabel('PC Value')
    ax.set_xticklabels([])
    ax.legend(title='Principal Components')
    fig.tight_layout()
    fig.savefig(output, dpi=300)
    plt.close(fig)


def render_s4(frame: pd.DataFrame, output: Path) -> None:
    plt.rcdefaults()
    values = frame[['Ck_initial', 'Ck_final']]
    median = values.median()
    iqr = values.quantile(.75) - values.quantile(.25)
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(5, 6), dpi=300)
    ax.bar(['Initial Ck', 'Final Ck'], median, yerr=iqr, capsize=8,
           color=['#377eb8', '#e41a1c'], width=.6)
    ax.set_ylabel('Ck', fontsize=14)
    ax.set_title('Median Ck at Start and End of Decay Phase\n(Error bar = IQR)', fontsize=15)
    ax.tick_params(axis='both', labelsize=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylim(min(median - iqr) * .95, max(median + iqr) * 1.05)
    fig.tight_layout()
    fig.savefig(output, bbox_inches='tight', dpi=300)
    plt.close(fig)


def fit_published_dimensions(path: Path, published: Path) -> None:
    with Image.open(path) as generated, Image.open(published) as original:
        if generated.size == original.size:
            return
        resized = generated.convert('RGB').resize(original.size, Image.Resampling.LANCZOS)
    resized.save(path)


def pdf_from_png(path: Path) -> Path:
    pdf = path.with_suffix('.pdf')
    with Image.open(path) as image:
        image.convert('RGB').save(pdf, 'PDF', resolution=300)
    return pdf


def original_ck_pairs() -> pd.DataFrame:
    frame = pd.read_csv(ENERGETICS, usecols=['track_id', 'period', 'Ck'])
    frame = frame.dropna(subset=['track_id', 'period', 'Ck'])
    frame = frame.loc[frame.period.ne('residual')]
    valid = frame.groupby('track_id').period.agg(lambda s: s.drop_duplicates().tolist())
    ids = set(valid[valid.map(lambda phases: phases == ['incipient', 'intensification', 'mature', 'decay'])].index)
    decay = frame.loc[frame.track_id.isin(ids) & frame.period.eq('decay')]
    result = decay.groupby('track_id', sort=True).Ck.agg(Ck_initial='first', Ck_final='last', decay_points='size').reset_index()
    if result.empty:
        raise ValueError('legacy decay Ck gate has no matching tracks')
    return result


def main() -> int:
    from scripts.article_figures import reproduce_downstream as article
    gate = json.loads((article.GATE / 'manifest.json').read_text())
    corrected = json.loads((article.CORRECTED / 'provenance.json').read_text())
    if not all(check['passed'] for check in gate['checks']) or corrected['status'] != 'VALIDATED_CORRECTED_CANDIDATES':
        raise ValueError('main article validation gate has not passed')
    if not CORRECTED_CK.is_file() or not REMOTE_HASHES.is_file():
        raise FileNotFoundError('corrected per-timestep Ck extraction and remote source hashes are required')
    data = {}
    for version in ('original', 'corrected'):
        data[version] = {
            'extremes': pd.read_csv(ROOT / f'results/{version}/article/eof_extreme_assignments.csv'),
            'clusters': pd.read_csv(ROOT / f'results/{version}/article/cluster_assignments.csv'),
            'scores': pd.read_csv(ROOT / f'results/{version}/article/eof_scores_total.csv'),
        }
    expected = [1305, 1334, 433, 600, 375, 642, 337, 383]
    actual = [len(data['original']['extremes'].query('dominant_eof == @mode and sign == @sign'))
              for mode in range(1, 5) for sign in ('positive', 'negative')]
    if actual != expected:
        raise ValueError(f'S1 legacy count gate differs from published figure: {actual}')
    tracks = pd.read_csv(TRACKS, usecols=['track_id', 'date', 'lat vor', 'lon vor', 'vor42'])
    tracks.date = pd.to_datetime(tracks.date)
    selected_ids = set(pd.concat([data[v]['extremes'].track_id for v in data]))
    metrics = track_metrics(tracks, selected_ids)
    all_duration = tracks.groupby('track_id').date.agg(['min', 'max'])
    all_duration['duration'] = (all_duration['max'] - all_duration['min']).dt.days
    intensity = pd.read_csv(ENERGETICS, usecols=['track_id', 'vor42']).groupby('track_id').vor42.max()
    s3_threshold = float(intensity.quantile(.95))
    s3_ids = set(intensity[intensity > s3_threshold].index)
    ck = {'original': original_ck_pairs(), 'corrected': pd.read_csv(CORRECTED_CK)}
    if not set(ck['corrected'].track_id) <= set(data['corrected']['scores'].track_id):
        raise ValueError('corrected decay Ck contains IDs outside validated population')
    if set(ck['original'].track_id) != set(ck['corrected'].track_id):
        raise ValueError('S4 legacy and corrected strict-four-phase IDs differ')
    outputs = {}
    for version in ('original', 'corrected'):
        result_dir = ROOT / f'results/{version}/supplementary'
        figure_dir = ROOT / f'figures/{version}/supplementary'
        result_dir.mkdir(parents=True, exist_ok=True)
        figure_dir.mkdir(parents=True, exist_ok=True)
        extremes = data[version]['extremes']
        s1 = extremes[['track_id', 'sign', 'dominant_eof']].merge(metrics, on='track_id', validate='many_to_one')
        s1['q'] = s1.sign.map({'positive': 'EOF(+)', 'negative': 'EOF(-)'})
        csv(result_dir / 's1_eof_cyclone_metrics.csv', s1)
        s2 = data[version]['clusters'][['track_id', 'cluster']].merge(
            all_duration[['duration']], left_on='track_id', right_index=True, validate='one_to_one')
        assert len(s2) == (679 if version == 'original' else 603)
        csv(result_dir / 's2_cluster_duration.csv', s2)
        # The original script outer-merges q10 first, then q90; its q95 filter
        # is based on maximum vorticity over all archived tracked cyclones.
        order = pd.concat([extremes.query('sign == "negative"'),
                           extremes.query('sign == "positive"')]).drop_duplicates('track_id').sort_values('track_id')
        s3 = order.loc[order.track_id.isin(s3_ids), ['track_id', *PC_COLS]]
        csv(result_dir / 's3_intense_pc_scores.csv', s3)
        csv(result_dir / 's4_decay_ck_pairs.csv', ck[version])
        outputs[version] = {'S1': s1, 'S2': s2, 'S3': s3, 'S4': ck[version]}
        for label, name in NAMES.items():
            destination = figure_dir / f'fig_{label.lower()}_{Path(name).stem}.png'
            published = SUBMISSION / name
            if version == 'original':
                shutil.copyfile(published, destination)
            else:
                {'S1': render_s1, 'S2': render_s2, 'S3': render_s3, 'S4': render_s4}[label](outputs[version][label], destination)
                fit_published_dimensions(destination, published)
                pdf_from_png(destination)
    comparison_dir = ROOT / 'figures/comparison/supplementary'
    comparison_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for label, name in NAMES.items():
        stem = f'fig_{label.lower()}_{Path(name).stem}'
        original = ROOT / f'figures/original/supplementary/{stem}.png'
        corrected = ROOT / f'figures/corrected/supplementary/{stem}.png'
        pair = comparison_dir / f'{stem}_published_corrected.png'
        pdf = make_pair(original, corrected, pair)
        rows.append(dict(figure=label, original_png=rel(original), original_sha256=sha256_file(original),
                         corrected_png=rel(corrected), corrected_sha256=sha256_file(corrected),
                         comparison_png=rel(pair), comparison_sha256=sha256_file(pair),
                         comparison_pdf=rel(pdf), comparison_pdf_sha256=sha256_file(pdf),
                         source_script=str(ORIGINAL_SCRIPTS[label]), source_script_sha256=sha256_file(ORIGINAL_SCRIPTS[label])))
    comparison_results = ROOT / 'results/comparison/supplementary'
    csv(comparison_results / 'figure_manifest.csv', pd.DataFrame(rows))
    for name in ('s1_eof_cyclone_metrics.csv', 's2_cluster_duration.csv',
                 's3_intense_pc_scores.csv', 's4_decay_ck_pairs.csv'):
        pair = pd.concat([pd.read_csv(ROOT / f'results/{version}/supplementary/{name}').assign(
            version='before' if version == 'original' else 'after') for version in ('original', 'corrected')],
            ignore_index=True)
        csv(comparison_results / name, pair)
    sources = {str(path): sha256_file(path) for path in [TRACKS, ENERGETICS, CORRECTED_CK,
                Path(__file__).with_name('extract_corrected_decay_ck.py'),
                ROOT / 'results/original/article/reproduction_gate/manifest.json',
                ROOT / 'results/corrected/article/provenance.json',
                *ORIGINAL_SCRIPTS.values(), *[SUBMISSION / name for name in NAMES.values()]]}
    remote_sources = {}
    for line in REMOTE_HASHES.read_text().splitlines():
        digest, path = line.split(maxsplit=1)
        if len(digest) != 64 or not path.startswith('/p1-swell/danilocs/lec_climatology_corrected_v2/'):
            raise ValueError('invalid remote production source hash')
        remote_sources[path] = digest
    if len(remote_sources) != 2:
        raise ValueError('missing corrected production provenance or population manifest hash')
    summary = dict(populations={'original': 6789, 'corrected': 3820},
                   s1_counts_original=actual, s2_clusters={'original': 679, 'corrected': 603},
                   s3_original_script_quantile=.95, s3_threshold=s3_threshold,
                   s3_selected={version: len(outputs[version]['S3']) for version in outputs},
                   s4_valid={version: len(outputs[version]['S4']) for version in outputs},
                   sources=sources, remote_sources=remote_sources,
                   generator_sha256=sha256_file(Path(__file__)))
    for version in ('original', 'corrected', 'comparison'):
        directory = ROOT / f'results/{version}/supplementary'
        figures = ROOT / f'figures/{version}/supplementary'
        files = [*directory.glob('*.csv'), *figures.glob('*.png'), *figures.glob('*.pdf')]
        manifest = dict(summary, family=version,
                        outputs={rel(path): sha256_file(path) for path in files})
        (directory / 'provenance.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
