# Phase 5 — Volatility Forecasting Report

**Generated from:** config SHA-256 `54ccd33d…855d6c` · data snapshot
`manifest_2026-08-06.json` · git commit per
[phase5_manifest.json](phase5_manifest.json)
**Run:** 2026-08-15, `python scripts/run_analysis.py --phase 5`
**Scope:** volatility models only, estimated through each rebalance
date. **No portfolio returns, regime model, or strategy selection was
computed or examined.** All numbers below are read from the generated
tables; per-artifact hashes are in the manifest.

---

## Setup (as frozen)

Three models — 63-day rolling historical, EWMA (λ = 0.94, seeded with
the first 63 days' sample variance), GARCH(1,1) with normal innovations
refit at every origin — each estimated on expanding windows of daily
log returns **through the forecast origin only**. Forecast object:
integrated variance of the next holding period (trading days after the
month-end origin through the next month-end), evaluated against
realized integrated variance (sum of squared daily log returns).
249 month-end origins per asset, 2005-11-30 to 2026-06-30 (the final
partial month is excluded); identical dates for all models, enforced by
an alignment assertion. Losses: QLIKE primary, MAE/RMSE (variance
units) secondary. Daily variance floor 1e-8. Implementation choices
documented in `src/volatility.py` before results were seen: zero-mean
GARCH on returns scaled by 100; DM tests with HAC(3) standard errors.

## Estimation diagnostics

All **1,245 GARCH refits converged (0 substitutions, 0 floored
forecasts)** — `volatility_estimation_log.csv`. The EWMA fallback path
exists and is unit-tested, but was never triggered on this data.

## Results (`volatility_loss_by_asset.csv`)

Mean QLIKE, full evaluation window (249 months; OOS-2010+ subset in the
table, same ordering everywhere):

| Asset | Hist63 | EWMA | GARCH(1,1) | Lowest |
|---|---|---|---|---|
| SPY | 0.544 | 0.424 | **0.326** | GARCH |
| QQQ | 0.421 | 0.338 | **0.271** | GARCH |
| IWM | 0.384 | 0.284 | **0.235** | GARCH |
| GLD | 0.287 | 0.270 | **0.224** | GARCH |
| IEF | 0.173 | 0.177 | **0.158** | GARCH |

**GARCH(1,1) attains the lowest QLIKE for all five assets**, in both
the full window and the 2010+ subset, and it also leads MAE/RMSE for
most assets. Diebold-Mariano on QLIKE differentials
(`forecast_comparisons.csv`, HAC(3), n = 249):

- **GARCH vs hist63:** GARCH favored for all five; differences
  significant at the 5% level for SPY (p = 0.035), QQQ (p = 0.021), and
  GLD (p = 0.008); not significant for IWM (p = 0.11) or IEF (p = 0.17).
- **GARCH vs EWMA:** GARCH favored for all five; significant at 5% for
  SPY (p = 0.011), QQQ (p = 0.001), and IWM (p = 0.031); marginal for
  GLD (p = 0.059) and IEF (p = 0.066).
- **EWMA vs hist63:** EWMA ahead for four of five assets but **never
  significantly** (p = 0.12-0.45); hist63 is trivially ahead for IEF.

Caveats stated up front: 15 pairwise tests are reported with no
multiplicity correction because none of them is the preregistered
primary hypothesis (that is the Phase 9-11 portfolio comparison); with
~249 monthly observations and volatility-clustered losses, p-values
near 0.05 deserve little weight. The qualitative pattern — GARCH first,
EWMA second, rolling historical last — is consistent across assets and
subwindows, which matters more than any single p-value.

## The preregistration consequence, stated plainly

The frozen plan fixed **EWMA as the portfolio-feeding model regardless
of this comparison** (chosen ex ante for determinism and zero
convergence risk). The comparison now says GARCH forecasts holding-
period variance better. Both statements stand:

1. The volatility-scaled strategy in the main analysis uses EWMA,
   exactly as preregistered. This result does not and cannot promote
   GARCH into the main specification.
2. A GARCH-fed variant belongs in the robustness analysis (the frozen
   grid already lists "different volatility models"), where it will be
   labeled robustness, not headline.

This is the designed behavior of the preregistration: a better-looking
alternative discovered after the freeze changes the robustness section,
never the main specification.

## Reading the figure

`forecasts_vs_realized_spy.png` (annualized-vol transform for
readability; losses are computed on variances): all three forecasts
lag realized volatility at crisis onsets — necessarily, being formed
before the period they forecast — and the 63-day historical model both
arrives latest at spikes and decays slowest afterward (visible after
2008-09, 2011, 2020), which is the mechanical source of its QLIKE
deficit. GARCH tracks the post-spike decay best; that pattern, not
level accuracy in calm periods, is where its edge comes from.

## Artifacts

`outputs/forecasts/volatility_forecasts.parquet` (3,735 rows: 249
origins x 5 assets x 3 models, forecasts + realized targets + flags),
`outputs/tables/volatility_loss_by_asset.csv`,
`outputs/tables/forecast_comparisons.csv`,
`outputs/tables/volatility_estimation_log.csv`,
`outputs/figures/forecasts_vs_realized_spy.png`,
[phase5_manifest.json](phase5_manifest.json) (SHA-256 of each artifact,
git commit, config and data hashes). Reproduce:
`python scripts/run_analysis.py --phase 5` (refuses to run off-snapshot).
Tests: 12 Phase 5 unit tests cover the EWMA recursion, QLIKE formula,
holding-period alignment, causality under future perturbation, the
GARCH failure/substitution path, and the variance floor.
