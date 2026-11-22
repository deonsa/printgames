"""Original, dependency-free, seeded generators for six printable puzzle types.

They return serializable puzzle dictionaries. All positions are zero-indexed.
No online gameplay code, external word lists, or AI dependencies are required.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import random
import re
from typing import Any

DIRECTIONS = ((0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1))
LEVEL_DIRS = {"easy": DIRECTIONS[:2], "medium": (DIRECTIONS[0], DIRECTIONS[1], (1, 1), (1, -1)), "hard": DIRECTIONS}


def _difficulty(value: str) -> None:
    if value not in LEVEL_DIRS:
        raise ValueError("difficulty must be easy, medium, or hard")


def _sanitize_word(value: str, alphabet: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ") -> str:
    word = "".join(c for c in str(value).upper() if c in alphabet)
    if len(word) < 2:
        raise ValueError(f"word/number {value!r} has fewer than 2 allowed characters")
    return word


def _occurrences(grid: list[list[str]], word: str) -> int:
    n = len(grid)
    count = 0
    # Treat reversed sightings as the same physical path for palindromes.
    seen = set()
    for r in range(n):
        for c in range(n):
            for dr, dc in DIRECTIONS:
                rr, cc = r + (len(word) - 1) * dr, c + (len(word) - 1) * dc
                if not (0 <= rr < n and 0 <= cc < n):
                    continue
                cells = tuple((r + j * dr, c + j * dc) for j in range(len(word)))
                if all(grid[x][y] == word[j] for j, (x, y) in enumerate(cells)):
                    seen.add(min(cells, cells[::-1]))
    return len(seen)


def make_search(words: list[str], *, size: int = 13, difficulty: str = "medium", seed: int = 0, numeric: bool = False) -> dict[str, Any]:
    """A deterministic letter/number search. The requested items occur once each.

    Rejects ambiguous target strings that are contained within other targets.
    On pathological word sets, fails explicitly rather than silently omitting words.
    """
    _difficulty(difficulty)
    if not 6 <= size <= 25:
        raise ValueError("size must be in 6..25")
    alpha = "0123456789" if numeric else "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    normalized = [_sanitize_word(w, alpha) for w in words]
    if len(normalized) < 2 or len(set(normalized)) != len(normalized):
        raise ValueError("provide at least 2 distinct valid search items")
    if any(len(w) > size for w in normalized):
        raise ValueError("an item is longer than grid size")
    if any(a in b or a[::-1] in b for a in normalized for b in normalized if a != b):
        raise ValueError("an item is a substring of another item, which creates ambiguous solutions")
    if sum(map(len, normalized)) > size * size * 0.9:
        raise ValueError("too many item characters for the grid; increase size")
    rng = random.Random(seed)
    for _attempt in range(160):
        grid = [["" for _ in range(size)] for _ in range(size)]
        positions: dict[str, dict[str, int]] = {}
        success = True
        for word in sorted(normalized, key=lambda w: (-len(w), w)):
            candidates = []
            for dr, dc in LEVEL_DIRS[difficulty]:
                for r in range(size):
                    for c in range(size):
                        if not (0 <= r + dr * (len(word) - 1) < size and 0 <= c + dc * (len(word) - 1) < size):
                            continue
                        overlaps = 0
                        valid = True
                        for i, letter in enumerate(word):
                            old = grid[r + i * dr][c + i * dc]
                            if old and old != letter:
                                valid = False
                                break
                            overlaps += bool(old)
                        if valid:
                            candidates.append((overlaps, r, c, dr, dc))
            if not candidates:
                success = False
                break
            # Vary layout while gently favoring useful crossing letters.
            rng.shuffle(candidates)
            candidates.sort(key=lambda p: p[0], reverse=True)
            choice = rng.choice(candidates[:min(30, len(candidates))])
            _, r, c, dr, dc = choice
            for i, letter in enumerate(word):
                grid[r + dr * i][c + dc * i] = letter
            positions[word] = {"row": r, "col": c, "dr": dr, "dc": dc}
        if not success:
            continue
        for r in range(size):
            for c in range(size):
                if not grid[r][c]:
                    grid[r][c] = rng.choice(alpha)
        if all(_occurrences(grid, word) == 1 for word in normalized):
            return {"type": "number_search" if numeric else "word_search", "title": "Number Search" if numeric else "Word Search", "difficulty": difficulty, "seed": seed, "grid": grid, "items": normalized, "placements": positions}
    raise ValueError("could not create an unambiguous search grid; change the seed, list or size")


def _cross_candidates(board: list[list[str]], word: str, rng: random.Random) -> list[tuple[int, int, int, int, int]]:
    """Crossword positions: score, r, c, dr, dc. A crossing is mandatory."""
    n = len(board)
    candidates = []
    # Across and down only.
    for dr, dc in ((0, 1), (1, 0)):
        for r in range(n):
            for c in range(n):
                er = r + dr * (len(word) - 1)
                ec = c + dc * (len(word) - 1)
                if not (0 <= er < n and 0 <= ec < n):
                    continue
                before = (r - dr, c - dc)
                after = (er + dr, ec + dc)
                if any(0 <= rr < n and 0 <= cc < n and board[rr][cc] for rr, cc in (before, after)):
                    continue
                crosses = 0
                ok = True
                for i, ch in enumerate(word):
                    rr, cc = r + i * dr, c + i * dc
                    old = board[rr][cc]
                    if old and old != ch:
                        ok = False
                        break
                    if old:
                        crosses += 1
                    else:
                        neighbors = ((rr - 1, cc), (rr + 1, cc)) if dr == 0 else ((rr, cc - 1), (rr, cc + 1))
                        if any(0 <= nr < n and 0 <= nc < n and board[nr][nc] for nr, nc in neighbors):
                            ok = False
                            break
                if ok and crosses:
                    mid = n // 2
                    center_dist = abs((r + er) / 2 - mid) + abs((c + ec) / 2 - mid)
                    candidates.append((crosses * 1000 - int(center_dist * 8), r, c, dr, dc))
    rng.shuffle(candidates)
    candidates.sort(reverse=True)
    return candidates


def make_crossword(entries: dict[str, str], *, size: int = 19, seed: int = 0, require_all: bool = True) -> dict[str, Any]:
    """Generate classroom crosswords with supplied (non-AI) clues.

    Fails transparently if words cannot all be included; never drops clues silently.
    """
    if not 9 <= size <= 29 or size % 2 == 0:
        raise ValueError("crossword grid size must be an odd number in 9..29")
    normalized: dict[str, str] = {}
    for raw, clue in entries.items():
        word = _sanitize_word(raw)
        if len(word) < 3 or len(word) > size:
            raise ValueError(f"{raw!r} must be 3..{size} letters")
        if word in normalized:
            raise ValueError(f"duplicate normalized crossword answer: {word}")
        if not str(clue).strip():
            raise ValueError(f"missing clue for {word}")
        normalized[word] = str(clue).strip()
    if not 3 <= len(normalized) <= 25:
        raise ValueError("provide 3..25 crossword entries")
    words = sorted(normalized, key=lambda w: (-len(w), w))
    best: tuple[list[list[str]], list[dict[str, Any]]] | None = None
    rng = random.Random(seed)
    for _ in range(130):
        board = [["" for _ in range(size)] for _ in range(size)]
        placed = []
        first = words[0] if _ < 20 else rng.choice(words[:min(4, len(words))])
        first_c = (size - len(first)) // 2
        first_r = size // 2
        for j, letter in enumerate(first):
            board[first_r][first_c + j] = letter
        placed.append({"word": first, "row": first_r, "col": first_c, "dr": 0, "dc": 1, "clue": normalized[first]})
        remaining = [w for w in words if w != first]
        # A crossable word may unlock another word: revisit after every placement.
        while remaining:
            scored = []
            for word in remaining:
                choices = _cross_candidates(board, word, rng)
                if choices:
                    score, r, c, dr, dc = choices[0]
                    scored.append((score, rng.random(), word, r, c, dr, dc))
            if not scored:
                break
            scored.sort(reverse=True)
            score, _, word, r, c, dr, dc = scored[rng.randrange(min(3, len(scored)))] if _ % 3 == 0 else scored[0]
            for j, letter in enumerate(word):
                board[r + j * dr][c + j * dc] = letter
            placed.append({"word": word, "row": r, "col": c, "dr": dr, "dc": dc, "clue": normalized[word]})
            remaining.remove(word)
        if best is None or len(placed) > len(best[1]):
            best = board, placed
        if len(placed) == len(words):
            break
    assert best is not None
    board, placed = best
    if require_all and len(placed) < len(words):
        missing = sorted(set(words) - {entry['word'] for entry in placed})
        raise ValueError(f"crossword cannot place all answers at size {size}; unplaced: {', '.join(missing)}")
    # Crop around used cells, with no misleading all-black outer padding.
    used = [(r, c) for r in range(size) for c in range(size) if board[r][c]]
    min_r, max_r = min(x for x, _ in used), max(x for x, _ in used)
    min_c, max_c = min(x for _, x in used), max(x for _, x in used)
    grid = [line[min_c:max_c + 1] for line in board[min_r:max_r + 1]]
    for p in placed:
        p['row'] -= min_r
        p['col'] -= min_c
    numbered = sorted({(p['row'], p['col']) for p in placed})
    labels = {pos: i for i, pos in enumerate(numbered, 1)}
    for p in placed:
        p['number'] = labels[(p['row'], p['col'])]
        p['direction'] = 'across' if p['dr'] == 0 else 'down'
    return {"type": "crossword", "title": "Vocabulary Crossword", "seed": seed, "grid": grid, "entries": sorted(placed, key=lambda p: (p['number'], p['direction'])), "omitted": sorted(set(words) - {p['word'] for p in placed})}


def make_kriss_kross(words: list[str], *, size: int = 19, seed: int = 0) -> dict[str, Any]:
    normalized = [_sanitize_word(w) for w in words]
    if len(set(normalized)) != len(normalized):
        raise ValueError("word list contains duplicate answers")
    model = make_crossword({w: f"{len(w)} letters" for w in normalized}, size=size, seed=seed)
    model['type'] = 'kriss_kross'
    model['title'] = 'Fill-in Crossword'
    model['word_bank'] = sorted(normalized, key=lambda w: (len(w), w))
    return model


def _shuffle_sudoku_solution(size: int, rng: random.Random) -> list[list[int]]:
    block_rows, block_cols = {4: (2, 2), 6: (2, 3), 9: (3, 3)}[size]
    # Standard Latin block pattern; preserve band/stack structure when permuting.
    base = [[(r * block_cols + r // block_rows + c) % size + 1 for c in range(size)] for r in range(size)]
    row_bands = list(range(size // block_rows))
    col_stacks = list(range(size // block_cols))
    rng.shuffle(row_bands)
    rng.shuffle(col_stacks)
    rows, cols = [], []
    for band in row_bands:
        values = list(range(band * block_rows, (band + 1) * block_rows))
        rng.shuffle(values)
        rows.extend(values)
    for stack in col_stacks:
        values = list(range(stack * block_cols, (stack + 1) * block_cols))
        rng.shuffle(values)
        cols.extend(values)
    digits = list(range(1, size + 1))
    rng.shuffle(digits)
    return [[digits[base[r][c] - 1] for c in cols] for r in rows]


def _sudoku_count(grid: list[list[int]], br: int, bc: int, limit: int = 2) -> int:
    n = len(grid)
    full = set(range(1, n + 1))
    count = 0

    def rec() -> None:
        nonlocal count
        if count >= limit:
            return
        best = None
        for r in range(n):
            for c in range(n):
                if grid[r][c]:
                    continue
                used = set(grid[r]) | {grid[rr][c] for rr in range(n)} | {grid[rr][cc] for rr in range((r // br) * br, (r // br + 1) * br) for cc in range((c // bc) * bc, (c // bc + 1) * bc)}
                options = full - used
                if not options:
                    return
                if best is None or len(options) < len(best[2]):
                    best = (r, c, options)
        if best is None:
            count += 1
            return
        r, c, opts = best
        for v in sorted(opts):
            grid[r][c] = v
            rec()
            grid[r][c] = 0
            if count >= limit:
                return
    rec()
    return count


def make_sudoku(*, size: int = 9, difficulty: str = 'medium', seed: int = 0) -> dict[str, Any]:
    _difficulty(difficulty)
    if size not in (4, 6, 9):
        raise ValueError("sudoku size must be 4, 6 or 9")
    br, bc = {4: (2, 2), 6: (2, 3), 9: (3, 3)}[size]
    rng = random.Random(seed)
    solution = _shuffle_sudoku_solution(size, rng)
    puzzle = [row[:] for row in solution]
    # Clue count is a rough difficulty control, not a formal rating.
    targets = {4: (9, 7, 6), 6: (21, 17, 14), 9: (41, 34, 29)}
    target = targets[size][('easy', 'medium', 'hard').index(difficulty)]
    cells = [(r, c) for r in range(size) for c in range(size)]
    rng.shuffle(cells)
    for r, c in cells:
        if sum(bool(x) for row in puzzle for x in row) <= target:
            break
        old = puzzle[r][c]
        puzzle[r][c] = 0
        if _sudoku_count(puzzle, br, bc) != 1:
            puzzle[r][c] = old
    return {"type": 'sudoku', 'title': f'{size}x{size} Sudoku', 'difficulty': difficulty, 'seed': seed, 'grid': puzzle, 'solution': solution, 'block_rows': br, 'block_cols': bc, 'clues': sum(bool(x) for row in puzzle for x in row)}


def _runs(cells: list[int]) -> tuple[int, ...]:
    runs = []
    current = 0
    for value in cells + [0]:
        if value:
            current += 1
        elif current:
            runs.append(current)
            current = 0
    return tuple(runs or [0])


def _nonogram_count(row_clues: list[tuple[int, ...]], col_clues: list[tuple[int, ...]], limit: int = 2) -> int:
    n = len(row_clues)
    possible_rows = [[tuple((mask >> col) & 1 for col in range(n)) for mask in range(1 << n) if _runs([(mask >> col) & 1 for col in range(n)]) == hint] for hint in row_clues]
    candidates = [tuple(tuple((mask >> row) & 1 for row in range(n)) for mask in range(1 << n) if _runs([(mask >> row) & 1 for row in range(n)]) == hint) for hint in col_clues]
    count = 0
    def rec(rows: list[tuple[int, ...]], possible_cols: list[list[tuple[int, ...]]]) -> None:
        nonlocal count
        if count >= limit:
            return
        r = len(rows)
        if r == n:
            count += 1
            return
        for candidate in possible_rows[r]:
            updated = [[opt for opt in possible_cols[c] if opt[r] == candidate[c]] for c in range(n)]
            if all(updated):
                rec(rows + [candidate], updated)
                if count >= limit:
                    return
    rec([], [list(x) for x in candidates])
    return count


def make_nonogram(*, size: int = 5, seed: int = 0) -> dict[str, Any]:
    if size not in (5, 7):
        raise ValueError('nonogram size must be 5 or 7')
    rng = random.Random(seed)
    # Small, recognizable silhouettes make better educational nonograms than
    # arbitrary noise. Every supplied silhouette is independently verified below.
    pictures = {
        5: {
            'heart': ('.#.#.', '#####', '#####', '.###.', '..#..'),
            'diamond': ('..#..', '.###.', '#####', '.###.', '..#..'),
            'tree': ('..#..', '.###.', '#####', '..#..', '..#..'),
            'fish': ('.###.', '#####', '#.###', '#####', '.###.'),
        },
        7: {
            'heart': ('.##.##.', '#######', '#######', '.#####.', '..###..', '...#...', '.......'),
            'house': ('...#...', '..###..', '.#####.', '#######', '#.....#', '#..#..#', '#######'),
            'rocket': ('...#...', '..###..', '..###..', '..###..', '.#####.', '.#.#.#.', '#..#..#'),
        },
    }
    name = rng.choice(sorted(pictures[size]))
    solution = [[int(c == '#') for c in row] for row in pictures[size][name]]
    rows = [_runs(row) for row in solution]
    cols = [_runs([solution[r][c] for r in range(size)]) for c in range(size)]
    if _nonogram_count(rows, cols) != 1:
        raise RuntimeError(f'internal nonogram template {name!r} is not uniquely solvable')
    return {"type": 'nonogram', 'title': f'{size}x{size} Nonogram', 'seed': seed, 'grid': [[0] * size for _ in range(size)], 'solution': solution, 'row_clues': [list(x) for x in rows], 'col_clues': [list(x) for x in cols], 'artwork_name': name}


GENERATORS = {
    'word_search': make_search,
    'number_search': lambda items, **kw: make_search(items, numeric=True, **kw),
    'crossword': make_crossword,
    'sudoku': make_sudoku,
    'nonogram': make_nonogram,
    'kriss_kross': make_kriss_kross,
}