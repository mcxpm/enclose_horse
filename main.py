import sys
from collections import deque
from pathlib import Path

import clingo

from scrape import INVALID_CELLS, SPECIAL_SCORES, LEGEND, fetch_level, parse_grid

ENCODING = Path(__file__).parent / "enclose.lp"


def grid_to_facts(grid, budget):
    """Describe the grid as clingo facts (see the top of enclose.lp)."""
    n, m = len(grid), len(grid[0])
    facts = [f"budget({budget})."]
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            facts.append(f"cell({r},{c}).")
            if r in (0, n - 1) or c in (0, m - 1):
                facts.append(f"boundary({r},{c}).")
            if is_valid_cell(ch):  # same rule validate_grid uses
                facts.append(f"walkable({r},{c}).")
            if ch == ".":
                facts.append(f"grass({r},{c}).")
            if ch == "H":
                facts.append(f"horse({r},{c}).")
            if ch in SPECIAL_SCORES:
                facts.append(f"bonus({r},{c},{SPECIAL_SCORES[ch]}).")
            if ch not in LEGEND:
                facts.append(f'portal({r},{c},"{ch}").')
    return "\n".join(facts)


def solver(grid, budget):
    """Return a copy of grid with the best walls placed as "W", or None if
    the horse can't be enclosed within the budget."""
    ctl = clingo.Control()
    ctl.load(str(ENCODING))
    ctl.add("base", [], grid_to_facts(grid, budget))
    ctl.ground([("base", [])])

    # clingo reports each better solution as it finds one; the last is optimal.
    best_walls = None

    def on_model(model):
        nonlocal best_walls
        best_walls = [
            (sym.arguments[0].number, sym.arguments[1].number)
            for sym in model.symbols(shown=True)
        ]

    ctl.solve(on_model=on_model)
    if best_walls is None:
        return None

    solved = [row[:] for row in grid]
    for r, c in best_walls:
        solved[r][c] = "W"
    return solved


def get_horse_position(grid):
    n, m = len(grid), len(grid[0])
    for i in range(n):
        for j in range(m):
            if grid[i][j] == "H":
                return (i, j)


def is_valid_cell(grid_value):
    return grid_value not in INVALID_CELLS


def get_portal_dest(grid, x, y):
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j] == grid[x][y] and ((i, j) != (x, y)):
                return (i, j)


def validate_grid(grid):
    horse_position = get_horse_position(grid)
    n, m = len(grid), len(grid[0])
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    q = deque([horse_position])
    score = 0
    seen = set()
    while q:
        x, y = q.popleft()
        if x == 0 or y == 0 or x == n - 1 or y == m - 1:
            return 0

        if (x, y) in seen:
            continue
        seen.add((x, y))

        grid_value = grid[x][y]

        score += 1 + SPECIAL_SCORES.get(grid_value, 0)

        if grid_value not in LEGEND:
            q.append(get_portal_dest(grid, x, y))

        for dx, dy in directions:
            x2, y2 = x + dx, y + dy
            if (
                0 <= x2 < n
                and 0 <= y2 < m
                and (x2, y2) not in seen
                and is_valid_cell(grid[x2][y2])
            ):
                q.append((x2, y2))
    return score


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else None  # date or level id, like scrape.py
    level = fetch_level(key)
    grid = parse_grid(level["map"])
    budget = level["budget"]
    solved_grid = solver(grid, budget)
    if solved_grid is None:
        print("No way to enclose the horse within the budget.")
        return False
    score = validate_grid(solved_grid)

    # Show placed walls as '#' so they stand out from pre-placed 'W's.
    for row, solved_row in zip(grid, solved_grid):
        print("".join("#" if a != b else a for a, b in zip(row, solved_row)))
    walls = sum(a != b for row, srow in zip(grid, solved_grid) for a, b in zip(row, srow))
    print(f"\n{level['name']}: score {score} using {walls}/{budget} walls "
          f"(optimal {level['optimalScore']})")

    return score == level["optimalScore"]


if __name__ == "__main__":
    main()
