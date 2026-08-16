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

---

## Round 2 — FAILED, corrections required

Round 1's seven defects are all confirmed fixed (see the "Round 1
resolution" column below). Round 2 inspects a newly built artifact and
records an explicit disposition for **every one of the 15 pages**, not
only the pages that were previously defective.

| Field | Value |
|---|---|
| PDF SHA-256 | `7019d029da61acebab724c290ca7a1297500fe174afab7746f80cab5e3c5be0a` |
| Commit | `6a77bef027eab081fc1308c997abf7fcc32af8af` |
| CI run | 31978675959 |
| Page count | 15 |
| Inspection date | 2026-08-16 |
| Automated gate | PASSED (latexmk clean, non-empty bbl, 0 unresolved markers, 0 overfull > 5pt) |
| Number census | PASSED (48 literals classified; 0 empirical results typed) |
| Visual result | **7 defects found, all typographic; no numerical error** |

### Page-by-page disposition (all 15)

| Page | Elements checked | Disposition | Round 1 resolution |
|---|---|---|---|
| 1 | Title, author, date, abstract, keywords, JEL, footnote, intro opening | **PASS** — minus signs typographic throughout (−0.075); abstract states magnitude correctly ("lowered ... by 0.175 pp") | — |
| 2 | Introduction, 6 macro citations, preregistration paragraph | **PASS** with note — D1 (hyphen-as-minus) is fixed; wording "an interval 9.0 times its width" is loose but not an error | D1 fixed |
| 3 | Literature, 14 author-year citations, Section 8 cross-reference | **PASS** — every citation resolves, no `[?]`, cross-reference resolves to "Section 8" | — |
| 4 | Literature (methods), 10 citations, data section, alignment paragraph | **PASS** — equity correlations render from macros (0.82, 0.92) | — |
| 5 | Licensing, preregistered design, equation (1), sample split, timeline | **PASS** — equation (1) typesets correctly | — |
| 6 | Strategy ladder, costs, equation (2), volatility, regimes | **FAIL** — **D8** "volatility- scaled" stray space after hyphen; **D9** "the fifteen pairwise comparisons 1 survives" mixes a word and a digit in one clause | — |
| 7 | Covariance construction, equation (3), conditioning diagnostics | **FAIL** — **D10** "0.16 %" renders a thin space before the percent sign while "1%" on the same line does not | — |
| 8 | Results, Table 1 (6 rows), equation (4), bootstrap paragraph | **PASS** — equation (4) is the exact line that aborted the previous build; it now typesets. Table 1 minus signs correct | — |
| 9 | Block length, returns/volatility, trading costs, Table 2 | **FAIL** — **D10** "54.19 %", "16.94 %"; **D11** "lower by 0.175 pp, a difference of −0.175 pp" states magnitude and signed value back to back; **D9** "11 of thirteen ... 12 of thirteen"; "Of the 5 secondary metric intervals" | — |
| 10 | Figure 1, 13 rows, axis labels, caption, footnote | **PASS** — D4/D5/D7 all fixed: display labels ("Three states", "κ = 30"), no duplicate, en-dash in the axis label. D6 (float alone on page) persists but is acceptable for a full-width figure | D4, D5, D7 fixed; D6 accepted |
| 11 | Sign instability, weight cap, minor factors, subperiods, limitations | **FAIL** — **D12** paragraph opens "2 preregistered variations", a sentence beginning with a digit; **D10** "45.4 %", "26.6 %", "73.4 %" beside "30%" and "40%" | — |
| 12 | Table 3 (13 rows), limitations, numerical reproduction | **PASS** — drop-realized-vol reads −0.023, matching the corrected prose; 1.45 × 10⁻¹¹ typesets via `\ensuremath` | D3 fixed |
| 13 | Researcher discretion, discussion, conclusion, cap-30 framing | **FAIL** — **D10** "73.4 %" directly beneath "40% to 30%" | — |
| 14 | Bibliography, entries Ang–Engle (9 entries) | **FAIL** — **D13** BibTeX lowercased protected words: "the em algorithm" (Dempster), "united kingdom inflation" (Engle), "1/n portfolio strategy" (DeMiguel) | — |
| 15 | Bibliography, entries Guidolin–Politis (13 entries), page fill | **FAIL** — **D13** "with the sharpe ratio" (Ledoit–Wolf 2008), "The markowitz optimization enigma" (Michaud). Page is ~90% full, satisfying the half-full rule | — |

### Defects in detail

**D8 — "volatility- scaled" (page 6).** A hyphen at the end of a source
line followed by a newline renders as "volatility- scaled". Cosmetic but
conspicuous in a compound the paper uses repeatedly.

**D9 — mixed word and digit counts in one clause (pages 6, 9).** Moving
counts into macros forced digits into sentences whose other numbers are
spelled out: "across the fifteen pairwise comparisons 1 survives", "11
of thirteen point estimates are positive and 12 of thirteen intervals
contain zero", "Of the 5 secondary metric intervals". The counts are
correct; the register is inconsistent. The fix is to phrase the sentence
so a digit reads naturally, not to revert to hand-typed words.

**D10 — thin space before the percent sign (pages 6, 7, 9, 11, 13).**
Generated percentages render as "54.19 %" because the macro writer
appends `\,` before every unit. That is right for "bps" and wrong for
"%", and the inconsistency is visible on the same line as hard-coded
values: page 13 reads "40% to 30% ... 73.4 % of that change".

**D11 — magnitude and signed value stated consecutively (page 9).**
"the regime-aware strategy's is lower by 0.175 pp, a difference of
−0.175 pp with a 95% interval ..." Both macros are correct; using both
in one sentence is redundant. Splitting signed from magnitude fixed a
semantic reversal in Round 1, and this is the cost of that split showing
up at the point of use.

**D12 — sentence begins with a digit (page 11).** "**Sign instability.**
2 preregistered variations reverse the sign ..." A sentence may not open
with a numeral. Same cause as D9.

**D13 — BibTeX case-folding (pages 14, 15).** `plainnat` lowercases
title words that are not brace-protected, so acronyms and proper nouns
were silently downcased: "em algorithm", "united kingdom", "1/n",
"sharpe ratio", "markowitz optimization". These are wrong as
bibliographic records, not merely ugly, and they are exactly the class
of error a build gate cannot see: BibTeX succeeded.

### Observation (not a defect)

`paper/tables/table3_secondary_intervals.tex` is generated but never
`\input` into the manuscript; the five secondary intervals appear in
prose only. Worth a decision before release: either include the table or
stop generating it.

### What Round 2 establishes

No numerical defect was found. Every value on every page traces to a
macro in `paper/result_inventory.csv`, the two corrections the census
surfaced (drop-realized-vol −0.023, between-state 0.16%) render as
corrected, and equation (4) — the line that aborted the previous build —
typesets. All seven defects are typographic or bibliographic.

Five of the seven (D9, D10, D11, D12 and part of D8) were introduced by
this round's own change: moving hand-typed results into macros. That is
the expected cost of the change and the reason the pass repeats rather
than being assumed.
