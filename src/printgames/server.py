"""PrintGames MCP Server — 16 print-ready puzzle and pen-and-paper game generators.

Compatible with both MCP SDK v2 (MCPServer) and v1 (FastMCP).
"""

from __future__ import annotations

import asyncio
import json
import socket
from pathlib import Path
from typing import Any

try:
    from mcp.server.mcpserver import MCPServer as _BaseMCPServer
    from mcp.server.mcpserver.exceptions import ToolError
except ImportError:  # pragma: no cover - fallback for mcp < 2.0
    from mcp.server.fastmcp.exceptions import ToolError
    from mcp.server.fastmcp import FastMCP as _BaseMCPServer  # type: ignore[no-redef]

from .core.icons import icon_names
from .core.pages import PAGE_SIZES
from .core.renderer import ExportResult, PdfExportError
from .core.themes import THEMES
from .games import GAME_REGISTRY, produce_booklet, produce_game
from .models import (
    AcrosticSpec,
    AnyGameSpec,
    AnagramScrambleSpec,
    BattleshipSpec,
    BoggleWordWheelSpec,
    BookletSpec,
    CategoriesSpec,
    ColorByNumberSpec,
    CryptogramSpec,
    DotsAndBoxesSpec,
    DotToDotSpec,
    HangmanSpec,
    HiddenPicturesSpec,
    MadLibsSpec,
    MazeSpec,
    RebusSpec,
    SpotTheDifferenceSpec,
    WordLadderSpec,
)

SERVER_INSTRUCTIONS = """
You are connected to the PrintGames MCP server, which generates publication-grade,
strictly page-fitted printable games (PDF and/or standalone HTML) across 16 game types.

MANDATORY RULES FOR AI CALLERS:
1. ALWAYS supply complete, original, audience-appropriate content and context:
   - Never pass placeholder text, lorem ipsum, or incomplete clues.
   - Always write clear, friendly player-facing `instructions` tailored to the exact game and age group.
   - Always choose an explicit `page_size` (letter, a4, a5, half_letter, kdp_6x9, kdp_8x10, square_8x8, legal, a3, custom),
     `orientation` (portrait/landscape), and `theme` (editorial_classic, botanical_ink, playful_studio, vintage_press, clean_minimal, ocean_breeze).
2. CALL `list_capabilities` (or read `printgames://instructions` and `printgames://icons`) before designing visual puzzles
   so you use valid icon names, coordinate ranges, and optimal page-size ergonomics.
3. DOUBLE-CHECK mathematical & linguistic constraints before invoking tools:
   - Word Ladders: every step in `solution_steps` must be the same length and change EXACTLY 1 letter.
   - Acrostics: the multiset of all letters across `clues[].answer` MUST exactly match all letters in `quote`.
   - Anagrams with `bonus_phrase`: circled letters at `circled_indices` must be an exact anagram of `bonus_phrase.answer`.
   - Word Wheels: every `sample_words` entry must include `center_letter` and only use wheel letters.
   - Spot the Difference: every non-`add` difference `target_id` must match an element `id` in `base_elements`.
   - Color-by-Number: every region `color_number` must exist in `palette`.
   - Mad Libs: `story_template` must contain 6 to 28 `{{PART OF SPEECH}}` or `{{PART OF SPEECH|hint}}` blanks.
4. If local PDF export fails and the error includes a print-ready HTML path, use an available browser printing tool to save the requested PDF. Honor CSS page size and print backgrounds, disable browser headers and footers, and verify the resulting pages.
5. Verify that `fit_verified` is true and review any warnings. If `render_preview_png=true` is used,
   you may inspect the generated PNGs to verify aesthetics.
""".strip()

mcp = _BaseMCPServer(
    "printgames",
    instructions=SERVER_INSTRUCTIONS,
)


def _format_export_result(game_type: str, title: str, result: ExportResult) -> dict[str, Any]:
    return {
        "status": "ok" if not result.warnings else "ok_with_warnings",
        "game_type": game_type,
        "title": title,
        "page_size": result.page_size_label,
        "page_dimensions_mm": {
            "width": result.page_dimensions_mm[0],
            "height": result.page_dimensions_mm[1],
        },
        "expected_pages": result.expected_pages,
        "verified_pdf_pages": result.verified_pdf_pages,
        "fit_verified": result.fit_verified,
        "files": result.output_paths,
        "warnings": result.warnings,
    }


def _export(spec: AnyGameSpec | BookletSpec) -> dict[str, Any]:
    try:
        if isinstance(spec, BookletSpec):
            return _format_export_result("booklet", spec.booklet_title, produce_booklet(spec))
        return _format_export_result(spec.game_type, spec.title, produce_game(spec))
    except PdfExportError as exc:
        raise ToolError(str(exc)) from exc


def _load_ai_instructions_text() -> str:
    candidate = Path(__file__).resolve().parents[2] / "AI_INSTRUCTIONS.md"
    if candidate.exists():
        return candidate.read_text(encoding="utf-8")
    return SERVER_INSTRUCTIONS


# =============================================================================
# DISCOVERY TOOL
# =============================================================================


@mcp.tool()
def list_capabilities() -> dict[str, Any]:
    """List all 16 supported print game types, page sizes, visual themes, and 75+ built-in SVG icon names.

    Call this first if you need exact icon names, page dimensions, or theme keys before generating a game.
    """
    return {
        "game_types": {
            k: {
                "category": cat,
                "tool_name": f"generate_{k}",
                "schema_model": model.__name__,
            }
            for k, (model, _, cat) in GAME_REGISTRY.items()
        },
        "booklet_tool": "create_game_booklet",
        "page_sizes": {
            k: {
                "label": v.label,
                "width_mm": v.width_mm,
                "height_mm": v.height_mm,
                "recommended_margin_mm": v.recommended_margin_mm,
                "description": v.description,
            }
            for k, v in PAGE_SIZES.items()
        },
        "themes": {
            k: {"label": v.label, "description": v.description, "accent": v.accent, "ink": v.ink}
            for k, v in THEMES.items()
        },
        "built_in_icons": icon_names(),
        "scene_element_types": [
            "icon",
            "text",
            "rect",
            "circle",
            "ellipse",
            "line",
            "polygon",
            "polyline",
            "path",
            "star",
            "scenic_tree",
            "scenic_pine",
            "scenic_house",
            "scenic_cloud",
            "scenic_mountain",
            "scenic_bush",
            "scenic_fence",
            "scenic_wave",
        ],
    }


# =============================================================================
# CATEGORY 1: WORD & LETTER PUZZLES (6 TOOLS)
# =============================================================================


@mcp.tool()
def generate_cryptogram(spec: CryptogramSpec) -> dict[str, Any]:
    """Generate a print-ready Cryptogram puzzle sheet (1–3 encrypted quotes + decoder scratchpad + optional Answer Key).

    Provide meaningful plaintext quotes, attributions, optional hint letters, clear instructions, page_size, and theme.
    """
    return _export(spec)


@mcp.tool()
def generate_word_ladder(spec: WordLadderSpec) -> dict[str, Any]:
    """Generate a print-ready Word Ladders sheet (1–4 ladders + optional rung clues + Answer Key).

    Every step in `solution_steps` must be identical length and differ by EXACTLY 1 letter from the previous step.
    """
    return _export(spec)


@mcp.tool()
def generate_anagram_scramble(spec: AnagramScrambleSpec) -> dict[str, Any]:
    """Generate a print-ready Anagrams & Word Scrambles sheet (4–20 items + optional Jumble bonus phrase + Answer Key).

    If `bonus_phrase` is provided, the letters at `circled_indices` across `items` must form an exact anagram of `bonus_phrase.answer`.
    """
    return _export(spec)


@mcp.tool()
def generate_acrostic(spec: AcrosticSpec) -> dict[str, Any]:
    """Generate a print-ready Acrostic puzzle (numbered transfer quote grid + two-column clues + Answer Key).

    IMPORTANT: The combined letters of all `clues[].answer` MUST match the exact multiset of letters in `quote`.
    """
    return _export(spec)


@mcp.tool()
def generate_boggle_word_wheel(spec: BoggleWordWheelSpec) -> dict[str, Any]:
    """Generate a print-ready Boggle Grid (4x4 or 5x5) OR circular Word Wheel puzzle with word log lines and Answer Key.

    For `mode='boggle_grid'`, supply `grid`. For `mode='word_wheel'`, supply `center_letter` and 6–10 `outer_letters`.
    Always provide verified `sample_words` for the Answer Key.
    """
    return _export(spec)


@mcp.tool()
def generate_rebus(spec: RebusSpec) -> dict[str, Any]:
    """Generate a print-ready Rebus Puzzles gallery (2–12 visual word-riddle cards + Answer Key with explanations).

    Each card uses a 240×150 canvas with declarative `text`, `icon` (from built-in library), and shape elements
    to craft clever spatial, typographic, and visual idioms.
    """
    return _export(spec)


# =============================================================================
# CATEGORY 2: VISUAL & SPATIAL ACTIVITIES (5 TOOLS)
# =============================================================================


@mcp.tool()
def generate_maze(spec: MazeSpec) -> dict[str, Any]:
    """Generate a print-ready solvable Maze ('rectangular', 'circular', or 'hexagonal') with BFS Answer Key.

    Provide thematic `title`, `instructions`, optional `story_prompt`, `start_label`/`end_label`, icons, dimensions, and `seed`.
    """
    return _export(spec)


@mcp.tool()
def generate_spot_the_difference(spec: SpotTheDifferenceSpec) -> dict[str, Any]:
    """Generate a print-ready Spot the Difference illustration pair (Picture A & mutated Picture B + Answer Key).

    Build a rich vector scene in `base_elements` (with unique `id`s) and specify 4–15 exact programmatic mutations
    in `differences` (remove, add, recolor, move, resize, rotate, flip_x, replace_icon, change_text).
    """
    return _export(spec)


@mcp.tool()
def generate_hidden_pictures(spec: HiddenPicturesSpec) -> dict[str, Any]:
    """Generate a print-ready Hidden Pictures (I Spy) sheet with detailed scene, visual icon checklist, and Answer Key.

    Compose a rich background scene in `background_elements` and disguise 5–16 `hidden_objects` inside it using
    built-in icons or custom SVG paths with thoughtful placement, scale, and rotation.
    """
    return _export(spec)


@mcp.tool()
def generate_dot_to_dot(spec: DotToDotSpec) -> dict[str, Any]:
    """Generate a print-ready Dot-to-Dot sheet (numbers, A–Z letters, or skip-counting) with automatic non-overlapping labels.

    Supply ordered point coordinates in `paths` forming a recognizable silhouette, optional pre-drawn `background_elements`
    (like eyes or scenery), and the hidden `subject` revealed on the Answer Key.
    """
    return _export(spec)


@mcp.tool()
def generate_color_by_number(spec: ColorByNumberSpec) -> dict[str, Any]:
    """Generate a print-ready Color-by-Number / Paint-by-Number illustration with numbered regions, palette key, and colored Answer Key.

    Define a harmonious `palette` (3–16 numbered colors) and closed vector `regions` (polygon, path, circle, ellipse, rect)
    making up the artwork. Region numbers are auto-centered if `label_x`/`label_y` are omitted.
    """
    return _export(spec)


# =============================================================================
# CATEGORY 3: MULTI-PLAYER PEN & PAPER GAMES (5 TOOLS)
# =============================================================================


@mcp.tool()
def generate_dots_and_boxes(spec: DotsAndBoxesSpec) -> dict[str, Any]:
    """Generate a print-ready Dots and Boxes sheet (1, 2, or 4 boards per page + player scorecards + optional guide lines)."""
    return _export(spec)


@mcp.tool()
def generate_battleship(spec: BattleshipSpec) -> dict[str, Any]:
    """Generate a print-ready Battleship command sheet (1 spacious sheet OR 2 cuttable side-by-side player sheets).

    Includes Defense Grid, Target Grid, customizable themed Fleet roster with hit checkboxes, and Hit/Miss legend.
    """
    return _export(spec)


@mcp.tool()
def generate_categories(spec: CategoriesSpec) -> dict[str, Any]:
    """Generate a print-ready Categories (Scattergories) score sheet (8–18 themed categories × 2–6 rounds, 1-up or 2-up cuttable)."""
    return _export(spec)


@mcp.tool()
def generate_hangman(spec: HangmanSpec) -> dict[str, Any]:
    """Generate a print-ready Hangman sheet (1, 2, or 4 rounds per page; gallows, snowman, flower, or rocket style).

    Supports open-play blank boards OR host-prepared `pre_filled_puzzles` with an automatic Host Secret Key page.
    """
    return _export(spec)


@mcp.tool()
def generate_mad_libs(spec: MadLibsSpec) -> dict[str, Any]:
    """Generate a print-ready Mad Libs activity (optional spoiler-free Word Collector Page 1 + spacious fill-in Story Sheet).

    Embed 6–28 blanks in `story_template` using `{{PART OF SPEECH}}` or `{{PART OF SPEECH|optional hint}}`.
    """
    return _export(spec)


# =============================================================================
# MULTI-GAME BOOKLET COMPILER
# =============================================================================


@mcp.tool()
def create_game_booklet(spec: BookletSpec) -> dict[str, Any]:
    """Compile 2–40 print games (any mix of the 16 types) into a single cohesive print-ready PDF booklet.

    Includes an optional Cover Page, automatic Table of Contents with page numbers, unified page size & theme,
    and collated Answer Keys at the back of the booklet.
    """
    return _export(spec)


# =============================================================================
# MCP RESOURCES & PROMPTS FOR AI DISCOVERY
# =============================================================================


@mcp.resource("printgames://instructions", mime_type="text/markdown")
def resource_instructions() -> str:
    """Comprehensive AI Operating Manual for designing beautiful print games via PrintGames MCP."""
    return _load_ai_instructions_text()


@mcp.resource("printgames://catalog", mime_type="application/json")
def resource_catalog() -> str:
    """JSON catalog of all 16 supported print game types grouped by category."""
    return json.dumps(list_capabilities()["game_types"], indent=2)


@mcp.resource("printgames://page-sizes", mime_type="application/json")
def resource_page_sizes() -> str:
    """JSON specifications of all supported print page sizes in millimeters."""
    return json.dumps(list_capabilities()["page_sizes"], indent=2)


@mcp.resource("printgames://themes", mime_type="application/json")
def resource_themes() -> str:
    """JSON specifications of all 6 editorial visual themes."""
    return json.dumps(list_capabilities()["themes"], indent=2)


@mcp.resource("printgames://icons", mime_type="application/json")
def resource_icons() -> str:
    """JSON list of all 75+ built-in SVG icon names usable across visual games."""
    return json.dumps({"count": len(icon_names()), "icons": icon_names()}, indent=2)


@mcp.prompt()
def design_print_game(game_type: str, topic: str, audience: str = "all ages", page_size: str = "letter") -> str:
    """Prompt template guiding an AI to design a rich, validated print game for a specific topic and audience."""
    return (
        f"Design a beautiful, print-ready '{game_type}' game about '{topic}' for '{audience}' "
        f"formatted for page_size='{page_size}'.\n\n"
        "Steps:\n"
        "1. Call `list_capabilities` (or read `printgames://instructions`) to verify exact icons, themes, and constraints.\n"
        "2. Craft 100% original, engaging, thematically rich content (clues, quotes, categories, story, or vector scene) "
        "along with tailored player-facing `instructions` and an appropriate `theme`.\n"
        "3. Double-check all game-specific constraints (e.g., letter multisets for Acrostics, 1-letter steps for Word Ladders, "
        "unique element IDs for Spot the Difference, valid palette refs for Color-by-Number).\n"
        f"4. Invoke `generate_{game_type}` with `output_format='pdf'` and verify `fit_verified` is true.\n"
        "5. Report the generated file path(s), page size, and page count to the user."
    )


@mcp.prompt()
def design_activity_booklet(
    booklet_title: str,
    theme_topic: str,
    audience: str = "family game night",
    page_size: str = "letter",
    game_count: int = 6,
) -> str:
    """Prompt template guiding an AI to produce a cohesive multi-game printable booklet."""
    return (
        f"Create a cohesive printable activity booklet titled '{booklet_title}' themed around '{theme_topic}' "
        f"for '{audience}' on '{page_size}' paper with {game_count} varied games.\n\n"
        "Steps:\n"
        "1. Call `list_capabilities` to pick a harmonious visual `theme` and choose a balanced mix across "
        "Word & Letter Puzzles, Visual & Spatial Activities, and Multi-Player Pen & Paper Games.\n"
        "2. Author complete, high-craft content for every game in the booklet (no placeholders).\n"
        "3. Call `create_game_booklet` with `include_cover=true`, `include_toc=true`, and `collate_answer_keys_at_end=true`.\n"
        "4. Verify `fit_verified` is true and present the finished booklet path and contents to the user."
    )


def main() -> None:
    """Entry point for running PrintGames as an MCP stdio server."""
    # Some managed environments allow socketpair creation but deny sends.
    # asyncio then silently drops worker-thread wakeups and the handshake stalls.
    try:
        reader, writer = socket.socketpair()
        with reader, writer:
            writer.send(b"x")
    except PermissionError:
        asyncio.run(_serve_with_timer())
    else:
        mcp.run(transport="stdio")


async def _serve_with_timer() -> None:
    loop = asyncio.get_running_loop()

    def tick() -> None:
        nonlocal timer
        timer = loop.call_later(0.05, tick)

    timer = loop.call_later(0.05, tick)
    try:
        await mcp.run_stdio_async()
    finally:
        timer.cancel()


if __name__ == "__main__":
    main()
