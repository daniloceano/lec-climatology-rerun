#!/usr/bin/env python3
"""Build the corrected 16-figure climatology report as a paginated PDF."""

from __future__ import annotations

import argparse
import json
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

from scripts.article_figures.generate import FIGURE_CAPTIONS


def page_footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#d4d8da"))
    canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#5f676b"))
    canvas.drawString(18 * mm, 9 * mm, "Corrected LEC climatology figure reproduction")
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
    figures_dir = root / "figures" / "lec_climatology_corrected"
    results_dir = root / "results" / "lec_climatology_corrected"
    output = root / "docs" / "lec_climatology_corrected_figures_report.pdf"

    manifest = pd.read_csv(results_dir / "figure_manifest.csv")
    stats = pd.read_csv(results_dir / "phase_statistics.csv")
    eof_variance = pd.read_csv(results_dir / "eof_variance_by_phase.csv")
    cluster_stats = pd.read_csv(results_dir / "intense_cluster_statistics.csv")
    provenance = json.loads((results_dir / "provenance.json").read_text())
    cluster_meta = json.loads((results_dir / "intense_cluster_metadata.json").read_text())
    if len(manifest) != 16:
        raise ValueError(f"expected 16 figures, found {len(manifest)}")

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
        title="Corrected reproduction of the LEC climatology figures",
        author="Danilo Couto de Souza",
        subject="Lorenz Energy Cycle climatology corrected rerun",
    )
    story = [
        Spacer(1, 8 * mm),
        Paragraph("Corrected reproduction of the LEC climatology figures", styles["ReportTitle"]),
        Paragraph(
            "A new 16-figure report based on the validated LorenzCycleToolKit 2.0.0 rerun "
            "for Southwestern Atlantic cyclones", styles["ReportSubtitle"],
        ),
        Table(
            [
                ["Corrected cyclones", f"{provenance['corrected_cyclones']:,}"],
                ["Primary cyclone-phase rows", f"{provenance['primary_phase_rows']:,}"],
                ["Toolkit commit", provenance["toolkit_commit"][:12]],
                ["Correction commit", provenance["toolkit_correction_commit"][:12]],
                ["Figures", "16 PNG + 16 PDF"],
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
            "This document recreates the scientific roles of Figures 1-16 in the published "
            "LEC climatology article while replacing every LEC-dependent value with the corrected "
            "3,820-case rerun. Published legacy figures remain untouched. Track-only and conceptual "
            "panels are regenerated from their frozen source data and definitions.",
            styles["BodySmall"],
        ),
        Paragraph("Scope decisions", styles["Section"]),
        Paragraph(
            "The main panels use one primary incipient, intensification, mature and decay record per "
            "cyclone. Secondary lifecycle episodes remain preserved upstream but are outside this "
            "four-phase reproduction. EOFs use the published 24-term correlation-matrix definition. "
            "Intense groups retain the published 90th-percentile vorticity criterion and four-cluster "
            "structure, with deterministic initialization for reproducibility.",
            styles["BodySmall"],
        ),
        PageBreak(),
        Paragraph("Updated numerical overview", styles["Section"]),
    ]

    phase_table = stats[stats["term"].isin(["Ca", "Ck", "Ce"])].pivot(index="phase", columns="term", values="mean")
    eof1 = eof_variance[eof_variance["eof"] == 1].set_index("scope")["explained_variance_pct"]
    overview = [["Phase", "Ca mean", "Ck mean", "Ce mean", "EOF1 variance"]]
    for phase in ["incipient", "intensification", "mature", "decay"]:
        overview.append([
            phase, f"{phase_table.loc[phase, 'Ca']:.2f}", f"{phase_table.loc[phase, 'Ck']:.2f}",
            f"{phase_table.loc[phase, 'Ce']:.2f}", f"{eof1.loc[phase]:.2f}%",
        ])
    story.append(Table(
        overview, colWidths=[40 * mm, 27 * mm, 27 * mm, 27 * mm, 34 * mm],
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
            f"{cluster_meta['eligible_corrected_cyclones']:,} corrected cyclones enter the four-group analysis.",
            styles["BodySmall"],
        ),
    ])
    cluster_table = [["Cluster", "n", "Mean maximum vorticity", "Median maximum vorticity"]]
    for row in cluster_stats.sort_values("cluster").itertuples():
        cluster_table.append([row.cluster, row.n, f"{row.max_vor42_mean:.2f}", f"{row.max_vor42_median:.2f}"])
    story.append(Table(
        cluster_table, colWidths=[28 * mm, 28 * mm, 50 * mm, 50 * mm],
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
    for number in range(1, 17):
        png = sorted(figures_dir.glob(f"fig_{number:02d}_*.png"))[0]
        block = [
            Paragraph(f"Figure {number}", styles["FigureTitle"]),
            scaled_image(png, max_image_width, max_image_height),
            Paragraph(FIGURE_CAPTIONS[number], styles["Caption"]),
        ]
        story.extend([PageBreak(), KeepTogether(block)])

    story.extend([
        PageBreak(),
        Paragraph("Reproducibility record", styles["Section"]),
        Paragraph(
            "Every figure has a PNG and PDF checksum in results/lec_climatology_corrected/figure_manifest.csv. "
            "The complete input hashes and pinned toolkit commits are recorded in the adjacent provenance.json. "
            "The workflow is scripts/article_figures/generate.py; this report is built by "
            "scripts/article_figures/build_report.py.", styles["BodySmall"],
        ),
    ])

    output.parent.mkdir(parents=True, exist_ok=True)
    document.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

