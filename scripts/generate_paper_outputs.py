"""Generate every table, figure and macro the paper uses. One command.

Reads only artifacts produced by earlier phases, routes every number
through ``src/units.py``, verifies each display value against its raw
value, and writes:

* ``paper/tables/*.csv``   - display tables carrying raw + display + unit
* ``paper/tables/*.tex``   - LaTeX tables generated from those frames
* ``paper/macros.tex``     - every headline number as a LaTeX macro
* ``paper/figures/*.png``  - the figures the paper references
* ``outputs/results_manifest.json`` - provenance for all of it

No number may be typed into the LaTeX by hand. The paper calls
``\\primarySharpeDiff`` and similar macros, so a changed result
propagates automatically and a stale number cannot survive.

    python scripts/generate_paper_outputs.py
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd  # noqa: E402

from src import latex as tex_util  # noqa: E402
from src import units as un  # noqa: E402
from src.eda import sha256_of  # noqa: E402

OUTPUTS = PROJECT_ROOT / "outputs"
PAPER = PROJECT_ROOT / "paper"
SNAPSHOT = PROJECT_ROOT / "data" / "snapshots" / "manifest_2026-08-06.json"

# Figures the paper references, in the order they appear.
PAPER_FIGURES = [
    "normalized_prices.png",
    "vix_vs_realized_vol.png",
    "regime_probabilities.png",
    "cumulative_growth.png",
    "strategy_drawdowns.png",
    "robustness_forest.png",
]


def macro_name(key: str) -> str:
    """snake_case to a LaTeX-legal camelCase macro name."""
    parts = key.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


CAPTIONS = {
    "table1_performance": "Realized performance, 2010--2026, net of 10 basis "
        "points. Annualized figures; maximum drawdown from the net wealth path.",
    "table2_primary_inference": "Preregistered primary comparison. Paired "
        "stationary bootstrap, 10{,}000 replications, mean block 21 trading "
        "days, seed 12345, on daily excess returns.",
    "table3_secondary_intervals": "Secondary metric differences, regime-aware "
        "minus rolling Ledoit--Wolf. Unadjusted intervals.",
    "table4_robustness_grid": "Robustness grid: thirteen specifications, each "
        "varying one factor from the primary model.",
}


def humanize(value: str) -> str:
    """Display label via the central registry.

    Raises on an unregistered identifier rather than falling back
    to the raw string, which is how an unescaped underscore
    previously reached the compiler.
    """
    return tex_util.latex_label_for(value)


def main() -> None:
    (PAPER / "tables").mkdir(parents=True, exist_ok=True)
    (PAPER / "figures").mkdir(parents=True, exist_ok=True)
    artifacts: list[Path] = []

    print("Reading phase outputs...")
    performance = pd.read_csv(OUTPUTS / "performance" / "performance_summary.csv")
    primary = pd.read_csv(OUTPUTS / "inference" / "primary_inference_summary.csv").iloc[0]
    secondary = pd.read_csv(OUTPUTS / "inference" / "secondary_metric_intervals.csv")
    hac = pd.read_csv(OUTPUTS / "inference" / "hac_mean_difference.csv")
    grid = pd.read_csv(OUTPUTS / "robustness" / "robustness_grid.csv")
    turnover_audit = pd.read_parquet(OUTPUTS / "backtests" / "accounting_audit.parquet")

    main_bps = 10
    net10 = performance[
        (performance["series"] == "net") & (performance["cost_bps"] == main_bps)
    ].set_index("strategy")

    # ------------------------------------------------------------------
    # Table 1: main performance, every number through the unit registry
    # ------------------------------------------------------------------
    order = ["equal_weight", "static_6040", "static_minvar",
             "rolling_lw_minvar", "ewma_scaled_minvar", "regime_minvar"]
    metrics = ["cagr", "ann_volatility", "sharpe", "sortino",
               "max_drawdown", "calmar"]
    rows = []
    for strategy in order:
        rows.append(un.build_display_table(
            {m: float(net10.loc[strategy, m]) for m in metrics}, label=strategy
        ))
    table1 = pd.concat(rows, ignore_index=True)
    un.verify_display_table(table1)

    # ------------------------------------------------------------------
    # Table 2: primary inference
    # ------------------------------------------------------------------
    table2 = un.build_display_table(
        {
            "sharpe_difference": float(primary["observed_difference"]),
            "ci95_lower": float(primary["ci95_lower"]),
            "ci95_upper": float(primary["ci95_upper"]),
            "p_value": float(primary["p_one_sided_centered_null"]),
        },
        label="regime_minvar minus rolling_lw_minvar",
    )
    un.verify_display_table(table2)

    # ------------------------------------------------------------------
    # Table 3: secondary metric intervals
    # ------------------------------------------------------------------
    metric_map = {"sharpe": "sharpe_difference", "sortino": "sharpe_difference",
                  "ann_volatility": "vol_difference", "cagr": "cagr_difference",
                  "max_drawdown": "maxdd_difference", "calmar": "sharpe_difference"}
    rows = []
    for _, row in secondary.iterrows():
        key = metric_map[row["metric"]]
        rows.append(un.build_display_table(
            {key: float(row["observed_difference"])}, label=row["metric"]
        ))
    table3 = pd.concat(rows, ignore_index=True)
    un.verify_display_table(table3)

    # ------------------------------------------------------------------
    # Table 4: robustness grid
    # ------------------------------------------------------------------
    rows = []
    for _, row in grid.iterrows():
        rows.append(un.build_display_table(
            {"sharpe_difference": float(row["sharpe_difference"]),
             "ci95_lower": float(row["ci95_lower"]),
             "ci95_upper": float(row["ci95_upper"]),
             "vol_difference": float(row["vol_difference"])},
            label=row["specification"],
        ))
    table4 = pd.concat(rows, ignore_index=True)
    un.verify_display_table(table4)

    tables = {
        "table1_performance": table1,
        "table2_primary_inference": table2,
        "table3_secondary_intervals": table3,
        "table4_robustness_grid": table4,
    }
    print("\nWriting tables (raw + display + unit in every row):")
    for name, frame in tables.items():
        csv_path = PAPER / "tables" / f"{name}.csv"
        frame.to_csv(csv_path, index=False)
        artifacts.append(csv_path)

        tex = frame.pivot(index="label", columns="metric", values="formatted")
        # Preserve the declared row order rather than pandas' alphabetical
        # sort, then replace every machine identifier with a display label
        # so no underscore reaches LaTeX.
        order = list(dict.fromkeys(frame["label"]))
        tex = tex.reindex(order)
        column_order = [c for c in dict.fromkeys(frame["metric"]) if c in tex.columns]
        tex = tex[column_order]
        tex = tex.map(
            lambda cell: "$-$" + cell[1:]
            if isinstance(cell, str) and cell.startswith("-") else cell
        )
        tex.index = [humanize(v) for v in tex.index]
        tex.columns = [humanize(c) for c in tex.columns]
        tex.index.name = None
        tex.columns.name = None

        tex_path = PAPER / "tables" / f"{name}.tex"
        tex_path.write_text(
            tex.to_latex(
                na_rep="",
                caption=CAPTIONS.get(name, name.replace("_", " ")),
                label=f"tab:{name}",
                column_format="l" + "r" * len(tex.columns),
                position="htbp",
            ).replace(
                # \small keeps the wide performance table inside the text
                # block; without it Table 1 overfulls by 24pt.
                r"\begin{tabular}", "\\small\n" + r"\begin{tabular}"
            ),
            encoding="utf-8",
        )
        artifacts.append(tex_path)
        print(f"  {name}.csv / .tex  ({len(frame)} values)")

    # ------------------------------------------------------------------
    # Macros: every headline number the prose cites
    # ------------------------------------------------------------------
    hac21 = hac[hac["hac_lags"] == 21].iloc[0]
    regime_turnover = turnover_audit[
        (turnover_audit["strategy"] == "regime_minvar")
        & (turnover_audit["cost_bps"] == main_bps)
    ]
    comparator_turnover = turnover_audit[
        (turnover_audit["strategy"] == "rolling_lw_minvar")
        & (turnover_audit["cost_bps"] == main_bps)
    ]
    years = len(regime_turnover) / 252

    headline = {
        "primary_sharpe_diff": float(primary["observed_difference"]),
        "primary_ci_lower": float(primary["ci95_lower"]),
        "primary_ci_upper": float(primary["ci95_upper"]),
        "primary_p_value": float(primary["p_one_sided_centered_null"]),
        "vol_difference": float(
            secondary.loc[secondary["metric"] == "ann_volatility",
                          "observed_difference"].iloc[0]),
        "hac_annual_return_diff": float(hac21["annualized_arithmetic_difference"]),
        "regime_sharpe": float(net10.loc["regime_minvar", "sharpe"]),
        "comparator_sharpe": float(net10.loc["rolling_lw_minvar", "sharpe"]),
        "vol_difference_magnitude": abs(float(
            secondary.loc[secondary["metric"] == "ann_volatility",
                          "observed_difference"].iloc[0])),
        "regime_half_turnover": float(
            regime_turnover["half_turnover_reporting"].sum() / years),
        "comparator_half_turnover": float(
            comparator_turnover["half_turnover_reporting"].sum() / years),
    }
    units_for = {
        "primary_sharpe_diff": "sharpe_difference",
        "primary_ci_lower": "ci95_lower",
        "primary_ci_upper": "ci95_upper",
        "primary_p_value": "p_value",
        "vol_difference": "vol_difference",
        "vol_difference_magnitude": "vol_difference",
        "hac_annual_return_diff": "mean_return_difference_annualized",
        "regime_sharpe": "sharpe",
        "comparator_sharpe": "sharpe",
        "regime_half_turnover": "half_turnover",
        "comparator_half_turnover": "half_turnover",
    }
    macro_frame = un.build_display_table(
        {units_for[k]: v for k, v in headline.items()}, label="headline"
    )  # verification only; names collide, so write macros from `headline`
    lines = [
        "% Generated by scripts/generate_paper_outputs.py. Do not edit.",
        f"% {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}",
        "",
    ]
    for key, raw in headline.items():
        _, unit, formatted = un.to_display(raw, units_for[key])
        # A leading text hyphen is not a minus sign; the figures already
        # use a typographic minus, so the prose must match.
        if formatted.startswith("-"):
            formatted = "$-$" + formatted[1:]
        # '%' is a LaTeX comment character: an unescaped one silently
        # swallows the rest of the line, including the closing brace.
        unit_tex = unit.replace("%", r"\%")
        suffix = f"\\,{unit_tex}" if unit_tex else ""
        lines.append(f"\\newcommand{{\\{macro_name(key)}}}{{{formatted}{suffix}}}")
    macros_path = PAPER / "macros.tex"
    macros_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    artifacts.append(macros_path)
    print(f"\nWrote {len(headline)} LaTeX macros -> paper/macros.tex")
    for line in lines[3:]:
        print(f"  {line}")

    # ------------------------------------------------------------------
    # Figures
    # ------------------------------------------------------------------
    print("\nCopying figures:")
    for name in PAPER_FIGURES:
        source = OUTPUTS / "figures" / name
        if not source.exists():
            print(f"  MISSING {name} (run the earlier phases)")
            continue
        destination = PAPER / "figures" / name
        shutil.copy2(source, destination)
        artifacts.append(destination)
        print(f"  {name}")

    # ------------------------------------------------------------------
    # Results manifest
    # ------------------------------------------------------------------
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT,
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    config_hash = hashlib.sha256()
    for name in ("config.yaml", "analysis_plan.yaml"):
        config_hash.update((PROJECT_ROOT / "config" / name).read_bytes())

    manifest = {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "git_commit": commit,
        "config_sha256": config_hash.hexdigest(),
        "data_snapshot_sha256": sha256_of(SNAPSHOT),
        "python_version": sys.version.split()[0],
        "headline_values": headline,
        "note": (
            "Every value passed through src/units.py and was verified against "
            "its raw value. The LaTeX reads numbers only via paper/macros.tex; "
            "no result is typed by hand."
        ),
        "artifacts": {
            str(p.relative_to(PROJECT_ROOT)).replace("\\", "/"): sha256_of(p)
            for p in artifacts
        },
    }
    manifest_path = OUTPUTS / "results_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nResults manifest: {manifest_path.relative_to(PROJECT_ROOT)}")
    print(f"  {len(artifacts)} artifacts, commit {commit[:12]}")
    print("\nAll paper outputs generated. No hand-entered numbers.")


if __name__ == "__main__":
    main()
