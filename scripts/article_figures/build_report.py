#!/usr/bin/env python3
"""Build the paired before-versus-after climatology report as a paginated PDF."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

def page_footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#d4d8da"))
    canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#5f676b"))
    canvas.drawString(18 * mm, 9 * mm, "LEC climatology before versus after")
    canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, f"Page {document.page}")
    canvas.restoreState()


def scaled_image(path: Path, max_width: float, max_height: float) -> Image:
    width, height = ImageReader(str(path)).getSize()
    factor = min(max_width / width, max_height / height)
    return Image(str(path), width=width * factor, height=height * factor)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.output_root.resolve()
    figures_dir = root / "figures" / "paired_control" / "article_style"
    results_dir = root / "results" / "paired_control" / "article_style"
    output = root / "docs" / "paired_control" / "lec_climatology_paired_article_style_report.pdf"

    manifest = pd.read_csv(results_dir / "figure_manifest.csv")
    stats = pd.read_csv(results_dir / "phase_statistics.csv")
    eof_variance = pd.read_csv(results_dir / "eof_variance_by_phase.csv")
    cluster_stats = pd.read_csv(results_dir / "intense_cluster_statistics.csv")
    provenance = json.loads((results_dir / "provenance.json").read_text())
    cluster_meta = json.loads((results_dir / "intense_cluster_metadata.json").read_text())
    if len(manifest) != 20:
        raise ValueError(f"expected 20 comparison files (Figures 1-11, 12a-b, 13-15 and 16a-d), found {len(manifest)}")

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=21, leading=25, textColor=colors.HexColor("#183b4e"),
        alignment=TA_LEFT, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="ReportSubtitle", parent=styles["Normal"], fontName="Helvetica",
        fontSize=10.5, leading=15, textColor=colors.HexColor("#43545d"), spaceAfter=16,
    ))
    styles.add(ParagraphStyle(
        name="Section", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=15, leading=18, textColor=colors.HexColor("#183b4e"), spaceBefore=6, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="FigureTitle", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=12, leading=15, textColor=colors.HexColor("#183b4e"), spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Caption", parent=styles["Normal"], fontName="Helvetica-Oblique",
        fontSize=8.6, leading=12, textColor=colors.HexColor("#33383b"),
        alignment=TA_CENTER, spaceBefore=6,
    ))
    styles.add(ParagraphStyle(
        name="BodySmall", parent=styles["BodyText"], fontSize=9.2, leading=13,
        textColor=colors.HexColor("#20272b"), spaceAfter=6,
    ))

    document = SimpleDocTemplate(
        str(output), pagesize=A4,
        rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=17 * mm, bottomMargin=19 * mm,
        title="LEC climatology figures before versus after",
        author="Danilo Couto de Souza",
        subject="Lorenz Energy Cycle climatology corrected rerun",
    )
    story = [
        Spacer(1, 8 * mm),
        Paragraph("LEC climatology figures: before versus after", styles["ReportTitle"]),
        Paragraph(
            "A direct comparison of the published legacy calculation and the validated "
            "LorenzCycleToolKit 2.0.0 rerun for Southwestern Atlantic cyclones",
            styles["ReportSubtitle"],
        ),
        Table(
            [
                ["Paired cyclones", f"{provenance['paired_cyclones']:,}"],
                ["Primary rows per version", f"{provenance['primary_phase_rows_per_version']:,}"],
                ["Toolkit commit", provenance["toolkit_commit"][:12]],
                ["Correction commit", provenance["toolkit_correction_commit"][:12]],
                ["Comparison files", "20 PNG + 20 PDF"],
            ],
            colWidths=[58 * mm, 100 * mm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8f1f4")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#263238")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b8c6cc")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]),
        ),
        Spacer(1, 7 * mm),
        Paragraph("Purpose", styles["Section"]),
        Paragraph(
            "This document places the legacy before result and the corrected after result in the same "
            "figure wherever possible. Both sides use the identical 3,820-cyclone population, so the "
            "differences isolate the toolkit correction rather than a change of sample. Published "
            "article files remain untouched.",
            styles["BodySmall"],
        ),
        Paragraph("Scope decisions", styles["Section"]),
        Paragraph(
            "The main panels use one primary incipient, intensification, mature and decay record per "
            "cyclone. Secondary lifecycle episodes remain preserved upstream but are outside this "
            "four-phase comparison. EOFs use the published 24-term correlation-matrix definition; "
            "corrected modes are matched to legacy modes by loading-pattern correlation and sign-aligned. "
            "Intense groups retain the published 90th-percentile criterion and are matched by standardized "
            "centroid distance.",
            styles["BodySmall"],
        ),
        PageBreak(),
        Paragraph("Before-after numerical overview", styles["Section"]),
    ]

    phase_table = stats[stats["term"].isin(["Ca", "Ck", "Ce"])].pivot(index=["version", "phase"], columns="term", values="mean")
    eof1 = eof_variance[eof_variance["eof"] == 1].set_index(["version", "scope"])["explained_variance_pct"]
    overview = [["Phase", "Ca before -> after", "Ck before -> after", "Ce before -> after", "EOF1 variance"]]
    for phase in ["incipient", "intensification", "mature", "decay"]:
        overview.append([
            phase,
            f"{phase_table.loc[('before', phase), 'Ca']:.2f} -> {phase_table.loc[('after', phase), 'Ca']:.2f}",
            f"{phase_table.loc[('before', phase), 'Ck']:.2f} -> {phase_table.loc[('after', phase), 'Ck']:.2f}",
            f"{phase_table.loc[('before', phase), 'Ce']:.2f} -> {phase_table.loc[('after', phase), 'Ce']:.2f}",
            f"{eof1.loc[('before', phase)]:.1f}% -> {eof1.loc[('after', phase)]:.1f}%",
        ])
    story.append(Table(
        overview, colWidths=[32 * mm, 34 * mm, 34 * mm, 34 * mm, 34 * mm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#183b4e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.3),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#bcc6ca")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7f8")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]),
    ))
    story.extend([
        Spacer(1, 7 * mm),
        Paragraph("Intense-cyclone groups", styles["Section"]),
        Paragraph(
            f"The pointwise vorticity threshold is {cluster_meta['vorticity_threshold']:.3f}; "
            f"{cluster_meta['eligible_paired_cyclones']:,} paired cyclones enter both four-group analyses. "
            "After groups are reordered to their closest before centroid.",
            styles["BodySmall"],
        ),
    ])
    cluster_table = [["Version", "Cluster", "n", "Mean max. vorticity", "Median max. vorticity"]]
    for version in ("before", "after"):
        for row in cluster_stats[cluster_stats["version"] == version].sort_values("cluster").itertuples():
            cluster_table.append([row.version, row.cluster, row.n, f"{row.max_vor42_mean:.2f}", f"{row.max_vor42_median:.2f}"])
    story.append(Table(
        cluster_table, colWidths=[29 * mm, 24 * mm, 22 * mm, 43 * mm, 43 * mm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#183b4e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.3),
            ("ALIGN", (0, 1), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#bcc6ca")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7f8")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]),
    ))

    max_image_width = A4[0] - document.leftMargin - document.rightMargin
    max_image_height = A4[1] - document.topMargin - document.bottomMargin - 45 * mm
    for row in manifest.itertuples():
        png = root / row.png
        block = [
            Paragraph(f"Figure {row.figure_label}", styles["FigureTitle"]),
            scaled_image(png, max_image_width, max_image_height),
            Paragraph(row.caption, styles["Caption"]),
        ]
        story.extend([PageBreak(), KeepTogether(block)])

    story.extend([
        PageBreak(),
        Paragraph("Reproducibility record", styles["Section"]),
        Paragraph(
            "Every figure has a PNG and PDF checksum in results/paired_control/article_style/figure_manifest.csv. "
            "The complete input hashes and pinned toolkit commits are recorded in the adjacent provenance.json. "
            "The workflow is scripts/article_figures/generate_comparison.py; this report is built by "
            "scripts/article_figures/build_report.py.", styles["BodySmall"],
        ),
    ])

    output.parent.mkdir(parents=True, exist_ok=True)
    document.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
