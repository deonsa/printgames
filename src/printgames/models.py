"""Strict Pydantic v2 schemas for all 16 print game types and multi-game booklets.

Every schema requires the calling AI to supply complete, thoughtful puzzle content,
instructions, and page/theme settings so generated printables are rich and error-free.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .core.icons import ICONS
from .core.pages import Orientation, PageSizeName
from .core.themes import ThemeName

Difficulty = Literal["easy", "medium", "hard", "expert", "all_ages"]
OutputFormat = Literal["pdf", "html", "both"]


class BaseGameSpec(BaseModel):
    """Shared layout, editorial metadata, and export parameters required for every game."""

    title: str = Field(..., min_length=2, max_length=90, description="Printed puzzle title.")
    instructions: str = Field(
        ...,
        min_length=12,
        max_length=420,
        description="Clear player-facing rules tailored to this specific game and audience.",
    )
    subtitle: str | None = Field(
        default=None,
        max_length=110,
        description="Optional thematic subtitle shown beneath the title.",
    )
    difficulty: Difficulty | None = Field(
        default=None,
        description="Optional difficulty badge: easy, medium, hard, expert, or all_ages.",
    )
    author_credit: str | None = Field(
        default=None,
        max_length=80,
        description="Optional footer credit (e.g., author, family name, classroom, event).",
    )
    page_size: PageSizeName = Field(
        default="letter",
        description="Physical page size: letter, a4, a5, half_letter, kdp_6x9, kdp_8x10, square_8x8, legal, a3, or custom.",
    )
    orientation: Orientation = Field(
        default="portrait",
        description="Page orientation: portrait or landscape.",
    )
    margin_mm: float | None = Field(
        default=None,
        ge=4.0,
        le=40.0,
        description="Optional override for outer page margin in millimeters.",
    )
    custom_width_mm: float | None = Field(
        default=None,
        ge=80.0,
        le=600.0,
        description="Required when page_size='custom'. Width in mm.",
    )
    custom_height_mm: float | None = Field(
        default=None,
        ge=80.0,
        le=600.0,
        description="Required when page_size='custom'. Height in mm.",
    )
    theme: ThemeName = Field(
        default="editorial_classic",
        description="Visual theme: editorial_classic, botanical_ink, playful_studio, vintage_press, clean_minimal, or ocean_breeze.",
    )
    ink_saver: bool = Field(
        default=False,
        description="Set true for high-contrast black-and-white home-printer ink-saver mode.",
    )
    include_answer_key: bool = Field(
        default=True,
        description="Include a clean Answer Key page where applicable.",
    )
    output_path: str | None = Field(
        default=None,
        description="Target file path (e.g., 'output/my_puzzle.pdf'). Defaults into ./output/.",
    )
    output_format: OutputFormat = Field(
        default="pdf",
        description="Output format: 'pdf' (default), 'html', or 'both'.",
    )
    render_preview_png: bool = Field(
        default=False,
        description="If true and PDF is generated, also render PNG previews of each page.",
    )


# =============================================================================
# CATEGORY 1: WORD & LETTER PUZZLES
# =============================================================================


class CryptogramItem(BaseModel):
    plaintext: str = Field(
        ...,
        min_length=12,
        max_length=280,
        description="The quote or message to encrypt using a monoalphabetic substitution cipher.",
    )
    attribution: str | None = Field(
        default=None,
        max_length=80,
        description="Author or source of the quote.",
    )
    encrypt_attribution: bool = Field(
        default=True,
        description="Whether to also encrypt the attribution using the same cipher.",
    )
    hint_letters: list[str] = Field(
        default_factory=list,
        description="Plaintext letters to pre-reveal as starter hints (e.g., ['E', 'T']).",
    )
    theme_clue: str | None = Field(
        default=None,
        max_length=100,
        description="Optional short thematic clue printed above the cryptogram.",
    )
    seed: int = Field(
        default=42,
        description="Deterministic seed for generating a valid derangement cipher (no letter maps to itself).",
    )
    custom_cipher_map: dict[str, str] | None = Field(
        default=None,
        description="Optional explicit mapping of plaintext A-Z -> ciphertext A-Z.",
    )

    @field_validator("hint_letters")
    @classmethod
    def _normalize_hints(cls, v: list[str]) -> list[str]:
        out = []
        for ch in v:
            c = ch.strip().upper()
            if not re.fullmatch(r"[A-Za-z]", ch.strip()):
                raise ValueError(f"hint_letters entries must be single A-Z letters, got '{ch}'.")
            out.append(c)
        return out


class CryptogramSpec(BaseGameSpec):
    game_type: Literal["cryptogram"] = "cryptogram"
    puzzles: list[CryptogramItem] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="1 to 3 cryptogram quotes to fit cleanly on the page.",
    )
    show_alphabet_tracker: bool = Field(
        default=True,
        description="Display an A-Z cipher decoding scratchpad strip at the bottom.",
    )
    show_letter_frequency: bool = Field(
        default=False,
        description="Display ciphertext letter frequency counts as an aid.",
    )


class WordLadderItem(BaseModel):
    label: str | None = Field(default=None, max_length=60, description="Optional ladder heading.")
    start_word: str = Field(..., min_length=3, max_length=8, description="Starting word.")
    end_word: str = Field(..., min_length=3, max_length=8, description="Target final word.")
    solution_steps: list[str] = Field(
        ...,
        min_length=3,
        max_length=10,
        description="Complete valid chain from start_word to end_word inclusive, changing exactly 1 letter per step.",
    )
    step_clues: list[str] | None = Field(
        default=None,
        description="Optional clues for each intermediate word (length = len(solution_steps) - 2).",
    )

    @model_validator(mode="after")
    def _validate_ladder(self) -> WordLadderItem:
        steps = [w.strip().upper() for w in self.solution_steps]
        start = self.start_word.strip().upper()
        end = self.end_word.strip().upper()
        if not start.isalpha() or not end.isalpha():
            raise ValueError("start_word and end_word must contain only A-Z letters.")
        if steps[0] != start or steps[-1] != end:
            raise ValueError(
                f"solution_steps must begin with '{start}' and end with '{end}', got '{steps[0]}' -> '{steps[-1]}'."
            )
        word_len = len(start)
        for i, w in enumerate(steps):
            if not w.isalpha() or len(w) != word_len:
                raise ValueError(
                    f"Every word in solution_steps must be {word_len} alphabetic letters (step {i}: '{w}')."
                )
            if i > 0:
                diffs = sum(1 for a, b in zip(steps[i - 1], w) if a != b)
                if diffs != 1:
                    raise ValueError(
                        f"Word ladder step '{steps[i - 1]}' -> '{w}' changes {diffs} letters; must change exactly 1."
                    )
        if self.step_clues is not None and len(self.step_clues) != len(steps) - 2:
            raise ValueError(
                f"step_clues must have {len(steps) - 2} entries (one per intermediate rung), got {len(self.step_clues)}."
            )
        self.start_word = start
        self.end_word = end
        self.solution_steps = steps
        return self


class WordLadderSpec(BaseGameSpec):
    game_type: Literal["word_ladder"] = "word_ladder"
    ladders: list[WordLadderItem] = Field(
        ...,
        min_length=1,
        max_length=4,
        description="1 to 4 word ladders arranged neatly on the page.",
    )


class ScrambleItem(BaseModel):
    answer: str = Field(..., min_length=3, max_length=24, description="The unscrambled real word or short phrase.")
    scrambled: str | None = Field(
        default=None,
        description="Optional explicit scrambled version; auto-scrambled deterministically if omitted.",
    )
    clue: str | None = Field(default=None, max_length=90, description="Optional definition or thematic hint.")
    circled_indices: list[int] = Field(
        default_factory=list,
        description="0-based letter indices in answer (ignoring spaces) circled to form a bonus final phrase.",
    )

    @model_validator(mode="after")
    def _validate_scramble(self) -> ScrambleItem:
        clean = self.answer.strip().upper()
        letters = [c for c in clean if c.isalpha()]
        if len(letters) < 3:
            raise ValueError(f"Scramble answer '{self.answer}' must have at least 3 letters.")
        for idx in self.circled_indices:
            if idx < 0 or idx >= len(letters):
                raise ValueError(
                    f"circled_indices {idx} out of range for '{clean}' ({len(letters)} letters)."
                )
        if self.scrambled is not None:
            sc_letters = sorted(c for c in self.scrambled.upper() if c.isalpha())
            if sc_letters != sorted(letters):
                raise ValueError(
                    f"Provided scrambled '{self.scrambled}' does not contain the exact same letters as '{clean}'."
                )
        self.answer = clean
        return self


class BonusPhrase(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=140, description="Riddle or prompt for the final unscrambled phrase.")
    answer: str = Field(..., min_length=3, max_length=40, description="Final bonus answer formed from circled letters.")


class AnagramScrambleSpec(BaseGameSpec):
    game_type: Literal["anagram_scramble"] = "anagram_scramble"
    items: list[ScrambleItem] = Field(
        ...,
        min_length=4,
        max_length=20,
        description="4 to 20 scrambled words/anagrams.",
    )
    bonus_phrase: BonusPhrase | None = Field(
        default=None,
        description="Optional Jumble-style final bonus riddle using the circled letters from items.",
    )
    show_word_bank: bool = Field(
        default=False,
        description="Optional shuffled word bank at bottom (great for younger players).",
    )
    seed: int = Field(default=7, description="Seed for deterministic auto-scrambling.")

    @model_validator(mode="after")
    def _validate_bonus(self) -> AnagramScrambleSpec:
        if self.bonus_phrase is not None:
            circled: list[str] = []
            for item in self.items:
                letters = [c for c in item.answer if c.isalpha()]
                for idx in item.circled_indices:
                    circled.append(letters[idx])
            target = [c for c in self.bonus_phrase.answer.upper() if c.isalpha()]
            if sorted(circled) != sorted(target):
                raise ValueError(
                    "Circled letters from items "
                    f"({''.join(sorted(circled))}) must be an exact anagram of bonus_phrase.answer "
                    f"({''.join(sorted(target))})."
                )
        return self


class AcrosticClue(BaseModel):
    label: str = Field(..., min_length=1, max_length=2, description="Clue letter label (A, B, C, ...).")
    clue: str = Field(..., min_length=3, max_length=120, description="Clue text for this answer word.")
    answer: str = Field(..., min_length=2, max_length=16, description="Letters-only answer word.")

    @field_validator("answer")
    @classmethod
    def _clean_answer(cls, v: str) -> str:
        cleaned = re.sub(r"[^A-Za-z]", "", v).upper()
        if len(cleaned) < 2:
            raise ValueError(f"Acrostic clue answer '{v}' must have at least 2 letters.")
        return cleaned


class AcrosticSpec(BaseGameSpec):
    game_type: Literal["acrostic"] = "acrostic"
    quote: str = Field(
        ...,
        min_length=20,
        max_length=165,
        description="Hidden quote spelled out in the numbered transfer grid.",
    )
    author_and_source: str = Field(
        ...,
        min_length=3,
        max_length=90,
        description="Author and source of the quote (classic acrostics spell this with clue first letters).",
    )
    clues: list[AcrosticClue] = Field(
        ...,
        min_length=4,
        max_length=26,
        description="Clues whose combined letters are an exact 1-to-1 match for the letters in quote.",
    )
    require_first_letters_spell_author: bool = Field(
        default=False,
        description="If true, validates that the first letters of clue answers spell author_and_source.",
    )
    seed: int = Field(default=19, description="Seed for distributing numbered positions across clues.")

    @model_validator(mode="after")
    def _validate_acrostic(self) -> AcrosticSpec:
        quote_letters = sorted(c for c in self.quote.upper() if c.isalpha())
        clue_letters = sorted("".join(c.answer for c in self.clues))
        if quote_letters != clue_letters:
            q_cnt = Counter(quote_letters)
            c_cnt = Counter(clue_letters)
            missing = "".join(sorted((q_cnt - c_cnt).elements()))
            extra = "".join(sorted((c_cnt - q_cnt).elements()))
            raise ValueError(
                "Acrostic clue answers must contain the EXACT same multiset of letters as quote. "
                f"Missing from clues: '{missing or 'none'}'; extra in clues: '{extra or 'none'}'."
            )
        if self.require_first_letters_spell_author:
            firsts = "".join(c.answer[0] for c in self.clues)
            expected = re.sub(r"[^A-Za-z]", "", self.author_and_source).upper()
            if firsts != expected:
                raise ValueError(
                    f"First letters of clue answers ('{firsts}') must spell author_and_source ('{expected}')."
                )
        return self


def _grid_contains_word(grid: list[list[str]], word: str) -> bool:
    size = len(grid)
    tiles = [tile for row in grid for tile in row]
    if Counter(word) - Counter("".join(tiles)):
        return False

    def trace(row: int, col: int, offset: int, visited: int) -> bool:
        cell = row * size + col
        bit = 1 << cell
        tile = tiles[cell]
        if visited & bit or not word.startswith(tile, offset):
            return False
        offset += len(tile)
        if offset == len(word):
            return True
        visited |= bit
        return any(
            trace(r, c, offset, visited)
            for r in range(max(0, row - 1), min(size, row + 2))
            for c in range(max(0, col - 1), min(size, col + 2))
        )

    return any(trace(r, c, 0, 0) for r in range(size) for c in range(size))


class BoggleWordWheelSpec(BaseGameSpec):
    game_type: Literal["boggle_word_wheel"] = "boggle_word_wheel"
    mode: Literal["boggle_grid", "word_wheel"] = Field(
        ...,
        description="Choose 'boggle_grid' (NxN adjacent letter dice) or 'word_wheel' (circular wheel with mandatory center letter).",
    )
    # Boggle grid fields
    grid: list[list[str]] | None = Field(
        default=None,
        description="Required for mode='boggle_grid': 4x4 or 5x5 2D array of letters (e.g., [['S','T','A','R'], ...]; 'Qu' supported).",
    )
    # Word wheel fields
    center_letter: str | None = Field(
        default=None,
        description="Required for mode='word_wheel': single mandatory center letter.",
    )
    outer_letters: list[str] | None = Field(
        default=None,
        description="Required for mode='word_wheel': 6 to 10 surrounding letters.",
    )
    pangram_word: str | None = Field(
        default=None,
        description="Optional full-wheel word using every letter (shown in Answer Key).",
    )
    # Shared gameplay metadata
    min_word_length: int = Field(default=3, ge=3, le=6, description="Minimum accepted word length.")
    timer_suggestion: str | None = Field(default="3 Minutes", description="Suggested round timer badge.")
    target_goals: dict[str, int] = Field(
        default_factory=lambda: {"Good": 12, "Great": 20, "Genius": 30},
        description="Word-count milestones shown as player goals.",
    )
    scoring_table: dict[str, str] | None = Field(
        default=None,
        description="Optional Boggle point values by word length (e.g. {'3-4': '1 pt', '5': '2 pts', '6': '3 pts', '7+': '5 pts'}).",
    )
    writing_lines: int = Field(
        default=36,
        ge=12,
        le=60,
        description="Number of lined spaces provided for players to write discovered words.",
    )
    sample_words: list[str] = Field(
        ...,
        min_length=6,
        max_length=60,
        description="AI-verified valid words from this grid/wheel printed on the Answer Key.",
    )

    @model_validator(mode="after")
    def _validate_mode(self) -> BoggleWordWheelSpec:
        for word in self.sample_words:
            if len(word.strip()) < self.min_word_length:
                raise ValueError(f"Sample word '{word}' is shorter than min_word_length.")
        if self.mode == "boggle_grid":
            if not self.grid or len(self.grid) not in (4, 5):
                raise ValueError("mode='boggle_grid' requires a 4x4 or 5x5 grid.")
            n = len(self.grid)
            for row in self.grid:
                if len(row) != n:
                    raise ValueError(f"Boggle grid must be square ({n}x{n}).")
                for tile in row:
                    if not re.fullmatch(r"[A-Za-z]|[Qq][Uu]", tile.strip()):
                        raise ValueError(f"Invalid Boggle tile '{tile}'. Use A–Z or Qu.")
            self.grid = [[tile.strip().upper() for tile in row] for row in self.grid]
            for word in self.sample_words:
                if not _grid_contains_word(self.grid, word.strip().upper()):
                    raise ValueError(f"Sample word '{word}' cannot be traced on this Boggle grid.")
        else:
            if not self.center_letter or len(self.center_letter.strip()) != 1:
                raise ValueError("mode='word_wheel' requires a single center_letter.")
            if not self.outer_letters or not (6 <= len(self.outer_letters) <= 10):
                raise ValueError("mode='word_wheel' requires 6 to 10 outer_letters.")
            self.center_letter = self.center_letter.strip().upper()
            self.outer_letters = [c.strip().upper() for c in self.outer_letters]
            avail = Counter([self.center_letter, *self.outer_letters])
            for word in self.sample_words:
                w = word.strip().upper()
                if self.center_letter not in w:
                    raise ValueError(
                        f"Word wheel sample word '{w}' must contain center_letter '{self.center_letter}'."
                    )
                if Counter(w) - avail:
                    raise ValueError(
                        f"Word wheel sample word '{w}' uses letters not present in the wheel."
                    )
        return self


class RebusCard(BaseModel):
    answer: str = Field(..., min_length=2, max_length=80, description="The decoded common phrase or idiom.")
    explanation: str | None = Field(
        default=None,
        max_length=140,
        description="Brief explanation printed in the Answer Key.",
    )
    hint: str | None = Field(default=None, max_length=60, description="Optional subtle hint under the card.")
    elements: list[dict[str, Any]] = Field(
        ...,
        min_length=1,
        max_length=24,
        description=(
            "Visual elements positioned on a 240x160 card canvas. Supports type='text' "
            "(text, x, y, font_size, weight, color, rotate, italic, underline, strikethrough, vertical, letter_spacing), "
            "type='icon' (icon_name, x, y, size, stroke, fill, rotate), and shapes (line, rect, circle, path, polygon)."
        ),
    )


class RebusSpec(BaseGameSpec):
    game_type: Literal["rebus"] = "rebus"
    puzzles: list[RebusCard] = Field(
        ...,
        min_length=2,
        max_length=12,
        description="2 to 12 visual Rebus riddle cards arranged in a clean gallery grid.",
    )
    columns: int | None = Field(
        default=None,
        ge=2,
        le=3,
        description="Optional override for grid columns (2 or 3). Auto-selected from puzzle count if omitted.",
    )


# =============================================================================
# CATEGORY 2: VISUAL & SPATIAL ACTIVITIES
# =============================================================================


class MazeSpec(BaseGameSpec):
    game_type: Literal["maze"] = "maze"
    shape: Literal["rectangular", "circular", "hexagonal"] = Field(
        default="rectangular",
        description="Maze geometry: 'rectangular', 'circular' (polar rings), or 'hexagonal' (honeycomb).",
    )
    cols: int = Field(
        default=18,
        ge=6,
        le=42,
        description="Columns for rectangular/hexagonal mazes (recommended 10-28 for crisp printability).",
    )
    rows: int = Field(
        default=22,
        ge=6,
        le=48,
        description="Rows for rectangular/hexagonal mazes (recommended 12-32).",
    )
    rings: int = Field(
        default=9,
        ge=4,
        le=16,
        description="Concentric rings for shape='circular' mazes.",
    )
    algorithm: Literal["recursive_backtracker", "prims", "braid"] = Field(
        default="recursive_backtracker",
        description="Maze generation style: recursive_backtracker (long winding corridors), prims (branchy), or braid (loops).",
    )
    braid_ratio: float = Field(
        default=0.25,
        ge=0.0,
        le=0.7,
        description="Fraction of dead-ends opened into loops when algorithm='braid'.",
    )
    seed: int = Field(default=101, description="Deterministic RNG seed for reproducible mazes.")
    start_label: str = Field(default="START", max_length=28, description="Label at the maze entrance.")
    end_label: str = Field(default="FINISH", max_length=28, description="Label at the maze exit.")
    start_icon: str | None = Field(default=None, description="Optional icon name from library for the start marker.")
    end_icon: str | None = Field(default=None, description="Optional icon name from library for the finish marker.")
    story_prompt: str | None = Field(
        default=None,
        max_length=220,
        description="Optional narrative banner above the maze (e.g., story context for kids or themed booklets).",
    )
    wall_style: Literal["crisp", "rounded"] = Field(default="rounded", description="Line cap style for maze walls.")

    @field_validator("start_icon", "end_icon")
    @classmethod
    def _check_icon(cls, v: str | None) -> str | None:
        if v is None:
            return None
        key = v.strip().lower().replace(" ", "_").replace("-", "_")
        if key not in ICONS:
            raise ValueError(f"Unknown icon '{v}'. Check list_capabilities for valid icon names.")
        return key


class SpotDifferenceChange(BaseModel):
    number: int = Field(..., ge=1, le=20, description="Difference number (1..N).")
    target_id: str = Field(
        ...,
        description="Element 'id' from base_elements to modify (or '__add__' when change_type='add').",
    )
    change_type: Literal[
        "remove",
        "add",
        "recolor",
        "move",
        "resize",
        "rotate",
        "flip_x",
        "replace_icon",
        "change_text",
    ] = Field(..., description="Exact mutation applied to Picture B only.")
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Mutation parameters: e.g. {dx, dy}, {fill}, {scale}, {angle}, {icon_name}, {text}, or {element}.",
    )
    description: str = Field(
        ...,
        min_length=4,
        max_length=120,
        description="Clear description of this difference for the Answer Key.",
    )
    marker_x: float | None = Field(default=None, description="Optional override X for Answer Key circle.")
    marker_y: float | None = Field(default=None, description="Optional override Y for Answer Key circle.")


class SpotTheDifferenceSpec(BaseGameSpec):
    game_type: Literal["spot_the_difference"] = "spot_the_difference"
    scene_description: str = Field(
        ...,
        min_length=8,
        max_length=180,
        description="Short description of the illustrated scene.",
    )
    canvas_width: float = Field(default=480.0, ge=200.0, le=1000.0)
    canvas_height: float = Field(default=300.0, ge=150.0, le=1000.0)
    sky_color: str = Field(default="#EAF4FB", description="Top backdrop color.")
    ground_color: str | None = Field(default="#DDECD5", description="Optional lower ground color.")
    horizon_y: float | None = Field(default=205.0, description="Y coordinate separating sky and ground.")
    base_elements: list[dict[str, Any]] = Field(
        ...,
        min_length=8,
        max_length=120,
        description="Vector scene elements forming Picture A. Every element that may change MUST have a unique 'id'.",
    )
    differences: list[SpotDifferenceChange] = Field(
        ...,
        min_length=4,
        max_length=15,
        description="4 to 15 exact differences applied to Picture B.",
    )
    layout: Literal["auto", "stacked", "side_by_side"] = Field(
        default="auto",
        description="'stacked' works best in portrait; 'side_by_side' works best in landscape; 'auto' picks based on orientation.",
    )
    show_checklist: bool = Field(
        default=True,
        description="Display numbered checkboxes at bottom to track discovered differences.",
    )

    @model_validator(mode="after")
    def _validate_diff_targets(self) -> SpotTheDifferenceSpec:
        ids = {str(el["id"]) for el in self.base_elements if el.get("id") is not None}
        for d in self.differences:
            if d.change_type != "add" and d.target_id not in ids:
                raise ValueError(
                    f"Difference #{d.number} targets id '{d.target_id}', which is not present in base_elements."
                )
        return self


class HiddenObjectItem(BaseModel):
    name: str = Field(..., min_length=2, max_length=40, description="Display name in the 'Objects to Find' checklist.")
    icon_name: str | None = Field(
        default=None,
        description="Icon name from built-in library (provide icon_name OR custom_svg_path).",
    )
    custom_svg_path: str | None = Field(
        default=None,
        description="Optional custom SVG path 'd' inside 24x24 viewBox if not using a built-in icon.",
    )
    x: float = Field(..., description="X center coordinate in scene canvas.")
    y: float = Field(..., description="Y center coordinate in scene canvas.")
    size: float = Field(default=24.0, ge=10.0, le=90.0, description="Rendered size in canvas units.")
    rotate: float = Field(default=0.0, description="Rotation angle in degrees for clever camouflage.")
    flip_x: bool = Field(default=False, description="Horizontal mirror flip.")
    stroke: str | None = Field(default=None, description="Optional camouflage stroke color (defaults to scene ink).")
    fill: str = Field(default="none", description="Optional fill (usually 'none' or subtle tint to blend in).")
    stroke_width: float = Field(default=1.4, ge=0.6, le=3.0)
    opacity: float = Field(default=0.88, ge=0.35, le=1.0)
    hint: str | None = Field(default=None, max_length=90, description="Optional location hint for Answer Key.")

    @model_validator(mode="after")
    def _validate_shape(self) -> HiddenObjectItem:
        if not self.icon_name and not self.custom_svg_path:
            raise ValueError(f"Hidden object '{self.name}' requires either icon_name or custom_svg_path.")
        if self.icon_name:
            key = self.icon_name.strip().lower().replace(" ", "_").replace("-", "_")
            if key not in ICONS:
                raise ValueError(f"Unknown icon_name '{self.icon_name}' on hidden object '{self.name}'.")
            self.icon_name = key
        return self


class HiddenPicturesSpec(BaseGameSpec):
    game_type: Literal["hidden_pictures"] = "hidden_pictures"
    scene_description: str = Field(..., min_length=8, max_length=180, description="Description of the illustrated scene.")
    canvas_width: float = Field(default=620.0, ge=250.0, le=1200.0)
    canvas_height: float = Field(default=420.0, ge=200.0, le=1000.0)
    background_color: str = Field(default="#FFFFFF", description="Canvas background color.")
    background_elements: list[dict[str, Any]] = Field(
        ...,
        min_length=10,
        max_length=180,
        description="Detailed line-art/scenic background elements that visually disguise the hidden objects.",
    )
    hidden_objects: list[HiddenObjectItem] = Field(
        ...,
        min_length=5,
        max_length=16,
        description="5 to 16 disguised objects hidden inside the scene and listed in the checklist.",
    )
    checklist_style: Literal["icon_and_label", "label_only"] = Field(
        default="icon_and_label",
        description="Show mini visual icons alongside each object name in the checklist, or labels only.",
    )


class DotPoint(BaseModel):
    x: float
    y: float
    label_dx: float | None = Field(default=None, description="Optional manual label X offset.")
    label_dy: float | None = Field(default=None, description="Optional manual label Y offset.")


class DotSubPath(BaseModel):
    points: list[DotPoint] = Field(..., min_length=2, description="Ordered points in this continuous stroke.")
    close_path: bool = Field(default=False, description="Connect the last dot of this sub-path back to its first dot.")


class DotToDotSpec(BaseGameSpec):
    game_type: Literal["dot_to_dot"] = "dot_to_dot"
    subject: str = Field(
        ...,
        min_length=2,
        max_length=60,
        description="Name of the hidden picture revealed when dots are connected (shown on Answer Key).",
    )
    reveal_subject_on_puzzle: bool = Field(
        default=False,
        description="If false, keeps the subject a surprise until the Answer Key!",
    )
    canvas_width: float = Field(default=500.0, ge=200.0, le=1000.0)
    canvas_height: float = Field(default=520.0, ge=200.0, le=1000.0)
    sequence_type: Literal["numbers", "uppercase_letters", "lowercase_letters", "skip_count"] = Field(
        default="numbers",
        description="Dot labeling sequence: numbers (1,2,3..), uppercase_letters (A,B,C..), lowercase_letters, or skip_count.",
    )
    skip_step: int = Field(default=2, ge=2, le=25, description="Step increment when sequence_type='skip_count'.")
    paths: list[DotSubPath] = Field(
        ...,
        min_length=1,
        max_length=8,
        description="One or more ordered dot paths forming the drawing. Multiple sub-paths show a star lift indicator.",
    )
    background_elements: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Pre-drawn context details (eyes, water lines, ground, stems) rendered softly on the puzzle page.",
    )
    solution_fill: str | None = Field(
        default=None,
        description="Optional gentle fill color applied to closed paths on the Answer Key.",
    )

    @model_validator(mode="after")
    def _validate_total_dots(self) -> DotToDotSpec:
        total = sum(len(sp.points) for sp in self.paths)
        if total < 8:
            raise ValueError(f"Dot-to-dot must have at least 8 total dots, got {total}.")
        if self.sequence_type in {"uppercase_letters", "lowercase_letters"} and total > 26:
            raise ValueError(
                f"Letter sequence supports at most 26 dots, got {total}. Use 'numbers' or 'skip_count'."
            )
        return self


class PaletteColor(BaseModel):
    number: int = Field(..., ge=1, le=24, description="Region number matching this color.")
    color_name: str = Field(..., min_length=2, max_length=32, description="Human-readable color name (e.g., 'Sky Blue').")
    hex_color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex fill color (e.g., '#7CC6FE').")


class ColorRegion(BaseModel):
    color_number: int = Field(..., ge=1, le=24, description="Palette number assigned to this region.")
    shape_type: Literal["polygon", "path", "circle", "ellipse", "rect"] = "polygon"
    points: list[list[float]] | None = Field(default=None, description="Vertex list [[x,y], ...] for shape_type='polygon'.")
    d: str | None = Field(default=None, description="SVG path data for shape_type='path'.")
    cx: float | None = None
    cy: float | None = None
    r: float | None = None
    rx: float | None = None
    ry: float | None = None
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None
    label_x: float | None = Field(default=None, description="X for the region number. Required for SVG paths.")
    label_y: float | None = Field(default=None, description="Y for the region number. Required for SVG paths.")
    label_size: float | None = Field(default=None, ge=7.0, le=28.0, description="Optional font size override for region number.")

    @model_validator(mode="after")
    def _validate_path_label(self) -> ColorRegion:
        if self.shape_type == "path":
            if not self.d or not self.d.strip():
                raise ValueError("A path region requires SVG path data in d.")
            if self.label_x is None or self.label_y is None:
                raise ValueError("A path region requires label_x and label_y inside the region.")
        return self


class ColorByNumberSpec(BaseGameSpec):
    game_type: Literal["color_by_number"] = "color_by_number"
    subject: str = Field(..., min_length=2, max_length=80, description="Title/subject of the artwork.")
    canvas_width: float = Field(default=500.0, ge=200.0, le=1000.0)
    canvas_height: float = Field(default=480.0, ge=200.0, le=1000.0)
    palette: list[PaletteColor] = Field(
        ...,
        min_length=3,
        max_length=16,
        description="Numbered color legend (3 to 16 colors).",
    )
    regions: list[ColorRegion] = Field(
        ...,
        min_length=6,
        max_length=180,
        description="Closed vector regions making up the line drawing.",
    )
    decorative_elements: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Optional un-numbered detail strokes (eyes, outlines, stems) drawn on top.",
    )
    show_color_swatches: bool = Field(
        default=True,
        description="Show colored swatches in the palette key (automatically monochrome-friendly in ink_saver mode).",
    )

    @model_validator(mode="after")
    def _validate_palette_refs(self) -> ColorByNumberSpec:
        nums = {p.number for p in self.palette}
        if len(nums) != len(self.palette):
            raise ValueError("Palette numbers must be unique.")
        for idx, r in enumerate(self.regions):
            if r.color_number not in nums:
                raise ValueError(
                    f"Region #{idx} references color_number {r.color_number}, which is not in palette {sorted(nums)}."
                )
        return self


# =============================================================================
# CATEGORY 3: MULTI-PLAYER PEN & PAPER GAMES
# =============================================================================


class DotsAndBoxesSpec(BaseGameSpec):
    game_type: Literal["dots_and_boxes"] = "dots_and_boxes"
    include_answer_key: bool = Field(default=False)
    rows: int = Field(default=8, ge=4, le=16, description="Number of dots vertically per board.")
    cols: int = Field(default=8, ge=4, le=16, description="Number of dots horizontally per board.")
    boards_per_page: Literal[1, 2, 4] = Field(
        default=1,
        description="1 giant board, 2 medium boards, or 4 quick-play boards on the page.",
    )
    player_count: int = Field(default=2, ge=2, le=4, description="Number of player score boxes.")
    player_labels: list[str] | None = Field(
        default=None,
        description="Optional player names or labels (defaults to Player 1, Player 2, ...).",
    )
    show_guide_lines: bool = Field(
        default=False,
        description="Draw ultra-faint dotted guide lines between dots (helpful for young players).",
    )
    pre_drawn_edges: list[list[int]] = Field(
        default_factory=list,
        description="Optional starting edges as [r1, c1, r2, c2] 0-based adjacent dot coordinates.",
    )


class BattleshipShip(BaseModel):
    name: str = Field(..., min_length=2, max_length=28)
    length: int = Field(..., ge=2, le=6)
    count: int = Field(default=1, ge=1, le=4)


class BattleshipSpec(BaseGameSpec):
    game_type: Literal["battleship"] = "battleship"
    include_answer_key: bool = Field(default=False)
    grid_size: int = Field(default=10, ge=6, le=12, description="Square coordinate grid dimension (classic is 10x10).")
    fleet: list[BattleshipShip] = Field(
        default_factory=lambda: [
            BattleshipShip(name="Carrier", length=5, count=1),
            BattleshipShip(name="Battleship", length=4, count=1),
            BattleshipShip(name="Cruiser", length=3, count=1),
            BattleshipShip(name="Submarine", length=3, count=1),
            BattleshipShip(name="Destroyer", length=2, count=1),
        ],
        min_length=2,
        max_length=8,
        description="Fleet roster with ship names, segment lengths, and counts.",
    )
    sheets_per_page: Literal[1, 2] = Field(
        default=1,
        description="1 = spacious single-player command sheet; 2 = two cuttable player sheets side-by-side (great in landscape!).",
    )
    theme_flavor: str = Field(
        default="Naval Command",
        max_length=50,
        description="Flavor header (e.g., 'Naval Command', 'Galactic Armada', 'Pirate Cove').",
    )
    defense_grid_label: str = Field(default="MY FLEET (Defense Grid)", max_length=40)
    target_grid_label: str = Field(default="ENEMY WATERS (Target Grid)", max_length=40)
    salvo_mode: bool = Field(
        default=False,
        description="Include optional Salvo variant rule reminder (fire 1 shot per surviving ship).",
    )


class CategoriesSpec(BaseGameSpec):
    game_type: Literal["categories"] = "categories"
    include_answer_key: bool = Field(default=False)
    categories: list[str] = Field(
        ...,
        min_length=8,
        max_length=18,
        description="8 to 18 curated Scattergories-style categories.",
    )
    rounds: int = Field(default=4, ge=2, le=6, description="Number of round columns on the sheet.")
    round_letters: list[str] | None = Field(
        default=None,
        description="Optional pre-filled letters for each round (leave omitted for blank letter-roll boxes).",
    )
    timer_minutes: int | None = Field(default=3, ge=1, le=10, description="Suggested round timer in minutes.")
    scoring_rules: str = Field(
        default="Unique answer = 1 pt · Alliterative bonus = +1 pt · Duplicate = 0 pts",
        max_length=160,
        description="Scoring summary displayed in footer/ribbon.",
    )
    sheets_per_page: Literal[1, 2] = Field(
        default=1,
        description="1 full-page sheet or 2 identical cuttable half-sheets side-by-side.",
    )

    @model_validator(mode="after")
    def _validate_letters(self) -> CategoriesSpec:
        if self.round_letters is not None and len(self.round_letters) != self.rounds:
            raise ValueError(
                f"round_letters must have exactly {self.rounds} items to match rounds."
            )
        return self


class HangmanRound(BaseModel):
    category: str = Field(..., min_length=2, max_length=40, description="Category hint shown to the guesser.")
    secret_word: str = Field(
        ...,
        min_length=3,
        max_length=28,
        description="Secret word or short phrase (blanks appear on player sheet; word appears only on Host Key).",
    )


class HangmanSpec(BaseGameSpec):
    game_type: Literal["hangman"] = "hangman"
    include_answer_key: bool = Field(
        default=False,
        description="Automatically forced True when pre_filled_puzzles are supplied (generates Host Secret Key).",
    )
    games_per_page: Literal[1, 2, 4] = Field(
        default=2,
        description="Number of Hangman game boards on the page (1, 2, or 4).",
    )
    visual_style: Literal["classic_gallows", "snowman", "flower", "rocket"] = Field(
        default="classic_gallows",
        description="Drawing theme: classic_gallows, or family-friendly snowman / flower / rocket.",
    )
    max_wrong_guesses: int = Field(
        default=6,
        ge=5,
        le=10,
        description="Number of body/stage parts before the round ends (6 is classic).",
    )
    show_alphabet_bank: bool = Field(
        default=True,
        description="Include an A-Z letter cross-off tracker on every board.",
    )
    pre_filled_puzzles: list[HangmanRound] | None = Field(
        default=None,
        description="Optional host-prepared rounds; blanks match secret words and a Host Key page is generated.",
    )

    @model_validator(mode="after")
    def _validate_rounds(self) -> HangmanSpec:
        if self.pre_filled_puzzles is not None:
            if len(self.pre_filled_puzzles) != self.games_per_page:
                raise ValueError(
                    f"pre_filled_puzzles count ({len(self.pre_filled_puzzles)}) must match games_per_page ({self.games_per_page})."
                )
            self.include_answer_key = True
        return self


class MadLibsSpec(BaseGameSpec):
    game_type: Literal["mad_libs"] = "mad_libs"
    include_answer_key: bool = Field(default=False)
    story_title: str = Field(..., min_length=2, max_length=80, description="Title of the Mad Libs story itself.")
    story_template: str = Field(
        ...,
        min_length=80,
        max_length=2600,
        description=(
            "Funny story prose containing 6 to 28 typed blanks using double braces: "
            "{{ADJECTIVE}}, {{PLURAL NOUN}}, or with an optional hint {{VERB ENDING IN -ING|something silly}}. "
            "Use blank lines (\\n\\n) for paragraphs."
        ),
    )
    include_word_collector_sheet: bool = Field(
        default=True,
        description=(
            "If true, Page 1 is a spoiler-free Word Collector prompt list and Page 2 is the full Story sheet! "
            "If false, prints as a single spacious fill-in story page."
        ),
    )
    illustration_icon: str | None = Field(
        default=None,
        description="Optional themed decorative icon from library for the story header.",
    )
    show_grammar_guide: bool = Field(
        default=True,
        description="Include a quick parts-of-speech mini reference box (Noun, Verb, Adjective, Adverb, Exclamation).",
    )

    @model_validator(mode="after")
    def _validate_template(self) -> MadLibsSpec:
        matches = re.findall(r"\{\{([^{}]+)\}\}", self.story_template)
        if not (6 <= len(matches) <= 28):
            raise ValueError(
                f"story_template must contain between 6 and 28 {{PART OF SPEECH}} blanks; found {len(matches)}."
            )
        if self.illustration_icon:
            key = self.illustration_icon.strip().lower().replace(" ", "_").replace("-", "_")
            if key not in ICONS:
                raise ValueError(f"Unknown illustration_icon '{self.illustration_icon}'.")
            self.illustration_icon = key
        return self


AnyGameSpec = (
    CryptogramSpec
    | WordLadderSpec
    | AnagramScrambleSpec
    | AcrosticSpec
    | BoggleWordWheelSpec
    | RebusSpec
    | MazeSpec
    | SpotTheDifferenceSpec
    | HiddenPicturesSpec
    | DotToDotSpec
    | ColorByNumberSpec
    | DotsAndBoxesSpec
    | BattleshipSpec
    | CategoriesSpec
    | HangmanSpec
    | MadLibsSpec
)


class BookletSpec(BaseModel):
    """Multi-game print-ready booklet with optional cover, TOC, and collated Answer Keys."""

    booklet_title: str = Field(..., min_length=2, max_length=90)
    subtitle: str | None = Field(default=None, max_length=120)
    author: str | None = Field(default=None, max_length=80)
    page_size: PageSizeName = Field(default="letter")
    orientation: Orientation = Field(default="portrait")
    margin_mm: float | None = Field(default=None, ge=4.0, le=40.0)
    custom_width_mm: float | None = Field(default=None, ge=80.0, le=600.0)
    custom_height_mm: float | None = Field(default=None, ge=80.0, le=600.0)
    theme: ThemeName = Field(default="editorial_classic")
    ink_saver: bool = Field(default=False)
    include_cover: bool = Field(default=True)
    include_toc: bool = Field(default=True)
    collate_answer_keys_at_end: bool = Field(
        default=True,
        description="Place all Answer Key pages together in a neat section at the back of the booklet.",
    )
    games: list[dict[str, Any]] = Field(
        ...,
        min_length=2,
        max_length=40,
        description="List of game specification dicts, each including 'game_type' and all required fields for that game.",
    )
    output_path: str | None = Field(default=None)
    output_format: OutputFormat = Field(default="pdf")
    render_preview_png: bool = Field(default=False)
