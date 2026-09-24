#!/usr/bin/env python3
"""Build the full-population article-versus-corrected comparison report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
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

RESULTS_NAME = "article_comparison"


def page_footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#d4d8da"))
    canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#5f676b"))
    canvas.drawString(18 * mm, 9 * mm, "LEC climatology - published article versus corrected rerun")
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
    results_dir = root / "results" / RESULTS_NAME
    output = root / "docs" / "lec_climatology_article_before_after_report.pdf"

    manifest = pd.read_csv(results_dir / "figure_manifest.csv")
    provenance = json.loads((results_dir / "provenance.json").read_text())
    cluster_meta = json.loads((results_dir / "intense_pc_cluster_metadata.json").read_text())
    cluster_stats = pd.read_csv(results_dir / "intense_pc_cluster_statistics.csv")
    total_variance = pd.read_csv(results_dir / "eof_variance_total.csv")
    if len(manifest) != 20:
        raise ValueError(f"expected 20 figure files, found {len(manifest)}")

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#183b4e"),
            alignment=TA_LEFT,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#43545d"),
            spaceAfter=16,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#183b4e"),
            spaceBefore=6,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FigureTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#183b4e"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Caption",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8.4,
            leading=11.5,
            textColor=colors.HexColor("#33383b"),
            alignment=TA_CENTER,
            spaceBefore=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["BodyText"],
            fontSize=9.2,
            leading=13,
            textColor=colors.HexColor("#20272b"),
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Warning",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9.4,
            leading=13.5,
            textColor=colors.HexColor("#8a2d20"),
            backColor=colors.HexColor("#fff1ed"),
            borderColor=colors.HexColor("#d58473"),
            borderWidth=0.6,
            borderPadding=7,
            spaceBefore=5,
            spaceAfter=10,
        )
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=19 * mm,
        title="LEC climatology - published article versus corrected rerun",
        author="Danilo Couto de Souza",
        subject="Audit and reconstruction of Lorenz Energy Cycle climatology figures",
    )

    story = [
        Spacer(1, 8 * mm),
        Paragraph("LEC climatology: published article versus corrected rerun", styles["ReportTitle"]),
        Paragraph(
            "A figure-by-figure reconstruction using the complete archived legacy population and the validated LorenzCycleToolKit 2.0.0 rerun",
            styles["ReportSubtitle"],
        ),
        Table(
            [
                ["Before population", f"{provenance['legacy_cyclones']:,} cyclones / {provenance['legacy_rows']:,} lifecycle rows"],
                ["After population", f"{provenance['corrected_cyclones']:,} cyclones / {provenance['corrected_rows']:,} lifecycle rows"],
                ["Intense clustering", f"5 groups on PCs 1-8; n={cluster_meta['eligible_legacy_cyclones']:,} -> {cluster_meta['eligible_corrected_cyclones']:,}"],
                ["Article source commit", provenance["legacy_source_commit_audited"][:12]],
                ["Figure files", "20 PNG + 20 vector PDF"],
            ],
            colWidths=[52 * mm, 106 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8f1f4")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.8),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b8c6cc")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            ),
        ),
        Spacer(1, 7 * mm),
        Paragraph("Interpretation boundary", styles["Section"]),
        Paragraph(
            "This is the literal article-to-rerun comparison. Because the before and after populations differ, visible changes combine the toolkit correction and the change from 6,789 archived systems to 3,820 validated complete-lifecycle reruns. Use the separate paired 3,820-cyclone report when the objective is to isolate the correction alone.",
            styles["Warning"],
        ),
        Paragraph("Reproduction audit", styles["Section"]),
        Paragraph(
            "The legacy total-lifecycle EOF calculation uses all archived periods for every cyclone, matching the original source workflow. Primary-phase figures use the exact incipient, intensification, mature and decay rows. Corrected EOFs are fitted independently, then reordered and sign-aligned to the legacy loading patterns for visual comparison.",
            styles["BodySmall"],
        ),
        PageBreak(),
        Paragraph("Numerical landmarks", styles["Section"]),
    ]

    variance_table = [["EOF", "Before variance", "After variance", "Matched after rank", "Pattern correlation"]]
    for mode in range(1, 5):
        before = total_variance[(total_variance["version"] == "before") & (total_variance["eof"] == mode)].iloc[0]
        after = total_variance[(total_variance["version"] == "after") & (total_variance["eof"] == mode)].iloc[0]
        variance_table.append(
            [
                mode,
                f"{before.explained_variance_pct:.3f}%",
                f"{after.explained_variance_pct:.3f}%",
                int(after.matched_rank),
                f"{after.pattern_correlation:.3f}",
            ]
        )
    story.append(
        Table(
            variance_table,
            colWidths=[24 * mm, 34 * mm, 34 * mm, 37 * mm, 39 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#183b4e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.3),
                    ("ALIGN", (0, 1), (-1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#bcc6ca")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7f8")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        )
    )
    story.extend([Spacer(1, 7 * mm), Paragraph("Intense-cyclone groups", styles["Section"])])
    cluster_table = [["Version", "Cluster", "n", "Mean max. vorticity", "Median max. vorticity"]]
    for version in ("before", "after"):
        for row in cluster_stats[cluster_stats["version"] == version].sort_values("cluster").itertuples():
            cluster_table.append(
                [row.version, row.cluster, row.n, f"{row.max_vor42_mean:.2f}", f"{row.max_vor42_median:.2f}"]
            )
    story.append(
        Table(
            cluster_table,
            colWidths=[28 * mm, 24 * mm, 22 * mm, 44 * mm, 44 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#183b4e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.1),
                    ("ALIGN", (0, 1), (-1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#bcc6ca")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7f8")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 4.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
                ]
            ),
        )
    )

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

    story.extend(
        [
            Spacer(1, 8 * mm),
            Paragraph("Reproducibility record", styles["Section"]),
            Paragraph(
                "Input and output SHA-256 hashes, population counts, EOF matching diagnostics, cluster centers, assignments and the audited source commit are recorded under results/article_comparison. The paired control is kept separately under docs/paired_control/.",
                styles["BodySmall"],
            ),
        ]
    )
    document.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
