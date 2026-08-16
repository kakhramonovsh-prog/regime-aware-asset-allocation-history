"""Validate the LaTeX source without compiling it.

LaTeX is not installed on every machine, and a missing macro, input or
figure is worth catching before a build attempt. Checks that every macro
used is defined, every \\input and \\includegraphics target exists, and
every citation resolves to the bibliography.

    python scripts/check_paper.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAPER = PROJECT_ROOT / "paper"

SOURCES = ["main.tex", "_sections_intro.tex", "_sections_results.tex"]


def main() -> None:
    text = "".join((PAPER / name).read_text(encoding="utf-8") for name in SOURCES)
    problems: list[str] = []

    macros_file = PAPER / "macros.tex"
    defined = set(re.findall(r"newcommand\{\\(\w+)\}", macros_file.read_text(encoding="utf-8")))
    used = set(re.findall(r"\\(\w+)\{\}", text)) | set(
        re.findall(r"\\(primary\w+|vol\w+|hac\w+|regime\w+|comparator\w+)\b", text)
    )
    undefined = {m for m in used if m in
                 {n for n in used if n[0].islower()} and m not in defined
                 and re.match(r"(primary|vol|hac|regime|comparator)", m)}
    print(f"Macros defined: {len(defined)}")
    print(f"  {', '.join(sorted(defined))}")
    if undefined:
        problems.append(f"macros used but not defined: {sorted(undefined)}")
    else:
        print("  all macros used in the text are defined")

    print("\nInputs:")
    for target in re.findall(r"\\input\{([^}]+)\}", text):
        candidate = PAPER / target
        if not candidate.suffix:
            candidate = candidate.with_suffix(".tex")
        status = "OK" if candidate.exists() else "MISSING"
        print(f"  [{status}] {target}")
        if status == "MISSING":
            problems.append(f"missing input: {target}")

    print("\nFigures:")
    for target in re.findall(r"includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", text):
        candidate = PAPER / target
        status = "OK" if candidate.exists() else "MISSING"
        print(f"  [{status}] {target}")
        if status == "MISSING":
            problems.append(f"missing figure: {target}")

    print("\nCitations:")
    cited = set(re.findall(r"\\cite[tp]?\{([^}]+)\}", text))
    cited = {key.strip() for group in cited for key in group.split(",")}
    entries = set(re.findall(r"@\w+\{([^,]+),",
                             (PAPER / "references.bib").read_text(encoding="utf-8")))
    for key in sorted(cited):
        status = "OK" if key in entries else "MISSING"
        print(f"  [{status}] {key}")
        if status == "MISSING":
            problems.append(f"citation without bib entry: {key}")
    unused = entries - cited
    if unused:
        print(f"  note: in bibliography but not cited: {sorted(unused)}")

    words = len(re.findall(r"\b\w+\b", re.sub(r"\\[a-zA-Z]+|%.*", "", text)))
    print(f"\nApproximate word count: {words:,}")

    print()
    if problems:
        print("PROBLEMS:")
        for problem in problems:
            print(f"  - {problem}")
        sys.exit(1)
    print("LaTeX source validates: all macros, inputs, figures and citations resolve.")


if __name__ == "__main__":
    main()
