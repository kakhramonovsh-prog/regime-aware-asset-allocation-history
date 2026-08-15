"""Publication figures for the EDA phase (matplotlib, saved to PNG).

Style rules applied throughout:

* One fixed color per asset across every figure (color follows the
  entity, never position): SPY blue, QQQ orange, IWM dark aqua, IEF
  violet, GLD dark magenta. This 5-slot set passes every palette check
  on the white figure surface (lightness band, chroma floor, adjacent
  CVD separation worst dE 8.4, normal-vision floor 27.1, and >= 3:1
  contrast for all five slots; validated with the palette script, not
  by eye). Legends plus CSV table views of every plotted series remain
  as secondary encoding.
* Single y-axis per panel, always. Recessive hairline grid, muted axis
  ink, no chartjunk.
* Every figure states its sample range in a footnote.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ASSET_COLORS = {
    "SPY": "#2a78d6",  # blue
    "QQQ": "#eb6834",  # orange
    "IWM": "#199e70",  # dark aqua
    "IEF": "#4a3aa7",  # violet
    "GLD": "#d55181",  # dark magenta
}
SERIES_1 = "#2a78d6"
SERIES_2 = "#eb6834"
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"

_RC = {
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": INK,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.labelsize": 9.5,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.5,
    "legend.frameon": False,
    "font.family": "sans-serif",
    "lines.linewidth": 1.4,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
}


def _footnote(fig: plt.Figure, index: pd.DatetimeIndex, extra: str = "") -> None:
    text = f"Sample: {index.min().date()} to {index.max().date()}. {extra}".strip()
    fig.text(0.01, -0.01, text, fontsize=7.5, color=MUTED, ha="left", va="top")


def _despine(ax: plt.Axes) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def fig_normalized_prices(prices: pd.DataFrame, path: Path) -> Path:
    """Total-return proxy history, indexed to 100, log scale."""
    normalized = prices / prices.iloc[0] * 100
    with plt.rc_context(_RC):
        fig, ax = plt.subplots(figsize=(10, 5.2))
        for asset in normalized.columns:
            ax.plot(normalized.index, normalized[asset],
                    color=ASSET_COLORS[asset], label=asset)
            ax.annotate(
                f" {asset} {normalized[asset].iloc[-1]:,.0f}",
                xy=(normalized.index[-1], normalized[asset].iloc[-1]),
                fontsize=8, color=ASSET_COLORS[asset], va="center",
            )
        ax.set_yscale("log")
        ax.set_yticks([100, 200, 400, 800, 1600])
        ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        ax.set_title("Cumulative growth of adjusted closes (total-return proxy), indexed to 100")
        ax.set_ylabel("Index level (log scale)")
        ax.margins(x=0.06)
        _despine(ax)
        ax.legend(loc="upper left", ncols=5)
        _footnote(fig, prices.index, "Dividend/split-adjusted closes; log y-axis.")
        fig.savefig(path)
        plt.close(fig)
    return path


def fig_return_distributions(returns: pd.DataFrame, path: Path) -> Path:
    """Daily log-return histograms with a matched-moment normal overlay."""
    with plt.rc_context(_RC):
        fig, axes = plt.subplots(2, 3, figsize=(11, 6), sharey=False)
        axes = axes.ravel()
        for i, asset in enumerate(returns.columns):
            ax = axes[i]
            r = returns[asset] * 100
            ax.hist(r, bins=120, density=True, color=ASSET_COLORS[asset], alpha=0.85)
            grid = np.linspace(r.min(), r.max(), 400)
            from scipy import stats as sps
            ax.plot(grid, sps.norm.pdf(grid, r.mean(), r.std(ddof=1)),
                    color=INK, linestyle="--", linewidth=1.0,
                    label="Normal (same mean/sd)")
            ax.set_title(asset)
            ax.set_xlabel("Daily log return (%)")
            ax.set_xlim(np.percentile(r, 0.05), np.percentile(r, 99.95))
            skew = sps.skew(r)
            kurt = sps.kurtosis(r, fisher=True)
            ax.text(0.02, 0.95, f"skew {skew:.2f}\nex.kurt {kurt:.1f}",
                    transform=ax.transAxes, fontsize=8, va="top", color=INK)
            _despine(ax)
            if i == 0:
                ax.legend(loc="upper right")
        axes[-1].axis("off")
        fig.suptitle("Daily log-return distributions vs normal benchmark",
                     fontsize=12, fontweight="bold")
        fig.tight_layout()
        _footnote(fig, returns.index, "x-axes trimmed at 0.05/99.95 percentiles for legibility.")
        fig.savefig(path)
        plt.close(fig)
    return path


def fig_rolling_volatility(returns: pd.DataFrame, path: Path,
                           windows: tuple[int, int] = (21, 63)) -> Path:
    """Stacked panels of annualized rolling volatility, one per window."""
    from src.preprocessing import rolling_volatility

    with plt.rc_context(_RC):
        fig, axes = plt.subplots(len(windows), 1, figsize=(10, 6.5), sharex=True)
        for ax, window in zip(axes, windows):
            vol = rolling_volatility(returns, window=window) * 100
            for asset in vol.columns:
                ax.plot(vol.index, vol[asset], color=ASSET_COLORS[asset],
                        label=asset, linewidth=1.1)
            ax.set_title(f"{window}-day rolling volatility (annualized)")
            ax.set_ylabel("Volatility (% p.a.)")
            _despine(ax)
        axes[0].legend(loc="upper right", ncols=5)
        fig.tight_layout()
        _footnote(fig, returns.index)
        fig.savefig(path)
        plt.close(fig)
    return path


def fig_rolling_correlations(returns: pd.DataFrame, path: Path, window: int = 63) -> Path:
    """63-day rolling correlation of SPY with each other asset."""
    from src.preprocessing import rolling_correlation

    others = [c for c in returns.columns if c != "SPY"]
    with plt.rc_context(_RC):
        fig, ax = plt.subplots(figsize=(10, 5))
        for asset in others:
            corr = rolling_correlation(returns["SPY"], returns[asset], window=window)
            ax.plot(corr.index, corr, color=ASSET_COLORS[asset],
                    label=f"SPY-{asset}", linewidth=1.1)
        ax.axhline(0, color=BASELINE, linewidth=0.9)
        ax.set_ylim(-1, 1)
        ax.set_title(f"{window}-day rolling correlation with SPY")
        ax.set_ylabel("Correlation")
        _despine(ax)
        ax.legend(loc="lower left", ncols=4)
        _footnote(fig, returns.index, "Daily log returns.")
        fig.savefig(path)
        plt.close(fig)
    return path


def fig_drawdowns(prices: pd.DataFrame, path: Path) -> Path:
    """Small-multiple drawdown curves, one panel per asset."""
    from src.preprocessing import drawdown_series

    dd = drawdown_series(prices) * 100
    with plt.rc_context(_RC):
        fig, axes = plt.subplots(len(dd.columns), 1, figsize=(10, 9), sharex=True)
        for ax, asset in zip(axes, dd.columns):
            ax.fill_between(dd.index, dd[asset], 0,
                            color=ASSET_COLORS[asset], alpha=0.75, linewidth=0)
            trough_date = dd[asset].idxmin()
            trough = dd[asset].min()
            ax.annotate(f"{asset}  min {trough:.0f}% ({trough_date.date()})",
                        xy=(0.005, 0.10), xycoords="axes fraction",
                        fontsize=8.5, color=INK)
            ax.set_ylim(min(-5, trough * 1.15), 2)
            ax.set_ylabel("%")
            _despine(ax)
        axes[0].set_title("Drawdown from running maximum (adjusted closes)")
        fig.tight_layout()
        _footnote(fig, prices.index)
        fig.savefig(path)
        plt.close(fig)
    return path


def fig_macro_features(macro: pd.DataFrame, slope: pd.Series, path: Path) -> Path:
    """Four-panel macro overview: VIX, Treasury yields, slope, fed funds."""
    with plt.rc_context(_RC):
        fig, axes = plt.subplots(4, 1, figsize=(10, 9.5), sharex=True)

        axes[0].plot(macro.index, macro["VIXCLS"], color=SERIES_1, linewidth=1.0)
        axes[0].set_title("VIX (CBOE Volatility Index, close)")
        axes[0].set_ylabel("Index points")

        axes[1].plot(macro.index, macro["DGS10"], color=SERIES_1,
                     linewidth=1.0, label="10-year")
        axes[1].plot(macro.index, macro["DGS2"], color=SERIES_2,
                     linewidth=1.0, label="2-year")
        axes[1].set_title("Treasury constant-maturity yields")
        axes[1].set_ylabel("% p.a.")
        axes[1].legend(loc="upper right", ncols=2)

        axes[2].plot(slope.index, slope, color=SERIES_1, linewidth=1.0)
        axes[2].axhline(0, color=BASELINE, linewidth=0.9)
        axes[2].set_title("Yield-curve slope (10y minus 2y)")
        axes[2].set_ylabel("Percentage points")

        axes[3].plot(macro.index, macro["DFF"], color=SERIES_1, linewidth=1.0)
        axes[3].set_title("Effective federal funds rate (DFF)")
        axes[3].set_ylabel("% p.a.")

        for ax in axes:
            _despine(ax)
        fig.tight_layout()
        _footnote(fig, macro.index, "Sources: FRED (VIXCLS, DGS10, DGS2, DFF).")
        fig.savefig(path)
        plt.close(fig)
    return path


def fig_vix_vs_realized(vix: pd.Series, rv: pd.Series, path: Path) -> Path:
    """VIX vs 21-day realized volatility: time overlay and scatter.

    Both series are annualized volatilities in percent, so a single
    shared y-axis is legitimate (never dual-axis).
    """
    aligned = pd.DataFrame({"VIX": vix, "RV21": rv}).dropna()
    corr = aligned["VIX"].corr(aligned["RV21"])
    with plt.rc_context(_RC):
        fig, (ax1, ax2) = plt.subplots(
            1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [2.1, 1]}
        )
        ax1.plot(aligned.index, aligned["VIX"], color=SERIES_1,
                 linewidth=1.0, label="VIX (implied)")
        ax1.plot(aligned.index, aligned["RV21"], color=SERIES_2,
                 linewidth=1.0, label="SPY 21d realized")
        ax1.set_title("Implied vs realized volatility (same units)")
        ax1.set_ylabel("Annualized volatility (%)")
        ax1.legend(loc="upper right")
        _despine(ax1)

        ax2.scatter(aligned["RV21"], aligned["VIX"], s=4, alpha=0.25,
                    color=SERIES_1, edgecolors="none")
        lim = max(aligned.max()) * 1.05
        ax2.plot([0, lim], [0, lim], color=BASELINE, linewidth=0.9)
        ax2.set_xlim(0, lim)
        ax2.set_ylim(0, lim)
        ax2.set_xlabel("SPY 21d realized vol (%)")
        ax2.set_ylabel("VIX (%)")
        ax2.set_title(f"Level correlation {corr:.2f}")
        _despine(ax2)

        fig.tight_layout()
        _footnote(fig, aligned.index, "45-degree line shown; points above it = implied premium.")
        fig.savefig(path)
        plt.close(fig)
    return path
