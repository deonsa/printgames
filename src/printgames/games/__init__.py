"""Unified game dispatcher and multi-game booklet compiler."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

from ..core.pages import PageSpec, resolve_page_spec
from ..core.renderer import (
    ExportResult,
    RenderedPage,
    build_cover_page_html,
    build_toc_page_html,
    export_document,
    paginate_toc,
)
from ..core.themes import ThemeSpec, get_theme
from ..models import (
    AcrosticSpec,
    AnagramScrambleSpec,
    AnyGameSpec,
    BattleshipSpec,
    BoggleWordWheelSpec,
    BookletSpec,
    CategoriesSpec,
    ColorByNumberSpec,
    CryptogramSpec,
    WordSearchSpec,
    NumberSearchSpec,
    CrosswordSpec,
    KrissKrossSpec,
    SudokuSpec,
    NonogramSpec,
    DotToDotSpec,
    DotsAndBoxesSpec,
    HangmanSpec,
    HiddenPicturesSpec,
    MadLibsSpec,
    MazeSpec,
    RebusSpec,
    SpotTheDifferenceSpec,
    WordLadderSpec,
)
from .printable_puzzles import (
    render_word_search,
    render_number_search,
    render_crossword,
    render_kriss_kross,
    render_sudoku,
    render_nonogram,
)
from .multiplayer_games import (
    render_battleship,
    render_categories,
    render_dots_and_boxes,
    render_hangman,
    render_mad_libs,
)
from .visual_puzzles import (
    render_color_by_number,
    render_dot_to_dot,
    render_hidden_pictures,
    render_maze,
    render_spot_the_difference,
)
from .word_puzzles import (
    render_acrostic,
    render_anagram_scramble,
    render_boggle_word_wheel,
    render_cryptogram,
    render_rebus,
    render_word_ladder,
)

GAME_REGISTRY: dict[str, tuple[type[AnyGameSpec], Callable[[Any, PageSpec, ThemeSpec], list[RenderedPage]], str]] = {
    # Word & Letter Puzzles
    "word_search": (WordSearchSpec, render_word_search, "Word & Letter Puzzles"),
    "number_search": (NumberSearchSpec, render_number_search, "Word & Letter Puzzles"),
    "crossword": (CrosswordSpec, render_crossword, "Word & Letter Puzzles"),
    "kriss_kross": (KrissKrossSpec, render_kriss_kross, "Word & Letter Puzzles"),
    "sudoku": (SudokuSpec, render_sudoku, "Logic Puzzles"),
    "nonogram": (NonogramSpec, render_nonogram, "Logic Puzzles"),
    "cryptogram": (CryptogramSpec, render_cryptogram, "Word & Letter Puzzles"),
    "word_ladder": (WordLadderSpec, render_word_ladder, "Word & Letter Puzzles"),
    "anagram_scramble": (AnagramScrambleSpec, render_anagram_scramble, "Word & Letter Puzzles"),
    "acrostic": (AcrosticSpec, render_acrostic, "Word & Letter Puzzles"),
    "boggle_word_wheel": (BoggleWordWheelSpec, render_boggle_word_wheel, "Word & Letter Puzzles"),
    "rebus": (RebusSpec, render_rebus, "Word & Letter Puzzles"),
    # Visual & Spatial Activities
    "maze": (MazeSpec, render_maze, "Visual & Spatial Activities"),
    "spot_the_difference": (SpotTheDifferenceSpec, render_spot_the_difference, "Visual & Spatial Activities"),
    "hidden_pictures": (HiddenPicturesSpec, render_hidden_pictures, "Visual & Spatial Activities"),
    "dot_to_dot": (DotToDotSpec, render_dot_to_dot, "Visual & Spatial Activities"),
    "color_by_number": (ColorByNumberSpec, render_color_by_number, "Visual & Spatial Activities"),
    # Multi-Player Pen & Paper Games
    "dots_and_boxes": (DotsAndBoxesSpec, render_dots_and_boxes, "Multi-Player Pen & Paper Games"),
    "battleship": (BattleshipSpec, render_battleship, "Multi-Player Pen & Paper Games"),
    "categories": (CategoriesSpec, render_categories, "Multi-Player Pen & Paper Games"),
    "hangman": (HangmanSpec, render_hangman, "Multi-Player Pen & Paper Games"),
    "mad_libs": (MadLibsSpec, render_mad_libs, "Multi-Player Pen & Paper Games"),
}


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return slug[:60] or "printgame"


def render_game_pages(spec: AnyGameSpec, page_spec: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    entry = GAME_REGISTRY.get(spec.game_type)
    if entry is None:
        raise ValueError(f"Unknown game_type '{spec.game_type}'.")
    _, render_fn, _ = entry
    return render_fn(spec, page_spec, theme)


def produce_game(spec: AnyGameSpec) -> ExportResult:
    """Validate, render, and export a single print game specification."""
    page_spec = resolve_page_spec(
        page_size=spec.page_size,
        orientation=spec.orientation,
        margin_mm=spec.margin_mm,
        custom_width_mm=spec.custom_width_mm,
        custom_height_mm=spec.custom_height_mm,
    )
    theme = get_theme(spec.theme, ink_saver=spec.ink_saver)
    pages = render_game_pages(spec, page_spec, theme)

    out_path = spec.output_path or str(Path("output") / f"{spec.game_type}_{_slugify(spec.title)}.pdf")
    return export_document(
        pages=pages,
        page_spec=page_spec,
        theme=theme,
        doc_title=spec.title,
        output_path=out_path,
        output_format=spec.output_format,
        render_preview_png=spec.render_preview_png,
    )


def produce_game_from_dict(data: dict[str, Any]) -> ExportResult:
    game_type = data.get("game_type")
    if not game_type or game_type not in GAME_REGISTRY:
        valid = ", ".join(GAME_REGISTRY.keys())
        raise ValueError(f"Missing or invalid game_type '{game_type}'. Valid types: {valid}")
    model_cls, _, _ = GAME_REGISTRY[game_type]
    spec = model_cls.model_validate(data)
    return produce_game(spec)


def produce_booklet(spec: BookletSpec) -> ExportResult:
    """Compile multiple games into a single print-ready booklet with optional cover, TOC, and collated answer keys."""
    page_spec = resolve_page_spec(
        page_size=spec.page_size,
        orientation=spec.orientation,
        margin_mm=spec.margin_mm,
        custom_width_mm=spec.custom_width_mm,
        custom_height_mm=spec.custom_height_mm,
    )
    theme = get_theme(spec.theme, ink_saver=spec.ink_saver)

    puzzle_pages: list[RenderedPage] = []
    answer_pages: list[RenderedPage] = []
    toc_entries: list[tuple[str, str, int]] = []

    for idx, raw_game in enumerate(spec.games, start=1):
        gtype = raw_game.get("game_type")
        if gtype not in GAME_REGISTRY:
            valid = ", ".join(GAME_REGISTRY.keys())
            raise ValueError(f"Booklet game #{idx} has invalid game_type '{gtype}'. Valid: {valid}")
        model_cls, render_fn, _ = GAME_REGISTRY[gtype]
        # Inherit booklet page & theme defaults unless explicitly overridden
        merged = {
            "page_size": spec.page_size,
            "orientation": spec.orientation,
            "margin_mm": spec.margin_mm,
            "custom_width_mm": spec.custom_width_mm,
            "custom_height_mm": spec.custom_height_mm,
            "theme": spec.theme,
            "ink_saver": spec.ink_saver,
            **raw_game,
        }
        game_spec = model_cls.model_validate(merged)
        rendered = render_fn(game_spec, page_spec, theme)

        start_page_num = len(puzzle_pages) + 1
        first_puzzle = next((p for p in rendered if not p.is_answer_key), rendered[0])
        toc_entries.append((game_spec.title, first_puzzle.category, start_page_num))

        if spec.collate_answer_keys_at_end:
            for p in rendered:
                if p.is_answer_key:
                    answer_pages.append(p)
                else:
                    puzzle_pages.append(p)
        else:
            puzzle_pages.extend(rendered)

    final_pages: list[RenderedPage] = []
    if spec.include_cover:
        cover_html = build_cover_page_html(
            title=spec.booklet_title,
            subtitle=spec.subtitle,
            author=spec.author,
            game_count=len(spec.games),
            theme=theme,
            page=page_spec,
        )
        final_pages.append(
            RenderedPage(
                title=spec.booklet_title,
                category="Cover",
                body_html="",
                custom_page_html=cover_html,
            )
        )

    if spec.include_toc:
        chunks = paginate_toc(toc_entries, page_spec, bool(answer_pages))
        front_matter_count = len(final_pages) + len(chunks)
        first_index = 1
        for index, chunk in enumerate(chunks):
            entries = [(title, category, n + front_matter_count) for title, category, n in chunk]
            answer_start = None
            if answer_pages and index == len(chunks) - 1:
                answer_start = front_matter_count + len(puzzle_pages) + 1
            final_pages.append(RenderedPage(
                title="Table of Contents",
                category="Contents",
                body_html="",
                custom_page_html=build_toc_page_html(entries, answer_start, theme, page_spec, first_index),
            ))
            first_index += len(chunk)

    final_pages.extend(puzzle_pages)
    final_pages.extend(answer_pages)

    out_path = spec.output_path or str(Path("output") / f"booklet_{_slugify(spec.booklet_title)}.pdf")
    return export_document(
        pages=final_pages,
        page_spec=page_spec,
        theme=theme,
        doc_title=spec.booklet_title,
        output_path=out_path,
        output_format=spec.output_format,
        render_preview_png=spec.render_preview_png,
    )
