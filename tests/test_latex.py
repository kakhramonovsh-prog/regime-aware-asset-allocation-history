"""Tests for LaTeX escaping and label resolution.

Both failures these guard against actually reached a build: an
unescaped percent silently commented out a macro line, and raw
snake_case identifiers produced "Missing $ inserted" and no PDF.
"""

from __future__ import annotations

import pytest

from src import latex


# ---------------------------------------------------------------------------
# Every special character
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("_", r"\_"),
        ("%", r"\%"),
        ("&", r"\&"),
        ("#", r"\#"),
        ("$", r"\$"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
        ("\\", r"\textbackslash{}"),
    ],
)
def test_each_special_character_is_escaped(raw, expected):
    assert latex.escape(raw) == expected


def test_all_special_characters_together():
    raw = r"_%&#${}~^\ "
    escaped = latex.escape(raw)
    # No bare special character may survive, ignoring the ones that are
    # part of an escape sequence.
    assert "ann_volatility" not in escaped
    for character in "_%&#$":
        assert f"\\{character}" in escaped
    assert r"\textasciitilde{}" in escaped
    assert r"\textasciicircum{}" in escaped
    assert r"\textbackslash{}" in escaped


def test_backslash_escaped_first_so_replacements_are_not_mangled():
    # If the backslash were escaped last, the backslashes introduced by
    # earlier replacements would be double-escaped.
    assert latex.escape("a_b") == r"a\_b"
    assert latex.escape("100%") == r"100\%"
    assert latex.escape(r"\_") == r"\textbackslash{}\_"


def test_regression_percent_in_a_unit_string():
    """The bug that would have commented out a macro line."""
    assert latex.escape("54.19 %") == r"54.19 \%"
    assert "\\%" in latex.escape("%")


def test_regression_underscore_in_a_column_name():
    """The bug that produced 'Missing $ inserted' and no PDF."""
    assert latex.escape("ann_volatility") == r"ann\_volatility"
    assert latex.escape("max_drawdown") == r"max\_drawdown"


def test_escape_accepts_non_strings():
    assert latex.escape(0.021) == "0.021"
    assert latex.escape(None) == "None"


def test_plain_text_is_unchanged():
    assert latex.escape("Regime-aware min-var") == "Regime-aware min-var"


# ---------------------------------------------------------------------------
# Label registry
# ---------------------------------------------------------------------------

def test_registered_identifiers_resolve():
    assert latex.label_for("regime_minvar") == "Regime-aware min-var"
    assert latex.label_for("sharpe") == "Sharpe"
    assert latex.label_for("cap_30pct") == r"30\% cap"


def test_unknown_identifier_raises_rather_than_falling_back():
    """A silent fallback to the raw identifier is how an unescaped
    underscore reaches the compiler."""
    with pytest.raises(latex.UnknownLabelError, match="no display label"):
        latex.label_for("some_new_metric")


def test_no_registered_label_contains_a_bare_special_character():
    """Every label must already be LaTeX-safe: bare specials would break
    the build exactly as the raw identifiers did."""
    for registry in latex._REGISTRIES:
        for key, label in registry.items():
            for character in "_&#":
                bare = [
                    i for i, ch in enumerate(label)
                    if ch == character and (i == 0 or label[i - 1] != "\\")
                ]
                assert not bare, f"{key}: bare '{character}' in {label!r}"
            # A percent must always be escaped; an unescaped one comments
            # out the rest of the line.
            for i, ch in enumerate(label):
                if ch == "%":
                    assert i > 0 and label[i - 1] == "\\", \
                        f"{key}: unescaped '%' in {label!r}"


def test_every_strategy_in_the_ladder_is_registered():
    from src import optimization as opt

    for strategy in opt.STRATEGIES:
        assert latex.is_registered(strategy), f"{strategy} has no display label"


def test_every_robustness_specification_is_registered():
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts.run_robustness import build_specifications

    for spec in build_specifications():
        assert latex.is_registered(spec.name), f"{spec.name} has no display label"
