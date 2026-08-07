"""Volatility forecasting models (Phase 5 — not yet implemented).

Planned contents:

* rolling historical volatility forecasts,
* EWMA (RiskMetrics, lambda from config) forecasts,
* GARCH(1,1) via the ``arch`` package with rolling/expanding refits,
* out-of-sample forecast evaluation: MAE, RMSE, QLIKE against a
  realized-volatility proxy.

Implementation begins after the data pipeline is confirmed working.
"""

from __future__ import annotations


def not_yet_implemented() -> None:
    """Placeholder so accidental imports fail loudly."""
    raise NotImplementedError("Phase 5: volatility models are not implemented yet")
