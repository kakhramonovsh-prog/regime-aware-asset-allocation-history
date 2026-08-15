# Regime-Aware Volatility Forecasting and Dynamic Asset Allocation

**Evidence from U.S. Financial Markets**

Empirical research project. Status: **design preregistered
(`v0.2.0-preregistered`); Phase 4 EDA complete (`v0.3.0-eda`,
[report](outputs/phase4_eda_report.md)); volatility and regime modelling
next.** No strategy results exist yet, and none will be reported until
the out-of-sample experiments have run.

## Research question

Does conditioning a risk-based allocation on latent market states
improve out-of-sample risk-adjusted performance, beyond what dynamic
covariance estimation alone delivers?

## Preregistered design

The full empirical design was frozen **before any model was estimated**
(git tag `v0.2.0-preregistered`): hypothesis, primary comparison,
sample split, information/execution timeline, model specifications,
cost convention, and the complete robustness grid.

- Prose: [docs/research_design.md](docs/research_design.md)
- Machine-readable: [config/analysis_plan.yaml](config/analysis_plan.yaml)
- Enforcement: `tests/test_analysis_plan.py` fails if the runtime
  configuration drifts from the frozen plan.

The primary comparison is regime-aware minimum variance against
**rolling Ledoit-Wolf minimum variance** (the closest non-regime
strategy), net of 10 bps costs, so any headline improvement is
attributable to regime conditioning rather than to dynamic covariance
estimation. Equal weight and 60/40 remain as economic benchmarks.

## Motivation

Static allocations hold risk exposure fixed while market risk moves in
persistent, identifiable states: volatility clusters, and equity-bond
correlations shift sign across stress episodes. If those states are
detectable in real time (using only information available at each
rebalance date) a portfolio that conditions its risk profile on the
estimated state may achieve a better risk-return trade-off after
transaction costs. Whether it does is an empirical question, and the
answer after costs is not obvious. This project tests it with a
walk-forward design built to exclude look-ahead bias.

## Methodology

1. **Volatility models.** Rolling historical, EWMA (RiskMetrics), and
   GARCH(1,1), compared out-of-sample with MAE, RMSE, and QLIKE.
2. **Regime identification.** Gaussian Hidden Markov Model on
   standardized market features (market return, realized volatility,
   lagged VIX, lagged yield-curve slope). Two states in the main
   specification; three states as robustness. Estimation is
   expanding-window, and only **filtered** probabilities (computed from
   data through the rebalance date) ever feed a trading decision;
   smoothed full-sample probabilities appear solely in labeled ex-post
   descriptive figures.
3. **Covariance estimation.** Sample, exponentially weighted, and
   Ledoit-Wolf shrinkage, with eigenvalue/condition-number diagnostics.
4. **Portfolio strategies (ablation ladder).** Equal weight → 60/40 →
   static minimum variance → rolling Ledoit-Wolf minimum variance →
   volatility-scaled minimum variance → regime-aware minimum variance,
   so each rung isolates one design ingredient. Long-only, fully
   invested, 40% max weight, no expected-return forecasting.
5. **Walk-forward backtest.** Monthly rebalancing with a strict
   timeline: signal at month-end close *t*, execution at the close of
   *t+1*, new weights earn returns from *t+1* to *t+2* onward, costs
   charged at execution. FRED series are lagged one extra trading day
   in signals. Costs of 10 bps (primary) with 0/5/20 bps sensitivity.
6. **Inference.** Bootstrap confidence intervals, HAC standard errors,
   and Sharpe-difference tests rather than visual comparison.
7. **Robustness.** Alternative windows, rebalance frequencies, cost
   levels, state counts, covariance estimators, weight limits, and
   subperiods (pre-2020, COVID, 2022 tightening).

## Data

Five liquid US-listed ETFs (SPY, QQQ, IWM, IEF, GLD) from Yahoo
Finance, plus VIX, Treasury yields, and the fed funds rate from FRED.
Daily, from GLD's 2004 inception (effective sample from early 2005).
Adjusted closes proxy total returns. Full sources, units, alignment
rules, and missing-value policy: [data/README.md](data/README.md).
Benchmark: 60% SPY / 40% IEF.

## Key findings

Not yet available. This section will be populated from generated
outputs after the walk-forward experiments and robustness checks have
run, whether or not the results favor the regime-aware strategies.

## Repository structure

```
├── config/          config.yaml (runtime) + analysis_plan.yaml (frozen preregistration)
├── docs/            research_design.md — preregistered empirical design
├── data/
│   ├── raw/         Vendor files exactly as downloaded (not committed)
│   ├── processed/   Aligned analysis panels (not committed)
│   ├── snapshots/   SHA-256 manifests freezing each data snapshot (committed)
│   └── README.md    Data dictionary, sources, missing-value policy
├── notebooks/       Exploration and exposition; call src/, never re-implement it
├── src/             All substantive code: loading, preprocessing, models,
│                    optimization, backtest, metrics, tests, plotting
├── tests/           pytest suite, incl. look-ahead detection tests
├── scripts/         Pipeline entry points (download → analysis → backtest → paper)
├── outputs/         Generated figures, tables, fitted models (not committed)
└── paper/           LaTeX source; every number generated by scripts
```

## Installation

Requires Python 3.12 (hmmlearn has no Python 3.14 wheels yet).

```bash
git clone <repo-url>
cd regime-aware-asset-allocation
python -m venv .venv
.venv/Scripts/activate        # Windows; source .venv/bin/activate on Unix
pip install -r requirements.txt
```

Or with conda: `conda env create -f environment.yml`.

## Reproduction

```bash
python scripts/download_data.py        # raw + processed data
python scripts/run_analysis.py         # EDA, volatility, regimes  (pending)
python scripts/run_backtest.py         # walk-forward experiments  (pending)
python scripts/generate_paper_outputs.py  # paper figures/tables   (pending)
```

`make data | analysis | backtest | paper | test | all` wraps the same
commands. Random seeds are fixed in `config/config.yaml`; dependency
versions are pinned in `requirements.txt`. Run the test suite with:

```bash
python -m pytest tests/
```

## Limitations (known at design time)

* **Universe selection is itself hindsight.** ETFs avoid single-name
  survivorship, but choosing these five funds in 2026 uses knowledge
  that they survived and stayed liquid. Results are conditional on the
  universe.
* Yahoo Finance data is free-vendor quality; adjusted closes can be
  restated. Download metadata pins each snapshot.
* Transaction costs are modelled as proportional spread costs; no
  market impact, taxes, or borrowing constraints.
* Two decades of daily data contain few independent regime cycles, so
  statistical power against the static benchmarks is limited. The
  inference section quantifies rather than hides this.

## Future research

Candidate extensions, deliberately out of scope for the first paper:
international assets, credit and commodity sleeves, jump-robust
realized volatility from intraday data, regime models with
time-varying transition probabilities, and vendor cross-validation
against CRSP/Tiingo.

## Citation

```
Kakhramonov, S. (2026). Regime-Aware Volatility Forecasting and
Dynamic Asset Allocation: Evidence from U.S. Financial Markets.
Working paper. https://github.com/<user>/regime-aware-asset-allocation
```

MIT License.
