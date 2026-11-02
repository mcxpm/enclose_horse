"""Put the solver's walls onto the real enclose.horse board.

Prints a JavaScript snippet and copies it to the clipboard. Paste it into the
browser console on enclose.horse and the page reloads with the walls placed.
Nothing is submitted: you look at the board and press Submit yourself.

Usage:
    uv run python show_on_site.py               # today's daily
    uv run python show_on_site.py 2026-11-01    # a past daily (date or level id)

How it works: the game saves your in-progress board in localStorage under
"enclose_progress" as {levelId: {walls: [cell indices], savedAt: ...}} and
restores it when the page loads. The snippet writes the solution there and
reloads. The game ignores it for puzzles you've already submitted.
"""

import json
import shutil
import subprocess
import sys

from main import solver, validate_grid
from scrape import fetch_level, parse_grid


def wall_indices(grid, solved):
    """Cells where the solver placed a wall, as the game's flat index (row * cols + col)."""
    cols = len(grid[0])
    return [
        r * cols + c
        for r, (row, solved_row) in enumerate(zip(grid, solved))
        for c, (before, after) in enumerate(zip(row, solved_row))
        if before != after
    ]


def make_snippet(level_id, walls):
    return f"""(() => {{
  const id = {json.dumps(level_id)}, walls = {json.dumps(walls)};
  if (JSON.parse(localStorage.getItem("enclose_submissions") || "{{}}")[id]) {{
    console.warn("You've already submitted this puzzle, so the game will show your submitted walls instead.");
    return;
  }}
  const saved = JSON.parse(localStorage.getItem("enclose_progress") || "{{}}");
  saved[id] = {{ ...saved[id], walls, savedAt: Date.now() }};
  localStorage.setItem("enclose_progress", JSON.stringify(saved));
  if (window.__LEVEL__?.id === id) location.reload();
  else location.href = "/play/" + id;
}})();"""


def copy_to_clipboard(text):
    for cmd in (["wl-copy"], ["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]):
        if shutil.which(cmd[0]):
            try:
                subprocess.run(cmd, input=text.encode(), check=True, timeout=5)
                return True
            except (subprocess.SubprocessError, OSError):
                pass
    return False


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else None
    level = fetch_level(key)
    grid = parse_grid(level["map"])
    solved = solver(grid, level["budget"])
    if solved is None:
        print("No way to enclose the horse within the budget.")
        return

    walls = wall_indices(grid, solved)
    print(f"{level['name']}: score {validate_grid(solved)} with {len(walls)} walls "
          f"(optimal {level['optimalScore']})\n")
    snippet = make_snippet(level["id"], walls)
    print(snippet + "\n")
    if copy_to_clipboard(snippet):
        print("Copied to clipboard.")
    print("On enclose.horse: F12 -> Console, paste, press Enter.")
    print('(The first time, the browser may ask you to type "allow pasting" first.)')


if __name__ == "__main__":
    main()
