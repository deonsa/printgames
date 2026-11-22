"""Native PrintGames rendering of six seeded, printable puzzle families.

The engine supplies deterministic logical puzzles; this module supplies the
same RenderedPage interface as every existing PrintGames activity.  No second
PDF pipeline or separate MCP instance is introduced.
"""
from __future__ import annotations

from html import escape
from typing import Any

from ..core.pages import PageSpec
from ..core.renderer import RenderedPage
from ..core.themes import ThemeSpec
from ..models import (WordSearchSpec, NumberSearchSpec, CrosswordSpec,
                      KrissKrossSpec, SudokuSpec, NonogramSpec)
from .printable_engines import (make_search, make_crossword, make_kriss_kross,
                                make_sudoku, make_nonogram)


def _level(difficulty: str | None) -> str:
    return {"easy": "easy", "medium": "medium", "hard": "hard",
            "expert": "hard", "all_ages": "easy", None: "medium"}[difficulty]


def _puzzle(spec: Any) -> dict[str, Any]:
    if isinstance(spec, WordSearchSpec):
        return make_search(spec.words, size=spec.grid_size,
                           difficulty=_level(spec.difficulty), seed=spec.seed)
    if isinstance(spec, NumberSearchSpec):
        return make_search(spec.numbers, size=spec.grid_size,
                           difficulty=_level(spec.difficulty), seed=spec.seed, numeric=True)
    if isinstance(spec, CrosswordSpec):
        return make_crossword({entry.answer: entry.clue for entry in spec.entries},
                              size=spec.grid_size, seed=spec.seed)
    if isinstance(spec, KrissKrossSpec):
        return make_kriss_kross(spec.words, size=spec.grid_size, seed=spec.seed)
    if isinstance(spec, SudokuSpec):
        return make_sudoku(size=spec.grid_size, difficulty=_level(spec.difficulty), seed=spec.seed)
    if isinstance(spec, NonogramSpec):
        return make_nonogram(size=spec.grid_size, seed=spec.seed)
    raise TypeError(f"Unsupported printable puzzle specification: {type(spec).__name__}")


def _grid_table(data: dict[str, Any], page: PageSpec, theme: ThemeSpec, answer: bool) -> str:
    kind = data["type"]
    grid = data["grid"]
    nr, nc = len(grid), len(grid[0])
    available_w = max(40, page.content_width_mm - 23)
    available_h = max(50, page.content_height_mm * (0.49 if kind in ("crossword", "kriss_kross") else 0.57))
    cell = min((16 if kind in ("sudoku", "nonogram") else 10.5) * page.scale,
               available_w / (nc + (2.8 if kind == "nonogram" else 0)),
               available_h / (nr + (1.9 if kind == "nonogram" else 0)))
    # The native page-frame provides all headers, instructions, footers, and safe margins.
    table_start = f'<table style="border-collapse:collapse;table-layout:fixed;margin:0 auto;border:1pt solid {theme.border_strong};">'
    rows: list[str] = []
    if kind in ("word_search", "number_search"):
        found: set[tuple[int, int]] = set()
        if answer:
            for word, p in data["placements"].items():
                found.update((p["row"] + i*p["dr"], p["col"] + i*p["dc"]) for i in range(len(word)))
        for r, line in enumerate(grid):
            entries = []
            for c, ch in enumerate(line):
                marked = (r, c) in found
                bg = theme.accent_soft if marked else theme.paper
                weight = "800" if marked else "600"
                # Underlining and a dark cell outline remain visible in
                # ink-saver mode, where accent_soft and paper are both white.
                border = f"1.15pt solid {theme.ink}" if marked else f"0.45pt solid {theme.border}"
                underline = ("text-decoration:underline;text-decoration-thickness:1.2pt;"
                             "text-underline-offset:1.0pt;") if marked else ""
                entries.append(f'<td style="width:{cell:.2f}mm;height:{cell:.2f}mm;border:{border};background:{bg};text-align:center;padding:0;font-size:{max(7.0,cell*1.15):.1f}pt;font-weight:{weight};font-family:{theme.font_mono};{underline}">{escape(ch)}</td>')
            rows.append('<tr>' + ''.join(entries) + '</tr>')
    elif kind in ("crossword", "kriss_kross"):
        starts = {(x["row"], x["col"]): x["number"] for x in data["entries"]}
        for r, line in enumerate(grid):
            entries = []
            for c, ch in enumerate(line):
                if not ch:
                    entries.append(f'<td style="height:{cell:.2f}mm;width:{cell:.2f}mm;background:{theme.ink};border:0.45pt solid {theme.border_strong};padding:0;"></td>')
                else:
                    label = f'<span style="position:absolute;top:0.3mm;left:0.6mm;font-size:{max(5.0,cell*0.6):.1f}pt;line-height:1;">{starts[(r,c)]}</span>' if (r, c) in starts else ''
                    letter = escape(ch) if answer else ''
                    entries.append(f'<td style="position:relative;height:{cell:.2f}mm;width:{cell:.2f}mm;border:0.6pt solid {theme.border_strong};padding:0;vertical-align:middle;text-align:center;font-size:{max(7.0,cell*1.1):.1f}pt;font-weight:700;">{label}{letter}</td>')
            rows.append('<tr>' + ''.join(entries) + '</tr>')
    elif kind == "sudoku":
        br, bc = data["block_rows"], data["block_cols"]
        values = data["solution"] if answer else grid
        for r, line in enumerate(values):
            entries = []
            for c, ch in enumerate(line):
                top = "1.2pt" if r % br == 0 else "0.35pt"
                left = "1.2pt" if c % bc == 0 else "0.35pt"
                bottom = "1.2pt" if r == nr-1 else "0.35pt"
                right = "1.2pt" if c == nc-1 else "0.35pt"
                bg = theme.accent_soft if answer and not grid[r][c] else theme.paper
                entries.append(f'<td style="width:{cell:.2f}mm;height:{cell:.2f}mm;text-align:center;padding:0;font-size:{max(10.0,cell*1.45):.1f}pt;background:{bg};border-style:solid;border-color:{theme.border_strong};border-width:{top} {right} {bottom} {left};">{ch or "&nbsp;"}</td>')
            rows.append('<tr>' + ''.join(entries) + '</tr>')
    elif kind == "nonogram":
        values = data["solution"] if answer else grid
        header_cells = ''.join(f'<td style="height:{cell*1.6:.2f}mm;min-width:{cell:.2f}mm;text-align:center;vertical-align:bottom;font-size:{max(6.3,cell*0.9):.1f}pt;line-height:1.1;padding:0 0 1mm;">{"<br>".join(map(str, clues))}</td>' for clues in data["col_clues"])
        rows.append(f'<tr><td style="min-width:{cell*2.8:.2f}mm;border:0;"></td>{header_cells}</tr>')
        for r in range(nr):
            entries = []
            for c in range(nc):
                shade = theme.ink if answer and values[r][c] else theme.paper
                entries.append(f'<td style="width:{cell:.2f}mm;height:{cell:.2f}mm;border:0.55pt solid {theme.border_strong};background:{shade};padding:0;"></td>')
            hint = ' '.join(map(str, data["row_clues"][r]))
            rows.append(f'<tr><td style="min-width:{cell*2.8:.2f}mm;text-align:right;padding-right:2mm;border:0;font-size:{max(6.3,cell*0.85):.1f}pt;">{escape(hint)}</td>{"".join(entries)}</tr>')
    return '<div style="display:flex;justify-content:center;align-items:center;margin:2.5mm 0 4mm;">' + table_start + ''.join(rows) + '</table></div>'


def _notes(data: dict[str, Any], theme: ThemeSpec, answer: bool, page: PageSpec) -> str:
    kind = data["type"]
    if kind in ("word_search", "number_search"):
        items = ''.join(f'<span style="min-width:27%;padding:1.2mm 1mm;font-size:{8.4*page.scale:.1f}pt;font-weight:600;">{escape(w)}</span>' for w in data["items"])
        return f'<div style="border-top:0.8pt solid {theme.border};padding-top:2mm;margin-top:1mm;"><b>Find these {"numbers" if kind == "number_search" else "words"}:</b><div style="display:flex;flex-wrap:wrap;column-gap:3mm;margin-top:2mm;">{items}</div></div>'
    if kind == "crossword":
        groups = []
        for direction in ("across", "down"):
            entries = [p for p in data["entries"] if p["direction"] == direction]
            if entries:
                lines = ''.join(f'<div style="margin-bottom:1.4mm;font-size:{7.4*page.scale:.1f}pt;line-height:1.24;"><b>{p["number"]}.</b> {escape(p["clue"])} <span style="color:{theme.ink_muted};">({len(p["word"])})</span></div>' for p in entries)
                groups.append(f'<section style="min-width:0;flex:1;"><b style="display:block;margin-bottom:1.5mm;border-bottom:0.5pt solid {theme.border_strong};">{direction.title()}</b>{lines}</section>')
        return f'<div style="display:flex;gap:5mm;margin-top:2mm;">{"".join(groups)}</div>'
    if kind == "kriss_kross":
        lengths: dict[int, list[str]] = {}
        for w in data["word_bank"]:
            lengths.setdefault(len(w), []).append(w)
        groups = ''.join(f'<div style="padding:1.1mm 0;">{n} letters: {escape(", ".join(words))}</div>' for n, words in sorted(lengths.items()))
        return f'<div style="margin-top:3mm;border-top:0.5pt solid {theme.border};"><b>Use every word once:</b>{groups}</div>'
    if kind == "sudoku":
        return f'<p style="margin:3mm 0;text-align:center;color:{theme.ink_muted};">Fill each row, column and outlined box using every number once.</p>' if not answer else ''
    if kind == "nonogram":
        name = data.get("artwork_name", "picture")
        return f'<p style="text-align:center;color:{theme.ink_muted};">{escape("Picture: " + name.title()) if answer else "Shade boxes to match the row and column clues. Separate runs require a blank."}</p>'
    return ''


def _render(spec: Any, page: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    puzzle = _puzzle(spec)
    kind = puzzle["type"]
    category = {"word_search": "Word Search", "number_search": "Number Search",
                "crossword": "Crossword", "kriss_kross": "Fill-in Crossword",
                "sudoku": "Sudoku", "nonogram": "Nonogram"}[kind]
    def body(answer: bool) -> str:
        return '<div style="width:100%;">' + _grid_table(puzzle, page, theme, answer) + _notes(puzzle, theme, answer, page) + '</div>'
    pages = [RenderedPage(title=spec.title, category=category,
                          instructions=spec.instructions, subtitle=spec.subtitle,
                          difficulty=spec.difficulty, body_html=body(False),
                          footer_left=spec.author_credit or f"Word & Logic Puzzles · {category}")]
    if spec.include_answer_key:
        pages.append(RenderedPage(title=f"{spec.title} — Solution", category=category,
                                  body_html=body(True), is_answer_key=True,
                                  footer_left=spec.author_credit or f"{category} Answer Key"))
    return pages


def render_word_search(spec: WordSearchSpec, page: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    return _render(spec, page, theme)


def render_number_search(spec: NumberSearchSpec, page: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    return _render(spec, page, theme)


def render_crossword(spec: CrosswordSpec, page: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    return _render(spec, page, theme)


def render_kriss_kross(spec: KrissKrossSpec, page: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    return _render(spec, page, theme)


def render_sudoku(spec: SudokuSpec, page: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    return _render(spec, page, theme)


def render_nonogram(spec: NonogramSpec, page: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    return _render(spec, page, theme)