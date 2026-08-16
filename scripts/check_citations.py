"""Citation release gate.

Two separate requirements, because they fail differently:

1. **Bibliographic verification** --- authors, title, year, journal,
   volume, issue, pages and DOI match the publisher record.
2. **Claim verification** --- the cited paper actually supports the
   sentence it is attached to, with the supporting location recorded.

A citation can have perfect metadata and still be wrong about what it
claims, which is the more damaging error and the harder one to catch.
``paper/citation_audit.csv`` records both for every key.

    python scripts/check_citations.py [--release]

Without ``--release`` the script reports status and exits 0, so a draft
PDF can be built while verification is in progress. With ``--release``
it **fails** if any entry is pending, blocking the manuscript tag and
the public release.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAPER = PROJECT_ROOT / "paper"
AUDIT = PAPER / "citation_audit.csv"
BIB = PAPER / "references.bib"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", action="store_true",
                        help="fail if any citation is unverified")
    args = parser.parse_args()

    import pandas as pd

    audit = pd.read_csv(AUDIT)
    bib_text = BIB.read_text(encoding="utf-8")
    bib_keys = set(re.findall(r"@\w+\{([^,\s]+)\s*,", bib_text))
    audit_keys = set(audit["citation_key"])

    problems: list[str] = []

    missing_from_audit = bib_keys - audit_keys
    missing_from_bib = audit_keys - bib_keys
    if missing_from_audit:
        problems.append(f"in .bib but not audited: {sorted(missing_from_audit)}")
    if missing_from_bib:
        problems.append(f"audited but not in .bib: {sorted(missing_from_bib)}")

    verified = audit[audit["status"] == "verified"]
    pending = audit[audit["status"] != "verified"]

    print(f"Citations: {len(audit)} total, {len(verified)} verified, "
          f"{len(pending)} pending\n")

    if len(pending):
        print("PENDING (bibliographic and/or claim verification incomplete):")
        for _, row in pending.iterrows():
            print(f"  {row['citation_key']:16s} {row['supporting_location'][:78]}")

    # Every verified entry must actually carry the evidence of verification.
    for _, row in verified.iterrows():
        if str(row.get("metadata_verified")) != "yes":
            problems.append(f"{row['citation_key']}: marked verified but "
                            "metadata_verified is not 'yes'")
        if not str(row.get("supporting_location", "")).strip():
            problems.append(f"{row['citation_key']}: no supporting location "
                            "recorded for the cited claim")
        if str(row.get("supporting_location", "")).startswith("TO CHECK"):
            problems.append(f"{row['citation_key']}: marked verified but the "
                            "claim check is still outstanding")

    # The .bib itself must not advertise pending work at release time.
    pending_markers = bib_text.count("PENDING VERIFICATION")
    print(f"\n'PENDING VERIFICATION' markers in references.bib: {pending_markers}")

    if problems:
        print("\nAUDIT PROBLEMS:")
        for problem in problems:
            print(f"  - {problem}")

    if args.release:
        blocking = list(problems)
        if len(pending):
            blocking.append(f"{len(pending)} citation(s) not fully verified")
        if pending_markers:
            blocking.append(
                f"{pending_markers} 'PENDING VERIFICATION' marker(s) remain in "
                "references.bib"
            )
        if blocking:
            print("\nRELEASE BLOCKED:")
            for item in blocking:
                print(f"  - {item}")
            print("\nEvery citation needs both bibliographic verification and "
                  "claim verification before the manuscript tag.")
            sys.exit(1)
        print("\nRELEASE CHECK PASSED: all citations verified, both metadata "
              "and cited claim.")
        return

    if problems:
        sys.exit(1)
    print("\nDraft mode: pending citations are allowed. Run with --release "
          "before tagging the manuscript.")


if __name__ == "__main__":
    main()
