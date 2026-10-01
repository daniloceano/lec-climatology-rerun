"""Make article before/after panels from the validated original and corrected figures.

This renderer performs no EOF, cluster, LEC or density computation. It verifies
both source images, then places them side by side for visual diagnostics.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from scripts.article_figures.common import sha256_file
from scripts.article_figures.generate_corrected_article import FIGURE_NAMES

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT / 'figures/original/article'
CORRECTED = ROOT / 'figures/corrected/article'
COMPARISON = ROOT / 'figures/comparison/article'
RESULTS = ROOT / 'results/comparison/article'
VALIDATED = ROOT / 'results/corrected/article'


def make_pair(original: Path, corrected: Path, output: Path) -> Path:
    with Image.open(original) as before, Image.open(corrected) as after:
        if before.size != after.size:
            raise ValueError(f'validated pair has different dimensions: {original}, {corrected}')
        width = min(before.width, 1800)
        height = round(before.height * width / before.width)
        size = (width, height)
        before_view = before.convert('RGB').resize(size, Image.Resampling.LANCZOS)
        after_view = after.convert('RGB').resize(size, Image.Resampling.LANCZOS)
    gap, margin, header = 18, 20, 76
    panel = Image.new('RGB', (2 * width + gap + 2 * margin, height + header + margin), 'white')
    panel.paste(before_view, (margin, header))
    panel.paste(after_view, (margin + width + gap, header))
    draw = ImageDraw.Draw(panel)
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 38)
    draw.text((margin, 18), 'Published / legacy', fill='black', font=font)
    draw.text((margin + width + gap, 18), 'Corrected', fill='black', font=font)
    draw.line((margin + width + gap // 2, header, margin + width + gap // 2, header + height), fill='#777777', width=2)
    panel.save(output)
    pdf = output.with_suffix('.pdf')
    panel.save(pdf, 'PDF', resolution=300)
    return pdf


def main() -> int:
    validated = json.loads((VALIDATED / 'provenance.json').read_text())
    if validated['status'] != 'VALIDATED_CORRECTED_CANDIDATES':
        raise ValueError('corrected Figures 9–16 have not passed the legacy gate')
    corrected_manifest = pd.read_csv(VALIDATED / 'figure_manifest_09_16.csv').set_index('figure')
    published_manifest = pd.read_csv(VALIDATED / 'figure_manifest.csv').set_index('figure')
    if sorted(corrected_manifest.index) != list(range(9, 17)):
        raise ValueError('corrected Figure 9–16 manifest is incomplete')
    rows = []
    for number in range(9, 17):
        name = FIGURE_NAMES[number]
        before, after = ORIGINAL / name, CORRECTED / name
        if sha256_file(after) != corrected_manifest.loc[number, 'png_sha256']:
            raise ValueError(f'corrected figure hash mismatch: {after}')
        if sha256_file(before) != published_manifest.loc[number, 'published_png_sha256']:
            raise ValueError(f'published figure hash mismatch: {before}')
        output = COMPARISON / name.replace('.png', '_published_corrected.png')
        pdf = make_pair(before, after, output)
        rows.append(dict(
            figure_label=str(number),
            caption=f'Published Figure {number} (left) and validated corrected Figure {number} (right).',
            png=str(output.relative_to(ROOT)), pdf=str(pdf.relative_to(ROOT)),
            png_sha256=sha256_file(output), pdf_sha256=sha256_file(pdf),
            phase_eof_product='', eof_identity='',
            published_png=str(before.relative_to(ROOT)), published_png_sha256=sha256_file(before),
            corrected_png=str(after.relative_to(ROOT)), corrected_png_sha256=sha256_file(after),
        ))

    # Old 12a/12b and 16a–d panels encoded superseded scientific definitions.
    # Remove them only after all eight replacement panels have been built.
    current = {str((ROOT / row['png']).resolve()) for row in rows}
    for prefix in ('fig_12', 'fig_13', 'fig_14', 'fig_16'):
        for path in COMPARISON.glob(prefix + '*_published_corrected.*'):
            if path.suffix in {'.png', '.pdf'} and str(path.with_suffix('.png').resolve()) not in current:
                path.unlink()
    old = pd.read_csv(RESULTS / 'figure_manifest.csv')
    old = old[old.figure_label.astype(str).isin([str(n) for n in range(1, 9)])]
    final = pd.concat([old, pd.DataFrame(rows)], ignore_index=True)
    final.to_csv(RESULTS / 'figure_manifest.csv', index=False)
    provenance_path = RESULTS / 'provenance.json'
    provenance = json.loads(provenance_path.read_text())
    provenance.update(status='DERIVED_FROM_VALIDATED_WORKFLOWS', clusters=4,
                      figure_files=16,
                      workflow='published article versus validated corrected article',
                      method='Pillow side-by-side montage; no scientific recalculation',
                      source_results={'original': 'results/original/article',
                                      'corrected': 'results/corrected/article'},
                      corrected_provenance_sha256=sha256_file(VALIDATED / 'provenance.json'),
                      corrected_manifest_sha256=sha256_file(VALIDATED / 'figure_manifest_09_16.csv'),
                      figure_manifest_sha256=sha256_file(RESULTS / 'figure_manifest.csv'),
                      numeric_outputs={str(path.relative_to(ROOT)): sha256_file(path)
                                       for name in ('eof_scores_total.csv','eof_extreme_assignments.csv',
                                                    'eof_loadings_total.csv','eof_variance_total.csv',
                                                    'cluster_assignments.csv','cluster_centers.csv',
                                                    'figure14_statistics.csv')
                                       for path in [RESULTS / name]},
                      figures_09_16=rows)
    provenance_path.write_text(json.dumps(provenance, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
