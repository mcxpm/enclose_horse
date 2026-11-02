"""Fetch an enclose.horse puzzle from the page HTML.

The site embeds the puzzle in every page as `window.__LEVEL__ = {...}`,
so a plain GET plus a JSON parse is enough.

Usage:
    python scrape.py                # today's daily
    python scrape.py 2026-11-01     # a past daily, by date
    python scrape.py pTs2WX         # any level by id (e.g. a bonus round)
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

BASE = "https://enclose.horse"
CACHE_DIR = Path(__file__).parent / "levels"

# Map characters, taken from the game's own parser in play.js.
# Digits 0-9 and letters a-z are portals: cells sharing a character are linked.
LEGEND = {
    ".": "grass",
    "~": "water",  # horse can't walk on it
    "H": "horse",
    "U": "unicorn",  # bonus modes only
    "C": "cherry",  # +3
    "G": "gem",  # +10
    "S": "skull",  # -5
    "W": "wall",  # pre-placed
    "K": "gate",  # lava gates bonus
    "P": "pad",  # lava gates bonus
}

INVALID_CELLS = {"~", "W", "K", "P"}

SPECIAL_SCORES = {"C": 3, "G": 10, "S": -5}


def fetch_html(key=None):
    url = f"{BASE}/" if key is None else f"{BASE}/play/{key}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def extract_js_var(html, name):
    """Parse the JSON literal assigned to window.<name> in the page."""
    m = re.search(rf"window\.{re.escape(name)}\s*=\s*", html)
    if not m:
        return None
    obj, _ = json.JSONDecoder().raw_decode(html, m.end())
    return obj


def parse_grid(map_str):
    rows = map_str.strip().split("\n")
    width = len(rows[0])
    # The game pads short rows with grass, so do the same.
    return [list(row.ljust(width, ".")[:width]) for row in rows]


def fetch_level(key=None):
    html = fetch_html(key)
    level = extract_js_var(html, "__LEVEL__")
    if level is None:
        raise RuntimeError(
            "window.__LEVEL__ not found; the page layout may have changed"
        )
    # Only the daily page has the list of recent dailies (with bonus ids).
    level["_daily_levels"] = extract_js_var(html, "__DAILY_LEVELS__")
    return level


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else None
    level = fetch_level(key)
    grid = parse_grid(level["map"])

    print(f"{level['name']}  (id {level['id']}, date {level.get('dailyDate')})")
    print(
        f"{len(grid)} rows x {len(grid[0])} cols | wall budget {level['budget']} "
        f"| optimal score {level.get('optimalScore')} | bonus {level.get('bonusType')}"
    )
    print()
    print("\n".join("".join(row) for row in grid))

    CACHE_DIR.mkdir(exist_ok=True)
    out = CACHE_DIR / f"{level['id']}.json"
    out.write_text(json.dumps(level, indent=2))
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
