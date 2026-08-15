"""Run the analysis pipeline. Implemented: Phase 4 (EDA), Phase 5
(volatility forecasting).

Usage::

    python scripts/run_analysis.py [--phase {4,5,all}] [--config ...]

Every phase refuses to run unless the data on disk matches the frozen
SHA-256 snapshot manifest, and writes a provenance manifest tying every
artifact to the git commit, config hash, and data hashes.

Phase 5 estimates volatility models only (through each rebalance date);
no portfolio returns, regime model, or strategy selection is computed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from src import data_loader, eda, preprocessing as prep, visualization as viz  # noqa: E402
from src import volatility as vol  # noqa: E402

SNAPSHOT_MANIFEST = PROJECT_ROOT / "data" / "snapshots" / "manifest_2026-08-06.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config" / "config.yaml"))
    parser.add_argument("--phase", choices=["4", "5", "6", "all"], default="all")
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

    if args.phase in ("4", "all"):
        run_phase4(config, plan, prices, macro)
    if args.phase in ("5", "all"):
        run_phase5(config, plan, prices)
    if args.phase in ("6", "all"):
        run_phase6(config, plan, prices, macro)


def run_phase4(config: dict, plan: dict, prices: pd.DataFrame, macro: pd.DataFrame) -> None:
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
    manifest_path = eda.write_phase_manifest(
        artifacts, PROJECT_ROOT, SNAPSHOT_MANIFEST,
        PROJECT_ROOT / "outputs" / "eda_manifest.json",
    )
    print(f"\nProvenance manifest: {manifest_path.relative_to(PROJECT_ROOT)}")
    print("Phase 4 complete. Descriptive analysis only: no volatility model, "
          "HMM, portfolio optimization, or backtest was estimated or examined.")


def run_phase5(config: dict, plan: dict, prices: pd.DataFrame) -> None:
    """Volatility forecasting per the frozen Phase 5 specification."""
    returns = prep.log_returns(prices)
    cfg = vol.VolatilityConfig(
        hist_window=config["volatility_models"]["hist_window_days"],
        ewma_lambda=config["volatility_models"]["ewma_lambda"],
        min_observations=plan["volatility"]["min_observations"],
        variance_floor_daily=float(plan["volatility"]["variance_floor_daily"]),
    )
    n_dates = len(vol.month_end_rebalance_dates(returns.index, cfg.min_observations))
    print(f"\nPhase 5: fitting 3 models x {len(returns.columns)} assets x "
          f"{n_dates} month-end origins (GARCH refits take a few minutes)...")

    forecasts = vol.build_volatility_forecasts(returns, cfg)

    forecasts_dir = PROJECT_ROOT / "outputs" / "forecasts"
    tables_dir = PROJECT_ROOT / "outputs" / "tables"
    figures_dir = PROJECT_ROOT / "outputs" / "figures"
    forecasts_dir.mkdir(parents=True, exist_ok=True)
    artifacts: list[Path] = []

    fpath = forecasts_dir / "volatility_forecasts.parquet"
    forecasts.to_parquet(fpath, index=False)
    artifacts.append(fpath)
    print(f"  forecasts {fpath.name}  ({len(forecasts)} rows)")

    losses = vol.loss_table(forecasts, oos_start=plan["sample"]["oos_start"])
    lpath = tables_dir / "volatility_loss_by_asset.csv"
    losses.to_csv(lpath, index=False, float_format="%.6g")
    artifacts.append(lpath)
    print(f"  table  {lpath.name}")

    comparisons = pd.concat(
        [
            vol.diebold_mariano(forecasts, a, b)
            for a, b in [("ewma", "hist63"), ("garch11", "hist63"), ("garch11", "ewma")]
        ],
        ignore_index=True,
    )
    # Holm adjustment across the full family of 15 comparisons
    # (secondary column; unadjusted HAC(3) p-values are unchanged).
    comparisons["p_holm"] = vol.holm_adjust(comparisons["p_value"])
    cpath = tables_dir / "forecast_comparisons.csv"
    comparisons.to_csv(cpath, index=False, float_format="%.6g")
    artifacts.append(cpath)
    print(f"  table  {cpath.name}")

    garch_log = forecasts[forecasts["model"] == "garch11"][
        ["date", "asset", "horizon_days", "converged", "substituted", "floored"]
    ]
    gpath = tables_dir / "volatility_estimation_log.csv"
    garch_log.to_csv(gpath, index=False)
    artifacts.append(gpath)
    n_sub = int(garch_log["substituted"].sum())
    print(f"  table  {gpath.name}  (GARCH substitutions: {n_sub}/{len(garch_log)})")

    fig = viz.fig_forecasts_vs_realized(
        forecasts, "SPY", figures_dir / "forecasts_vs_realized_spy.png"
    )
    artifacts.append(fig)
    print(f"  figure {fig.name}")

    manifest_path = eda.write_phase_manifest(
        artifacts, PROJECT_ROOT, SNAPSHOT_MANIFEST,
        PROJECT_ROOT / "outputs" / "phase5_manifest.json",
        phase="5-volatility",
        note=(
            "Volatility forecasting only, estimated through each rebalance "
            "date. No portfolio returns, regime model, or strategy selection "
            "was computed or examined. EWMA remains the portfolio-feeding "
            "model regardless of this comparison (fixed ex ante)."
        ),
    )
    print(f"\nProvenance manifest: {manifest_path.relative_to(PROJECT_ROOT)}")
    print("Phase 5 complete. No portfolio returns or strategy selection examined.")


def run_phase6(config: dict, plan: dict, prices: pd.DataFrame, macro: pd.DataFrame) -> None:
    """Expanding-window HMM regime identification (no allocation work)."""
    from src import regimes as rg

    cfg = rg.HMMConfig(
        n_states=config["regimes"]["n_states_main"],
        n_init=config["regimes"]["n_initializations"],
        seed_start=config["regimes"]["init_seeds_start"],
        min_occupancy=config["regimes"]["min_state_occupancy"],
        min_observations=plan["volatility"]["min_observations"],
    )
    features = rg.build_features(
        prices, macro, macro_lag_days=config["data"]["macro_signal_lag_days"]
    )
    returns_index = prep.log_returns(prices).index
    # Primary sample starts at the preregistered first signal origin
    # (December 2009 month-end -> first execution 2010-01-04), NOT at
    # the earliest date satisfying the minimum-observation rule.
    rebalance_dates = rg.rebalance_origins(
        returns_index,
        first_signal_after=plan["sample"]["training_end"],
        min_observations=cfg.min_observations,
    )

    regimes_dir = PROJECT_ROOT / "outputs" / "regimes"
    figures_dir = PROJECT_ROOT / "outputs" / "figures"
    regimes_dir.mkdir(parents=True, exist_ok=True)
    artifacts: list[Path] = []

    print(f"\nPhase 6: {cfg.n_states}-state HMM, {len(rebalance_dates)} monthly refits "
          f"x {cfg.n_init} starts (seeds {cfg.seed_start}-{cfg.seed_start + cfg.n_init - 1})")
    print(f"  first signal origin {rebalance_dates[0].date()} "
          f"(preregistered), last {rebalance_dates[-1].date()}")
    out = rg.run_expanding_hmm(features, rebalance_dates, cfg, verbose=True)

    params = rg.implementation_parameters(cfg, features, str(rebalance_dates[0].date()))

    realtime = out["realtime"]
    rt_path = regimes_dir / "realtime_probabilities.parquet"
    realtime.to_parquet(rt_path, index=False)
    artifacts.append(rt_path)
    print(f"  regimes {rt_path.name}  ({len(realtime)} dates, "
          f"{int(realtime['classified_high_vol'].sum())} classified high-vol)")

    for name, frame in (
        ("all_initializations.csv", out["initializations"]),
        ("selected_fit_diagnostics.csv", out["diagnostics"]),
        ("model_revision_stability.csv", out["revisions"]),
        ("implementation_parameters.csv", params),
    ):
        path = regimes_dir / name
        frame.to_csv(path, index=False, float_format="%.6g")
        artifacts.append(path)
        print(f"  regimes {name}")

    tpath = regimes_dir / "transition_matrices.parquet"
    out["transitions"].to_parquet(tpath, index=False)
    artifacts.append(tpath)
    print(f"  regimes {tpath.name}")

    # State characteristics: feature means conditional on the real-time
    # classification (descriptive; uses stored real-time labels only).
    labels = realtime.set_index("date")["classified_high_vol"]
    joined = features.reindex(labels.index).join(labels)
    characteristics = joined.groupby("classified_high_vol").agg(["mean", "std", "count"])
    characteristics.columns = ["_".join(c) for c in characteristics.columns]
    cpath = regimes_dir / "state_characteristics.csv"
    characteristics.to_csv(cpath, float_format="%.6g")
    artifacts.append(cpath)
    print(f"  regimes {cpath.name}")

    # Stability diagnostics, split into two distinct concepts:
    #   (a) parameter dispersion + model revision  -> model stability
    #   (b) state evolution (endpoint prob movement) -> market conditions
    diagnostics = out["diagnostics"]
    revisions = out["revisions"]
    stability_rows = []
    for column in [c for c in diagnostics.columns if c.startswith(
            ("occupancy_s", "persistence_s", "n_eff_s", "expected_duration_s",
             "mean_realized_vol_s"))]:
        # Expected duration is infinite when a state is absorbing
        # (persistence = 1). Summarize finite values and count the rest
        # rather than letting inf swallow the whole row.
        series = diagnostics[column]
        finite = series[np.isfinite(series)]
        stability_rows.append({
            "concept": "parameter dispersion across refits", "quantity": column,
            "mean": finite.mean(), "std": finite.std(ddof=1),
            "min": finite.min(), "max": finite.max(),
            "n_non_finite": int((~np.isfinite(series)).sum()),
        })
    for column in ("mean_abs_prob_revision", "max_abs_prob_revision",
                   "prob_revision_corr", "classification_agreement",
                   "mean_drift_l2", "transmat_drift_l1"):
        series = revisions[column]
        stability_rows.append({
            "concept": "model revision (same overlapping window)", "quantity": column,
            "mean": series.mean(), "std": series.std(ddof=1),
            "min": series.min(), "max": series.max(),
        })
    evolution = realtime["prob_change_vs_prev_month"].dropna().abs()
    stability_rows.append({
        "concept": "state evolution (market conditions, NOT instability)",
        "quantity": "abs_monthly_change_in_endpoint_prob",
        "mean": evolution.mean(), "std": evolution.std(ddof=1),
        "min": evolution.min(), "max": evolution.max(),
    })
    counts = [
        ("n_refits", len(realtime)),
        ("n_classification_changes", int(realtime["classification_changed"].sum())),
        ("n_selected_seed_changes", int(revisions["selected_seed_changed"].sum())),
        ("n_guard_triggered", int(realtime["guard_triggered"].sum())),
        ("n_failed_initializations", int((~out["initializations"]["usable"]).sum())),
        ("n_refits_with_multiple_fits_in_selection_tol",
         int(out["initializations"].groupby("date")["within_selection_tol"].sum().gt(1).sum())),
    ]
    stability = pd.concat([
        pd.DataFrame(stability_rows),
        pd.DataFrame([{"concept": "counts", "quantity": q, "mean": v} for q, v in counts]),
    ], ignore_index=True)
    spath = regimes_dir / "stability_diagnostics.csv"
    stability.to_csv(spath, index=False, float_format="%.6g")
    artifacts.append(spath)
    print(f"  regimes {spath.name}")

    # Distinctiveness ONLY - not evidence of predictive or economic value.
    distinct = rg.distinctiveness_diagnostic(realtime, features)
    tcpath = regimes_dir / "distinctiveness_diagnostic.csv"
    distinct.to_csv(tcpath, index=False, float_format="%.6g")
    artifacts.append(tcpath)
    print(f"  regimes {tcpath.name}")

    # Feature ablations (preregistered robustness): drop VIX, drop RV.
    print("  running feature ablations (drop VIX, drop realized vol)...")
    ablation_rows = []
    for label, drop in (("drop_vix", "log_vix_lag1"),
                        ("drop_realized_vol", "realized_vol_21d")):
        alt = rg.run_ablation(features, drop, rebalance_dates, cfg)
        ablation_rows.append(rg.classification_agreement(realtime, alt, label))
    ablations = pd.DataFrame(ablation_rows)
    apath = regimes_dir / "feature_ablations.csv"
    ablations.to_csv(apath, index=False, float_format="%.6g")
    artifacts.append(apath)
    print(f"  regimes {apath.name}")

    # Ex-post smoothed path (descriptive only, stored separately).
    expost = rg.fit_expost_smoothed(features, cfg)
    epath = regimes_dir / "expost_smoothed_probabilities.parquet"
    expost.to_parquet(epath, index=False)
    artifacts.append(epath)
    print(f"  regimes {epath.name}  (EX-POST, never a trading signal)")

    fig = viz.fig_regime_probabilities(
        realtime, expost, features, figures_dir / "regime_probabilities.png"
    )
    artifacts.append(fig)
    print(f"  figure {fig.name}")

    manifest_path = eda.write_phase_manifest(
        artifacts, PROJECT_ROOT, SNAPSHOT_MANIFEST,
        PROJECT_ROOT / "outputs" / "phase6_manifest.json",
        phase="6-regimes",
        note=(
            "HMM regime identification only. Real-time signals are filtered "
            "probabilities from models fit through each rebalance date; "
            "ex-post smoothed probabilities are stored separately and are "
            "descriptive only. No covariance estimation, portfolio "
            "optimization, or strategy performance was computed or examined."
        ),
    )
    print(f"\nProvenance manifest: {manifest_path.relative_to(PROJECT_ROOT)}")
    print("Phase 6 complete. No covariance, optimization, or portfolio results examined.")


if __name__ == "__main__":
    main()
