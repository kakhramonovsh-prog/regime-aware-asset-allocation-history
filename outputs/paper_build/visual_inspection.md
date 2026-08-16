# Visual Inspection Audit

Inspection is a property of a **specific artifact**, not of the
manuscript in general. Any source change invalidates the inspected PDF:
a one-word edit can move a float and repaginate everything after it, so
the whole pass repeats against a newly built and newly hashed artifact.

## Round 1 — FAILED, corrections required

| Field | Value |
|---|---|
| PDF SHA-256 | `3b653741427bd63f84d345e09957bb7e07b840c230ee1ffcd60e94b1c85ef516` |
| Commit | `ca0a7f140b22ca1cc56847cbc5bfb85af9336cb6` |
| CI run | 31975553015 |
| Page count | 15 |
| Inspection date | 2026-08-16 |
| Automated gate | PASSED (bbl 6,637 bytes, 0 BibTeX errors, 0 unresolved markers, 0 overfull > 5pt) |
| Visual result | **7 defects found** |

### Page-by-page

| Page | Elements checked | Issue | Correction | Reverified |
|---|---|---|---|---|
| 1 | Title, author, abstract, keywords, JEL | None | — | pending round 2 |
| 2 | Introduction, macros, citations | **D1** hyphen used for negative numbers where a minus sign belongs | Serialize negatives as math minus | pending |
| 3 | Literature review, 14 citations | None | — | pending |
| 4 | Literature (methods), citations | None | — | pending |
| 5 | Data section, licensing paragraph | None | — | pending |
| 6 | Design, hypothesis equation (1), timeline | None | — | pending |
| 7 | Estimation, equation (3), Greek symbols | None | — | pending |
| 8 | Covariance, degeneracy policy | None | — | pending |
| 9 | Results, Table 2, inference prose | **D2** "which is -0.175 pp lower" is a double negative and states the opposite of what is meant; **D3** hyphens for negatives in Table 2 | Reword to "0.175 pp lower"; math minus in tables | pending |
| 10 | Figure 1, caption, axis labels | **D4** y-axis shows machine identifiers (`hmm_3_states`, `a2_accept_as_estimated`) instead of display labels; **D5** "primary (primary)" duplicated; **D6** figure alone on the page with large white space; **D7** axis says "Ledoit-Wolf" (hyphen) while the caption uses an en-dash | Use the label registry in the figure; drop the duplicate; tighten float placement; en-dash | pending |
| 11 | Robustness prose, sign instability | None | — | pending |
| 12 | Table 3 (13 rows), limitations | **D3** hyphens for negatives | Math minus | pending |
| 13 | Limitations, numerical reproduction | None | — | pending |
| 14 | Discussion, conclusion, cap-30 framing | None | — | pending |
| 15 | Bibliography | None observed; formatting consistent | — | pending |

### Defects in detail

**D1/D3 — hyphen where a minus sign belongs.** Negative numbers render
with a text hyphen (`-0.075`) rather than a typographic minus
(`−0.075`). The figure axis already uses a proper minus, so the document
is internally inconsistent. Affects every negative value in Tables 2, 3
and the macros.

**D2 — semantic error.** "annualized volatility, which is -0.175 pp
lower" says the volatility is *higher* by 0.175 pp, the opposite of the
finding. Either "0.175 pp lower" or "the difference is −0.175 pp" is
correct; the two must not be combined.

**D4 — machine identifiers in a figure.** The forest plot predates the
label registry and renders `drop_realized_vol`, `neff_kappa_30`,
`a3_total_covariance`. These are the same identifiers that broke the
LaTeX build; here they merely look unfinished, but the fix is the same
registry.

**D5 — duplicated text.** The primary row reads "primary  (primary)".

**D6 — float placement.** Figure 1 sits alone on page 10 with roughly
40% of the page blank above it.

**D7 — inconsistent dash.** Axis label "Ledoit-Wolf" versus caption
"Ledoit–Wolf".

### Verdict

Round 1 fails. The automated gate passed all seven of its criteria, and
the visual pass still found a semantic error that reverses the meaning
of a reported result. That is the argument for keeping the manual gate.

## Round 2 — pending

To be recorded after correction, rebuild in CI, and a fresh
page-by-page pass against the new hash.
