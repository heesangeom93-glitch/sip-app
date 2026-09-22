#!/usr/bin/env python3
"""Generate sip-word-list.csv from the Sip app's words.json.

Usage:
    scripts/build-word-list.py [WORDS_JSON] [OUT_CSV]

Defaults:
    WORDS_JSON  ~/dev/sip/data/words.json
    OUT_CSV     <repo root>/sip-word-list.csv   (repo root = parent of scripts/)

The output is UTF-8 with a BOM so Korean text opens correctly in Excel and
Numbers. The first line is a "#" comment carrying attribution and license,
followed by the CSV header row and one row per word, sorted by
(level, day, id). Standard library only.
"""

import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SIP_APP_DIR = Path.home() / "dev" / "sip"          # read-only reference; never written to
DEFAULT_WORDS_JSON = SIP_APP_DIR / "data" / "words.json"
DEFAULT_OUT_CSV = REPO_ROOT / "sip-word-list.csv"

COLUMNS = ["level", "day", "word", "pos", "korean", "example1", "example2", "source_list"]

ATTRIBUTION = (
    "# Sip word list — adapted from the New General Service List (NGSL) and "
    "New Academic Word List (NAWL) by Browne, C., Culligan, B., & Phillips, J. "
    "— CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/) "
    "— https://www.newgeneralservicelist.com "
    "— Sip's adaptation (level order, Korean meanings, examples) is shared "
    "under the same license."
)


def is_within(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def load_words(words_json: Path) -> list:
    with words_json.open(encoding="utf-8") as f:
        data = json.load(f)
    words = data["words"] if isinstance(data, dict) else data
    if not isinstance(words, list):
        raise SystemExit(f"error: unexpected JSON shape in {words_json}")
    return words


def to_row(w: dict) -> list:
    examples = list(w.get("examples") or [])
    examples += [""] * (2 - len(examples))
    return [
        w["level"],
        w["day"],
        w["word"],
        w.get("pos", ""),
        (w.get("meanings") or {}).get("ko", ""),
        examples[0],
        examples[1],
        w.get("list", ""),
    ]


def main(argv: list) -> int:
    words_json = Path(argv[1]).expanduser() if len(argv) > 1 else DEFAULT_WORDS_JSON
    out_csv = Path(argv[2]).expanduser() if len(argv) > 2 else DEFAULT_OUT_CSV

    if len(argv) > 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not words_json.is_file():
        print(f"error: words file not found: {words_json}", file=sys.stderr)
        return 1
    if is_within(out_csv, SIP_APP_DIR) or out_csv.resolve() == words_json.resolve():
        print(f"error: refusing to write inside the Sip app directory: {out_csv}", file=sys.stderr)
        return 1

    words = load_words(words_json)
    words.sort(key=lambda w: (w["level"], w["day"], w["id"]))

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig writes the BOM exactly once, before the comment line.
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        f.write(ATTRIBUTION + "\n")
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writerow(COLUMNS)
        for w in words:
            writer.writerow(to_row(w))

    print(f"Wrote {len(words)} rows to {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
