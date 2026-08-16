# Phase 12 — Robustness

**Generated from:** config SHA-256 · data snapshot `manifest_2026-08-06.json` ·
git commit per [phase12_manifest.json](phase12_manifest.json)
**Run:** 2026-08-16, `python scripts/run_robustness.py`

Thirteen specifications, each varying **one factor at a time** from the
primary model. No Cartesian product was constructed. Every specification
uses net returns at 10 bps; the grid contains no cost-varying case, as
cost sensitivity belongs to the Phase 11 secondary family.

**None of the results below changes the primary conclusion.** The
preregistered hypothesis was not supported in Phase 11, and no
robustness specification may be promoted into the headline.

---

## 1. The grid

Ordered as declared in `build_specifications()` — a conceptual ordering
fixed before any result was seen, never sorted by performance.

| # | Specification | Factor | ΔSharpe | 95% CI | Contains 0 | Sign = primary | p (unadj.) | p (Holm) |
|---|---|---|---|---|---|---|---|---|
| 1 | **primary** | — | **+0.0210** | [−0.075, +0.115] | Yes | — | 0.327 | *outside family* |
| 2 | hmm_3_states | HMM states | **−0.0284** | [−0.107, +0.048] | Yes | **No** | 0.763 | 1.000 |
| 3 | drop_vix | feature set | +0.0467 | [−0.046, +0.138] | Yes | Yes | 0.161 | 1.000 |
| 4 | drop_realized_vol | feature set | **−0.0235** | [−0.108, +0.059] | Yes | **No** | 0.708 | 1.000 |
| 5 | rolling_5y_window | estimation window | +0.0224 | [−0.063, +0.108] | Yes | Yes | 0.300 | 1.000 |
| 6 | **cap_30pct** | weight cap | **+0.0504** | **[+0.009, +0.093]** | **No** | Yes | **0.011** | **0.133** |
| 7 | cap_50pct | weight cap | +0.0169 | [−0.075, +0.108] | Yes | Yes | 0.351 | 1.000 |
| 8 | neff_kappa_30 | shrinkage | +0.0221 | [−0.075, +0.117] | Yes | Yes | 0.321 | 1.000 |
| 9 | neff_kappa_120 | shrinkage | +0.0191 | [−0.074, +0.110] | Yes | Yes | 0.337 | 1.000 |
| 10 | core_universe | universe | +0.0160 | [−0.068, +0.100] | Yes | Yes | 0.351 | 1.000 |
| 11 | alt_seeds_100 | HMM seeds | +0.0205 | [−0.076, +0.114] | Yes | Yes | 0.330 | 1.000 |
| 12 | a2_accept_as_estimated | A2 rule | +0.0181 | [−0.078, +0.112] | Yes | Yes | 0.351 | 1.000 |
| 13 | a3_total_covariance | A3 formula | +0.0210 | [−0.075, +0.115] | Yes | Yes | 0.327 | 1.000 |

**Sign stability:** 11 of 13 positive, **2 negative**. **Interval
coverage:** 12 of 13 contain zero. **After Holm adjustment across the
twelve-specification robustness family, nothing survives** — every
adjusted p-value is 1.000 except cap-30 at 0.133.

The primary specification reproduced exactly (+0.0210, CI [−0.0748,
+0.1147], matching Phase 11 to four decimals on both bounds), confirming
that specifications sharing a sample length receive identical bootstrap
index matrices and that cross-specification differences therefore
reflect returns rather than Monte Carlo noise.

## 2. Sign instability: the two negative specifications

Two preregistered specifications **reverse the sign** of the estimate:

- **Three-state HMM: −0.0284.** With a third state the regime-aware
  strategy underperforms the comparator on the point estimate.
- **Dropping realized volatility: −0.0235.** Removing the feature that
  Phase 4 showed carries most of the volatility signal (VIX-RV
  correlation 0.87) also reverses the sign.

Neither reversal is significant — both intervals contain zero — but
sign instability across preregistered variations is itself evidence
about the fragility of the effect. A finding that flips direction when
the state count changes is not a robust finding. This cuts *against*
the cap-30 result rather than with it, and both are reported with equal
prominence.

Three-state HMM diagnostics (`hmm_diagnostics_by_spec.csv`) show the
model itself is healthy, so the reversal is not an artifact of a broken
fit:

| State | Occupancy | Min n_eff | Mean realized vol | Persistence |
|---|---|---|---|---|
| 0 (low) | 0.319 | 523 | 0.0999 | 0.9942 |
| 1 (**middle**) | **0.454** | 487 | 0.1367 | 0.9946 |
| 2 (high) | 0.228 | 157 | 0.3215 | 0.9857 |

The **middle state is not degenerate** (45.4% occupancy, well above the
5% threshold, minimum effective sample size 487), canonical low < medium
< high ordering holds at every refit, and zero initializations failed.
Five refits produced an absorbing transition row and were routed through
the Amendment A2 fallback as designed.

## 3. The 30% cap: decomposed before interpreted

Cap-30 is the only specification whose unadjusted interval excludes
zero (+0.0504, [+0.009, +0.093], p = 0.011). **It does not survive Holm
adjustment (p = 0.133).** Before attributing it to anything, both legs
were compared:

| Quantity | cap 30% | **primary 40%** | cap 50% |
|---|---|---|---|
| ΔSharpe | +0.0504 | +0.0210 | +0.0169 |
| Regime volatility | 9.09% | 7.71% | 6.83% |
| Comparator volatility | 9.06% | 7.88% | 6.97% |
| **Volatility difference** | **+0.0003** | **−0.0018** | −0.0014 |
| Regime half-turnover | **26.7%** | **54.2%** | 47.9% |
| Comparator half-turnover | 18.1% | 16.9% | 15.9% |
| Regime cost expenditure | 5.33 bps | 10.84 bps | 9.58 bps |
| **Regime cost penalty vs comparator** | **+1.72 bps** | **+7.45 bps** | +6.39 bps |
| Mean IEF weight | 0.299 | 0.399 | 0.499 |
| Effective N assets (regime) | 3.70 | 2.92 | 2.61 |

**The cap-30 advantage is a turnover and cost effect, not better regime
identification.** Three facts establish this:

1. **The volatility advantage disappears.** At a 30% cap the regime
   strategy is marginally *more* volatile than the comparator (+0.0003)
   where at 40% it was less volatile (−0.0018). The risk-reduction
   channel — the one the model is designed to exploit — is absent
   exactly where the Sharpe gain is largest.
2. **Regime turnover halves, the comparator's does not.** Regime
   half-turnover falls from 54.2% to 26.7% while the comparator moves
   from 16.9% to 18.1%. A tighter cap constrains how far the regime
   signal can move weights, so the strategy trades far less.
3. **The cost penalty collapses.** The regime strategy's cost
   disadvantage versus the comparator falls from **+7.45 bps to
   +1.72 bps per year** — a 5.7 bps relative improvement. On a ~9%
   volatility portfolio that is worth roughly 0.06 Sharpe, the right
   order of magnitude for the observed +0.029 change.

Consistently, the CAGR difference rises from +0.0002 at the 40% cap to
+0.0053 at 30%, while the drawdown difference stays negligible — the
gain arrives through returns retained by trading less, not through risk
reduction. The cap also forces diversification (effective assets 3.70
vs 2.92) and mechanically lowers the IEF concentration that binds at
every origin.

**Wording for the paper:**

> Under the preregistered 30% weight-cap sensitivity, the regime-aware
> strategy produced a larger positive Sharpe difference and an
> unadjusted interval excluding zero. This result is secondary, belongs
> to a multi-specification robustness family, and does not alter the
> unsupported primary superiority hypothesis. It does not survive Holm
> adjustment across that family (p = 0.133), and decomposition shows it
> arises from constrained turnover and the resulting cost saving rather
> than from improved regime identification: the volatility advantage
> vanishes at the tighter cap.

The interesting economic content is therefore about **how portfolio
constraints interact with the cost of acting on a regime signal**, not
about the signal's quality.

## 4. Specifications that barely move the estimate

Several preregistered variations leave the result essentially unchanged,
which is informative in its own right:

- **A3 total-covariance mixture: +0.0210**, identical to the primary to
  four decimals. This confirms the Phase 7 measurement that the omitted
  between-state mean term is at most 0.16% of the within-state mixture.
  The A3 simplification is immaterial.
- **Shrinkage thresholds κ = 30 / 120: +0.0221 / +0.0191.** Even κ = 120,
  which Phase 7 flagged as potentially material (α falling from 0.879 to
  0.784 at minimum n_eff), moves the estimate by only 0.002.
- **Alternative seed block (100-115): +0.0205** versus +0.0210. Despite
  the selected seed changing at 152 of 199 refits in Phase 6, the
  economic result is unaffected — the 16-start protocol is doing its job.
- **A2 accept-as-estimated: +0.0181.** Accepting the four absorbing fits
  rather than falling back changes the estimate by 0.003, so the
  Amendment A2 policy choice is not driving anything.

## 5. Subperiods (descriptive only)

Sliced from the existing primary paths. **These are descriptive; no
inference is performed and no subperiod may enter the headline.**

| Subperiod | Days | ΔSharpe | ΔVolatility |
|---|---|---|---|
| Full out-of-sample | 4,173 | +0.0210 | −0.0018 |
| Pre-2020 | 2,516 | +0.1052 | −0.0004 |
| COVID (2020) | 232 | +0.0597 | −0.0040 |
| 2022 tightening | 460 | **−0.0638** | −0.0012 |
| Post-2020 | 1,657 | **−0.0756** | −0.0032 |

The pre-2020 estimate is five times the full-sample figure and the
post-2020 estimate is negative. With 232 days in the COVID slice and 460
in the tightening slice, these are far too small for inference, and the
sign disagreement between halves of the sample is a further reason to
treat the full-sample point estimate cautiously. **No favorable
subperiod is promoted.**

## 6. Failure accounting (all specifications, zeros included)

Across all 13 specifications: **zero HMM initialization failures, zero
optimizer failures, zero PSD corrections.** Guard events and A2
fallbacks occur only where expected — four absorbing-transition
fallbacks in the two-state specifications and five in the three-state
model, all routed through the documented rule.

## 7. Verification

`closing_checks.csv` records eleven closing conditions, **all passed**:
Holm input is the centered-null p-value (never the naive fraction below
zero); the Phase 11 primary sits outside the adjusted family; all
specifications share the identical evaluation window (2010-01-04 to
2026-08-06, 4,173 days); the forest plot order is conceptual rather than
performance-sorted; three-state outputs report all three occupancies and
effective sample sizes with a non-degenerate middle state and verified
canonical ordering; failure counts appear on every row; and subperiods
carry a descriptive-only label.

## 8. Artifacts

`outputs/robustness/robustness_grid.csv` (13 specifications, full
precision), `hmm_diagnostics_by_spec.csv`, `subperiod_descriptive.csv`,
`closing_checks.csv`, `run_log.txt`, per-specification checkpoints in
`partial/`; `outputs/figures/robustness_forest.png`;
[phase12_manifest.json](phase12_manifest.json).

Reproduce with `python scripts/run_robustness.py` (resumes from
checkpoints; `--force` recomputes) followed by
`python scripts/verify_robustness.py`.
