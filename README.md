# PrintGames MCP

A Model Context Protocol (MCP) server and rendering engine that generates **beautiful, publication-grade, strictly page-fitted printable games** (PDF and standalone HTML) across **22 classic game types** — plus multi-game activity booklets with cover pages, tables of contents, and collated answer keys.

## Supported Game Types (22)

### Word & Letter Puzzles
1. **Cryptograms** (`generate_cryptogram`) — Substitution-cipher quotes with hints, optional frequency counts, and A–Z decoder scratchpad.
2. **Word Ladders** (`generate_word_ladder`) — Validated 1-letter-per-step word chains with architectural rungs and optional clues.
3. **Anagrams & Word Scrambles** (`generate_anagram_scramble`) — Letter-tile scrambles with optional Jumble-style circled-letter bonus riddles and word banks.
4. **Acrostics** (`generate_acrostic`) — Numbered quote transfer grid paired with two-column clues and strict letter-multiset verification.
5. **Boggle-Style Grids & Word Wheels** (`generate_boggle_word_wheel`) — 4×4 / 5×5 tactile letter dice boards OR segmented circular word wheels with lined discovery logs.
6. **Rebus Puzzles** (`generate_rebus`) — Visual & typographic word-riddle cards powered by a 75+ built-in vector icon library and declarative layout primitives.

### Visual & Spatial Activities
7. **Mazes** (`generate_maze`) — Rectangular, circular (polar), and hexagonal (honeycomb) mazes using Recursive Backtracker, Prim's, or Braid algorithms with automatic BFS solution keys.
8. **Spot the Difference** (`generate_spot_the_difference`) — Declarative vector illustrations rendered side-by-side or stacked with exact programmatic differences and numbered reveal keys.
9. **Hidden Pictures / I Spy** (`generate_hidden_pictures`) — Detailed line-art/scenic vector illustrations disguising hidden objects + visual icon checklist + highlighted answer key.
10. **Dot-to-Dot** (`generate_dot_to_dot`) — Numbered, alphabetical, or skip-counting dot sequences with automatic collision-avoidance label positioning.
11. **Color-by-Number / Paint-by-Number** (`generate_color_by_number`) — Closed vector regions with auto-centered region numbers, swatch legend, and full-color answer key.

### Multi-Player Pen & Paper Games
12. **Dots and Boxes** (`generate_dots_and_boxes`) — 1, 2, or 4 boards per page with player scorecards and optional guide lines.
13. **Battleship** (`generate_battleship`) — Dual Defense/Target coordinate grids, customizable themed fleets, and 1-up or 2-up cuttable player sheets.
14. **Categories (Scattergories)** (`generate_categories`) — Curated category tables across multiple rounds with letter roll boxes and score totals.
15. **Hangman** (`generate_hangman`) — Classic gallows or family-friendly snowman, flower, and rocket themes; open-play or host-prepared rounds with Host Secret Key.
16. **Mad Libs** (`generate_mad_libs`) — Generously spaced fill-in story sheets with an optional Page-1 spoiler-free Word Collector sheet and grammar guide.

### Additional Printable Word & Logic Puzzles
17. **Word Search** (`generate_word_search`) — Seeded letter grids, difficulty-controlled directions, answer-key highlights, and teacher-supplied vocabulary.
18. **Number Search** (`generate_number_search`) — Search for number strings, including values with leading zeros, with solution paths.
19. **Crossword** (`generate_crossword`) — Numbered across/down crossword from teacher-authored `answer`/`clue` pairs; never silently omits clues.
20. **Fill-in Crossword / Kriss-Kross** (`generate_kriss_kross`) — Numbered blank crossword accompanied by a word bank grouped by answer length.
21. **Sudoku** (`generate_sudoku`) — Unique-solution 4×4, 6×6 and 9×9 printable Sudoku with answer key.
22. **Nonogram** (`generate_nonogram`) — Uniquely solvable 5×5 or 7×7 picture-logic puzzles with row/column run clues.

All six are registered in the **same MCP server**, use the standard `spec` envelope (`title`, `instructions`, `page_size`, `orientation`, `theme`, `ink_saver`, `include_answer_key`, `output_format`, and `output_path`), and work with `create_game_booklet`.

**Example: Word Search**

```json
{
  "game_type": "word_search",
  "title": "Rainforest Vocabulary",
  "instructions": "Circle each rainforest word in the letter grid, then tick it off below.",
  "words": ["JAGUAR", "CANOPY", "MONKEY", "TOUCAN"],
  "grid_size": 13,
  "seed": 42,
  "difficulty": "easy",
  "page_size": "a4",
  "theme": "playful_studio",
  "include_answer_key": true,
  "output_format": "both"
}
```

**Example: Crossword** — use `entries: [{"answer": "APPLE", "clue": "A crunchy fruit"}, ...]`, `grid_size: 19` (odd integer), and a reproducible `seed`.

### Bonus: Multi-Game Booklets
- **`create_game_booklet`** — Compiles 2–40 mixed games into a single print-ready PDF with Cover Page, automatic Table of Contents, unified styling, and collated Answer Keys at the back.

---

## Page Sizes & Themes

- **Page Sizes**: `letter` (8.5×11 in), `a4`, `a5`, `half_letter`, `kdp_6x9`, `kdp_8x10`, `square_8x8`, `legal`, `a3`, and `custom` (`custom_width_mm` × `custom_height_mm`), in `portrait` or `landscape`.
- **Visual Themes**: `editorial_classic`, `botanical_ink`, `playful_studio`, `vintage_press`, `clean_minimal`, `ocean_breeze`, plus `ink_saver: true` for crisp B&W home printing.
- **Fit Verification**: PDF exports check each sheet for clipped HTML content in Chromium and verify the page count with `pdfinfo`. A positive `fit_verified` requires both checks to pass. Warnings identify clipped pages.
- **If the browser cannot start**: PDF requests return an error with the path to a printable HTML copy. A connected browser can open that file and export it with CSS page size, background graphics, and browser headers and footers turned off. For manual export, choose Print → Save as PDF.

---

## Quick Start

### Prerequisites
- Python 3.11+ and [`uv`](https://docs.astral.sh/uv/)
- Google Chrome or Chromium installed (for print-exact PDF export; HTML output works with zero browser dependency). PrintGames tries installed Chromium browsers if the first one fails. Set `PRINTGAMES_CHROME` to select a specific executable or a compatible browser launcher.
- Optional: `poppler-utils` (`pdfinfo`, `pdftoppm`) for PDF page verification & PNG previews

### Install
```bash
git clone https://github.com/deonsa/printgames.git
cd printgames
uv sync
```

### Run as an MCP Server (stdio)
```bash
uv run printgames-mcp
# or
uv run printgames serve
```

### Configure in MCP Clients (Claude Desktop, Cursor, Antigravity, VS Code)
```json
{
  "mcpServers": {
    "printgames": {
      "command": "uv",
      "args": ["--directory", "/path/to/printgames", "run", "printgames-mcp"]
    }
  }
}
```

### CLI Usage
```bash
# Render a single game from a JSON specification
uv run printgames render path/to/game.json -o output/game.pdf --preview

# Render a multi-game booklet
uv run printgames booklet path/to/booklet.json -o output/booklet.pdf
```

---

## Instructions for AI Agents

See [AI_INSTRUCTIONS.md](./AI_INSTRUCTIONS.md) (also exposed live by the MCP server at resource URI `printgames://instructions`).
