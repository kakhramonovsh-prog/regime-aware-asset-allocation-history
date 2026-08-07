"""Market regime identification via Hidden Markov Models (Phase 6 — not yet implemented).

Planned contents:

* Gaussian HMM (``hmmlearn``) on standardized features: market return,
  market volatility, VIX level, yield-curve slope,
* expanding-window estimation so the regime label at each rebalance
  date uses only data available at that date,
* 2-state main specification; 3-state comparison via AIC/BIC,
  stability, and economic interpretability,
* regime visualization through time.

Implementation begins after the data pipeline is confirmed working.
"""

from __future__ import annotations


def not_yet_implemented() -> None:
    """Placeholder so accidental imports fail loudly."""
    raise NotImplementedError("Phase 6: regime models are not implemented yet")
