"""LaTeX escaping and label resolution for generated tables.

Two failures reached the build because generated text went into LaTeX
unescaped: an unescaped ``%`` silently commented out the rest of a macro
line, and raw ``snake_case`` identifiers produced "Missing $ inserted"
and no PDF at all. Both were the same root cause, so both are fixed in
one place.

Every string bound for LaTeX passes through :func:`escape`. Every
machine identifier passes through :func:`label_for`, which **raises on
an unknown key** rather than falling back to the raw identifier --- a
silent fallback is how an unescaped underscore reaches the compiler.
"""

from __future__ import annotations

# Replacements are applied through sentinels in a single pass. A naive
# sequential replace is wrong in both directions: escaping the backslash
# first inserts braces that the later brace rules then re-escape, while
# escaping it last mangles the backslashes the earlier rules introduced.
_ESCAPES: dict[str, str] = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escape(text: object) -> str:
    """Escape every LaTeX special character in ``text``.

    Covers the full set: backslash, ampersand, percent, dollar, hash,
    underscore, braces, tilde and caret. Each input character is mapped
    exactly once, so a replacement can never be escaped again.
    """
    return "".join(_ESCAPES.get(character, character) for character in str(text))


class UnknownLabelError(KeyError):
    """Raised when an identifier has no registered display label."""


STRATEGY_LABELS: dict[str, str] = {
    "equal_weight": "Equal weight",
    "static_6040": "60/40",
    "static_minvar": "Static min-var",
    "rolling_lw_minvar": "Rolling LW min-var",
    "ewma_scaled_minvar": "EWMA-scaled min-var",
    "regime_minvar": "Regime-aware min-var",
    "regime_minvar minus rolling_lw_minvar": "Regime-aware $-$ rolling LW",
    "headline": "Headline",
}

METRIC_LABELS: dict[str, str] = {
    "cagr": r"CAGR (\%)",
    "ann_volatility": r"Volatility (\%)",
    "sharpe": "Sharpe",
    "sortino": "Sortino",
    "max_drawdown": r"Max DD (\%)",
    "calmar": "Calmar",
    "sharpe_difference": r"$\Delta$ Sharpe",
    "vol_difference": r"$\Delta$ Vol (pp)",
    "cagr_difference": r"$\Delta$ CAGR (pp)",
    "maxdd_difference": r"$\Delta$ Max DD (pp)",
    "ci95_lower": "CI lower",
    "ci95_upper": "CI upper",
    "p_value": "$p$",
    "mean_return_difference_annualized": "Mean return diff (bps)",
    "cost_expenditure_annualized": "Cost (bps p.a.)",
    "half_turnover": r"Half-turnover (\%)",
    "full_traded_notional": r"Traded notional (\%)",
    "terminal_wealth": "Terminal wealth",
    "n_observations": "$N$",
    "difference": "Difference",
}

SPEC_LABELS: dict[str, str] = {
    "primary": "Primary",
    "hmm_3_states": "Three states",
    "drop_vix": "Drop VIX",
    "drop_realized_vol": "Drop realized vol",
    "rolling_5y_window": "Rolling 5y window",
    "cap_30pct": r"30\% cap",
    "cap_50pct": r"50\% cap",
    "neff_kappa_30": r"$\kappa = 30$",
    "neff_kappa_120": r"$\kappa = 120$",
    "core_universe": "Core universe",
    "alt_seeds_100": "Alternative seeds",
    "a2_accept_as_estimated": "Accept degenerate fits",
    "a3_total_covariance": "Total covariance mixture",
}

_REGISTRIES = (STRATEGY_LABELS, METRIC_LABELS, SPEC_LABELS)


def label_for(identifier: str) -> str:
    """Display label for a machine identifier.

    Raises :class:`UnknownLabelError` when the identifier is not
    registered. Falling back to the raw string would reintroduce the
    unescaped-underscore failure, so an unregistered identifier is
    treated as a bug rather than papered over.
    """
    for registry in _REGISTRIES:
        if identifier in registry:
            return registry[identifier]
    raise UnknownLabelError(
        f"no display label registered for {identifier!r}. Add it to "
        "src/latex.py rather than letting a raw identifier reach LaTeX."
    )


def is_registered(identifier: str) -> bool:
    return any(identifier in registry for registry in _REGISTRIES)
