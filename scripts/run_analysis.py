"""Run the analysis pipeline. Currently implemented: Phase 4 (EDA).

Usage::

    python scripts/run_analysis.py [--config config/config.yaml]

Phase 4 refuses to run unless every data file on disk matches the
frozen SHA-256 snapshot manifest, and it writes an EDA manifest tying
every artifact to the git commit, config hash, and data hashes.

Descriptive only: no volatility model, HMM, optimization, or backtest
is estimated here. Phases 5-7 will extend this script.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from src import data_loader, eda, preprocessing as prep, visualization as viz  # noqa: E402

SNAPSHOT_MANIFEST = PROJECT_ROOT / "data" / "snapshots" / "manifest_2026-08-06.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config" / "config.yaml"))
    args = parser.parse_args()

    config = data_loader.load_config(args.config)
    with open(PROJECT_ROOT / "config" / "analysis_plan.yaml", encoding="utf-8") as fh:
        plan = yaml.safe_load(fh)

    # ------------------------------------------------------------------
    # Integrity gate: only the frozen snapshot may be analyzed.
    # ------------------------------------------------------------------
    eda.verify_snapshot(SNAPSHOT_MANIFEST, PROJECT_ROOT)
    print(f"Snapshot verified against {SNAPSHOT_MANIFEST.name}: all hashes match.")

    processed = PROJECT_ROOT / config["data"]["processed_dir"]
    prices = pd.read_csv(processed / "prices.csv", index_col="Date", parse_dates=True)
    macro = pd.read_csv(processed / "macro.csv", index_col="Date", parse_dates=True)
    raw_dir = PROJECT_ROOT / config["data"]["raw_dir"]
    raw_prices = data_loader.load_raw_prices(raw_dir, list(config["data"]["tickers"]))
    raw_macro = data_loader.load_raw_macro(raw_dir, list(config["data"]["fred_series"]))

    returns = prep.log_returns(prices)
    slope = prep.yield_curve_slope(macro)

    tables_dir = PROJECT_ROOT / "outputs" / "tables"
    figures_dir = PROJECT_ROOT / "outputs" / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    artifacts: list[Path] = []

    # ------------------------------------------------------------------
    # Tables
    # ------------------------------------------------------------------
    def save(df: pd.DataFrame, name: str) -> None:
        path = tables_dir / name
        df.to_csv(path, float_format="%.6f")
        artifacts.append(path)
        print(f"  table  {name}")

    print("\nGenerating tables:")
    save(eda.summary_statistics(prices), "summary_statistics.csv")
    save(eda.macro_summary(macro), "macro_summary.csv")
    save(eda.missingness_audit(raw_prices, raw_macro, prices, macro), "missingness_audit.csv")
    save(eda.staleness_audit(prices, macro), "staleness_audit.csv")
    save(eda.calendar_audit(prices.index), "calendar_audit.csv")

    corr, conditioning = eda.correlation_and_conditioning(returns)
    save(corr, "correlation_matrix.csv")
    save(conditioning, "correlation_conditioning.csv")

    feature_corr, vix_rv = eda.macro_feature_correlations(prices, macro)
    save(feature_corr, "macro_feature_correlations.csv")
    save(vix_rv, "vix_vs_realized_vol_stats.csv")

    periods = {"full_sample": (str(prices.index.min().date()), str(prices.index.max().date())),
               "training_window": (plan["sample"]["full_start"], plan["sample"]["training_end"])}
    periods.update({k: tuple(v) for k, v in plan["robustness_grid"]["subperiods"].items()})
    save(eda.subperiod_summaries(prices, macro, periods), "subperiod_summaries.csv")

    # ------------------------------------------------------------------
    # Figures
    # ------------------------------------------------------------------
    print("Generating figures:")
    rv = eda.realized_vol_series(prices, window=21)
    figures = [
        viz.fig_normalized_prices(prices, figures_dir / "normalized_prices.png"),
        viz.fig_return_distributions(returns, figures_dir / "return_distributions.png"),
        viz.fig_rolling_volatility(returns, figures_dir / "rolling_volatility.png"),
        viz.fig_rolling_correlations(returns, figures_dir / "rolling_correlations.png"),
        viz.fig_drawdowns(prices, figures_dir / "drawdowns.png"),
        viz.fig_macro_features(macro, slope, figures_dir / "macro_features.png"),
        viz.fig_vix_vs_realized(macro["VIXCLS"], rv, figures_dir / "vix_vs_realized_vol.png"),
    ]
    for f in figures:
        artifacts.append(f)
        print(f"  figure {f.name}")

    # ------------------------------------------------------------------
    # Provenance manifest
    # ------------------------------------------------------------------
    manifest_path = eda.write_eda_manifest(
        artifacts, PROJECT_ROOT, SNAPSHOT_MANIFEST,
        PROJECT_ROOT / "outputs" / "eda_manifest.json",
    )
    print(f"\nProvenance manifest: {manifest_path.relative_to(PROJECT_ROOT)}")
    print("Phase 4 complete. Descriptive analysis only: no volatility model, "
          "HMM, portfolio optimization, or backtest was estimated or examined.")


if __name__ == "__main__":
    main()
