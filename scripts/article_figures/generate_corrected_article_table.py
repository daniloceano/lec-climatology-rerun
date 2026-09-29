#!/usr/bin/env python3
"""Recreate the article's LEC summary table with the corrected swell cache."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pandas as pd

REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY))

from scripts.article_figures.common import ENERGY_TERMS, EOF_TERMS, sha256_file  # noqa: E402


DEFAULT_CONFIG = REPOSITORY / "config" / "data_sources.toml"
TABLE_COLUMNS = ["Mean", "Median", "Std Dev", "Q25", "Q75", "IQR", "Range"]
LATEX_LABELS = {
    "Az": "Az",
    "Ae": "Ae",
    "Kz": "Kz",
    "Ke": "Ke",
    "Cz": "Cz",
    "Ca": "Ca",
    "Ck": "Ck",
    "Ce": "Ce",
    "BAz": "BAz",
    "BAe": "BAe",
    "BKz": "BKz",
    "BKe": "BKe",
    "BΦZ": r"$B\Phi Z$",
    "BΦE": r"$B\Phi E$",
    "Gz": "Gz",
    "Ge": "Ge",
    "∂Az/∂t (finite diff.)": r"$\frac{\partial A_z}{\partial t}$",
    "∂Ae/∂t (finite diff.)": r"$\frac{\partial A_e}{\partial t}$",
    "∂Kz/∂t (finite diff.)": r"$\frac{\partial K_z}{\partial t}$",
    "∂Ke/∂t (finite diff.)": r"$\frac{\partial K_e}{\partial t}$",
    "RGz": "RGz",
    "RKz": "RKz",
    "RGe": "RGe",
    "RKe": "RKe",
}
PLAIN_LABELS = {
    key: key.replace(" (finite diff.)", "") for key in LATEX_LABELS
}
CAPTION = (
    "Summary Statistics of Lorenz Energetics Components, computed as averages across "
    "the entire cyclone lifecycle: mean, median, standard deviation (std), 25th "
    "percentile (Q25), 75th percentile (Q75), interquantile range (IQR), and range. "
    "The IQR measures the range within which the central 50\\% of the values fall, "
    "while the range is computed as the difference between the maximum and minimum "
    "values. The units for the energy terms ($A_Z$, $A_E$, $K_Z$, and $K_E$) are "
    "$10^5 \\, J \\, m^{-2}$ and $W \\, m^{-2}$ for the remaining terms."
)


def git_head() -> str:
    return subprocess.check_output(
        ["git", "-C", str(REPOSITORY), "rev-parse", "HEAD"], text=True
    ).strip()


def resolve_repo_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else REPOSITORY / path


def read_config(path: Path) -> dict:
    with path.open("rb") as stream:
        return tomllib.load(stream)


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


def compute_statistics(cache: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(set(EOF_TERMS) - set(cache.columns))
    if missing:
        raise ValueError(f"corrected cache misses table columns: {missing}")
    if len(cache) != 15829 or cache["track_id"].nunique() != 3820:
        raise ValueError("corrected cache population does not match the validated rerun")

    rows = []
    for term in EOF_TERMS:
        values = pd.to_numeric(cache[term], errors="coerce").dropna()
        if term in ENERGY_TERMS:
            values = values / 1e5
        q25 = float(values.quantile(0.25))
        q75 = float(values.quantile(0.75))
        rows.append(
            {
                "term": term,
                "n": int(len(values)),
                "mean": float(values.mean()),
                "median": float(values.median()),
                "std_dev": float(values.std(ddof=1)),
                "q25": q25,
                "q75": q75,
                "iqr": q75 - q25,
                "range": float(values.max() - values.min()),
            }
        )
    return pd.DataFrame(rows)


def table_block(statistics: pd.DataFrame) -> str:
    rows = [
        r"\begin{table}[!htbp]",
        r"\centering",
        (
            r"\caption[Summary Statistics of Lorenz Energetics Components]{"
            + CAPTION
            + "}"
        ),
        r"\label{tab:lec_stats}",
        r"\begin{tabular}{lrrrrrrr}",
        r"\toprule",
        r"Term & Mean & Median & Std Dev & Q25 & Q75 & IQR & Range \\",
        r"\midrule",
    ]
    for record in statistics.itertuples(index=False):
        values = [
            record.mean,
            record.median,
            record.std_dev,
            record.q25,
            record.q75,
            record.iqr,
            record.range,
        ]
        rows.append(
            f"{LATEX_LABELS[record.term]} & "
            + " & ".join(f"{value:.2f}" for value in values)
            + r" \\"
        )
    rows.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    return "\n".join(rows) + "\n"


def markdown_table(statistics: pd.DataFrame) -> str:
    lines = [
        "# Corrected Table 1 — Lorenz energetics summary statistics",
        "",
        "Values use the same population unit and formatting as the article table: "
        "each cache row is a lifecycle-period mean; all 15,829 corrected rows are "
        "pooled. Energy terms are divided by $10^5$.",
        "",
        "| Term | Mean | Median | Std Dev | Q25 | Q75 | IQR | Range |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for record in statistics.itertuples(index=False):
        values = [
            record.mean, record.median, record.std_dev, record.q25,
            record.q75, record.iqr, record.range,
        ]
        lines.append(
            f"| {PLAIN_LABELS[record.term]} | "
            + " | ".join(f"{value:.2f}" for value in values)
            + " |"
        )
    return "\n".join(lines) + "\n"


def standalone_document(block: str) -> str:
    return "\n".join(
        [
            r"\documentclass[10pt]{article}",
            r"\usepackage[margin=0.65in]{geometry}",
            r"\usepackage{booktabs}",
            r"\usepackage{caption}",
            r"\pagestyle{empty}",
            r"\begin{document}",
            block.rstrip(),
            r"\end{document}",
            "",
        ]
    )


def extract_published_table(article_source: Path) -> str:
    text = article_source.read_text()
    label = text.index(r"\label{tab:lec_stats}")
    start = text.rfind(r"\begin{table}", 0, label)
    end = text.index(r"\end{table}", label) + len(r"\end{table}")
    if start < 0:
        raise ValueError("published Table 1 start not found")
    return text[start:end] + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    config = read_config(args.config)

    cache_spec = config["inputs"]["corrected_cache"]
    cache_path = resolve_repo_path(cache_spec["local"])
    verify_input(cache_path, cache_spec)
    cache = pd.read_parquet(cache_path)
    statistics = compute_statistics(cache)

    legacy_root = resolve_repo_path(config["article"]["legacy_source_root"])
    article_source = legacy_root / config["article"]["published_article_tex"]
    legacy_generator = legacy_root / "summary_statistics.py"
    if not article_source.is_file() or not legacy_generator.is_file():
        raise FileNotFoundError("frozen article table source is unavailable")

    original_root = resolve_repo_path(config["article"]["original_table_root"])
    corrected_root = resolve_repo_path(config["article"]["corrected_table_root"])
    results_root = resolve_repo_path(config["article"]["corrected_results_root"])
    original_root.mkdir(parents=True, exist_ok=True)
    corrected_root.mkdir(parents=True, exist_ok=True)
    results_root.mkdir(parents=True, exist_ok=True)

    original_tex = original_root / "table_01_lec_summary_statistics.tex"
    corrected_tex = corrected_root / "table_01_lec_summary_statistics.tex"
    standalone_tex = corrected_root / "table_01_lec_summary_statistics_standalone.tex"
    markdown = corrected_root / "table_01_lec_summary_statistics.md"
    csv_path = results_root / "table_01_lec_summary_statistics.csv"
    manifest_path = results_root / "table_01_manifest.json"

    original_tex.write_text(extract_published_table(article_source))
    block = table_block(statistics)
    corrected_tex.write_text(block)
    standalone_tex.write_text(standalone_document(block))
    markdown.write_text(markdown_table(statistics))
    statistics.to_csv(csv_path, index=False, float_format="%.10g")

    manifest = {
        "table": 1,
        "title": "Summary Statistics of Lorenz Energetics Components",
        "workflow": "published table layout with validated corrected rerun",
        "repository_commit_before_generation": git_head(),
        "corrected_cache": str(cache_path.relative_to(REPOSITORY)),
        "corrected_cache_sha256": sha256_file(cache_path),
        "corrected_cyclones": int(cache["track_id"].nunique()),
        "lifecycle_period_rows": int(len(cache)),
        "terms": int(len(statistics)),
        "method": (
            "pool all lifecycle-period means; sample standard deviation (ddof=1); "
            "Q25/Q75; IQR=Q75-Q25; range=max-min; energy terms divided by 1e5"
        ),
        "published_article_source": str(article_source),
        "published_article_source_sha256": sha256_file(article_source),
        "legacy_generator": str(legacy_generator),
        "legacy_generator_sha256": sha256_file(legacy_generator),
        "outputs": {
            str(path.relative_to(REPOSITORY)): sha256_file(path)
            for path in [original_tex, corrected_tex, standalone_tex, markdown, csv_path]
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "table": str(corrected_tex),
                "statistics": str(csv_path),
                "rows": len(statistics),
                "corrected_cyclones": 3820,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
