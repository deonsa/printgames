"""Category 1: Word & Letter Puzzles.

1. Cryptograms
2. Word Ladders
3. Anagrams & Word Scrambles
4. Acrostics
5. Boggle-Style Grids & Word Wheels
6. Rebus Puzzles
"""

from __future__ import annotations

import math
import random
import string
from collections import Counter
from html import escape

from ..core.pages import PageSpec
from ..core.renderer import RenderedPage
from ..core.scene_svg import render_scene_element
from ..core.themes import ThemeSpec
from ..models import (
    AcrosticSpec,
    AnagramScrambleSpec,
    BoggleWordWheelSpec,
    CryptogramSpec,
    RebusSpec,
    WordLadderSpec,
)

ALPHABET = list(string.ascii_uppercase)
_CIPHER_UPPER = str.maketrans(string.ascii_lowercase, string.ascii_uppercase)


# ---------------------------------------------------------------------------
# 1. CRYPTOGRAMS
# ---------------------------------------------------------------------------


def _build_derangement_cipher(seed: int, custom_map: dict[str, str] | None = None) -> dict[str, str]:
    if custom_map:
        normalized = {k.strip().upper(): v.strip().upper() for k, v in custom_map.items()}
        if len(normalized) == 26 and set(normalized.keys()) == set(ALPHABET) and set(normalized.values()) == set(ALPHABET):
            return normalized
    rng = random.Random(seed)
    letters = ALPHABET[:]
    for _ in range(200):
        shuffled = letters[:]
        rng.shuffle(shuffled)
        if all(a != b for a, b in zip(letters, shuffled)):
            return dict(zip(letters, shuffled))
    # Fallback cyclic shift
    return {a: ALPHABET[(i + 7) % 26] for i, a in enumerate(ALPHABET)}


def _cipher_tracker(
    counts: Counter[str], show_frequency: bool, label: str,
    s: float, theme: ThemeSpec, single_row: bool,
) -> str:
    cells = []
    for ch in ALPHABET:
        freq_sub = (
            f'<div style="font-size:{5.6 * s:.1f}pt;color:{theme.ink_muted};">{counts.get(ch, 0)}</div>'
            if show_frequency
            else ""
        )
        cells.append(
            f'<div style="flex:1;border:0.6pt solid {theme.border};border-radius:0.8mm;text-align:center;padding:{0.7 * s:.2f}mm 0;background:{theme.paper};">'
            f'<div style="font-family:{theme.font_mono};font-size:{7.4 * s:.1f}pt;font-weight:800;color:{theme.accent};">{ch}</div>'
            f'<div style="height:{4.4 * s:.2f}mm;border-top:0.5pt dotted {theme.border};margin-top:0.5mm;"></div>'
            f"{freq_sub}"
            f"</div>"
        )
    rows = [cells] if single_row else [cells[:13], cells[13:]]
    grid = "".join(f'<div style="display:flex;gap:{0.7 * s:.2f}mm;">{"".join(row)}</div>' for row in rows)
    label_extra = " & Letter Frequencies" if show_frequency else ""
    return (
        f'<div class="card-tinted" style="margin-top:auto;padding:{2.0 * s:.2f}mm {2.4 * s:.2f}mm;">'
        f'<div style="font-size:{7.0 * s:.1f}pt;font-weight:800;text-transform:uppercase;letter-spacing:0.06em;color:{theme.ink_muted};margin-bottom:1.2mm;">{label}{label_extra} (Top = Cipher · Bottom = Plaintext)</div>'
        f"{grid}"
        f"</div>"
    )


def render_cryptogram(spec: CryptogramSpec, page: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    s = page.scale
    count = len(spec.puzzles)
    dense = count >= 3 or page.is_compact
    cell_w = (5.4 if dense else 6.4) * s
    cell_h = (5.2 if dense else 6.2) * s
    font_c = (7.2 if dense else 8.2) * s
    font_h = (9.0 if dense else 10.5) * s
    row_gap = (2.8 if dense else 4.2) * s

    puzzle_blocks: list[str] = []
    answer_blocks: list[str] = []

    for idx, item in enumerate(spec.puzzles, start=1):
        cipher = _build_derangement_cipher(item.seed + idx * 31, item.custom_cipher_map)
        counts: Counter[str] = Counter()
        hints = set(item.hint_letters)
        plain_upper = item.plaintext.translate(_CIPHER_UPPER)

        words = plain_upper.split(" ")
        word_htmls: list[str] = []
        for word in words:
            chars_html: list[str] = []
            for ch in word:
                if ch in cipher:
                    c_ch = cipher[ch]
                    counts[c_ch] += 1
                    revealed = ch if ch in hints else ""
                    rev_style = f"color:{theme.accent};font-weight:800;" if revealed else ""
                    chars_html.append(
                        f'<span style="display:inline-flex;flex-direction:column;align-items:center;width:{cell_w:.2f}mm;margin:0 {0.45 * s:.2f}mm;">'
                        f'<span style="width:100%;height:{cell_h:.2f}mm;border-bottom:1.1pt solid {theme.ink};display:flex;align-items:flex-end;justify-content:center;font-family:{theme.font_mono};font-size:{font_h:.1f}pt;line-height:1.1;{rev_style}">{escape(revealed)}</span>'
                        f'<span style="font-family:{theme.font_mono};font-size:{font_c:.1f}pt;font-weight:700;color:{theme.ink_muted};margin-top:{0.5 * s:.2f}mm;">{c_ch}</span>'
                        f"</span>"
                    )
                else:
                    chars_html.append(
                        f'<span style="display:inline-flex;flex-direction:column;align-items:center;padding:0 {0.4 * s:.2f}mm;">'
                        f'<span style="height:{cell_h:.2f}mm;display:flex;align-items:flex-end;font-size:{font_h:.1f}pt;font-weight:700;">{escape(ch)}</span>'
                        f'<span style="font-size:{font_c:.1f}pt;opacity:0;">.</span>'
                        f"</span>"
                    )
            word_htmls.append(
                f'<span style="display:inline-flex;align-items:flex-end;margin-right:{3.6 * s:.2f}mm;margin-bottom:{row_gap:.2f}mm;">{"".join(chars_html)}</span>'
            )

        attr_html = ""
        if item.attribution:
            if item.encrypt_attribution:
                attr_chars = []
                for ch in item.attribution.translate(_CIPHER_UPPER):
                    if ch in cipher:
                        c_ch = cipher[ch]
                        counts[c_ch] += 1
                        revealed = ch if ch in hints else ""
                        attr_chars.append(
                            f'<span style="display:inline-flex;flex-direction:column;align-items:center;width:{cell_w * 0.85:.2f}mm;margin:0 {0.3 * s:.2f}mm;">'
                            f'<span style="width:100%;height:{cell_h * 0.85:.2f}mm;border-bottom:0.9pt solid {theme.ink_muted};display:flex;align-items:flex-end;justify-content:center;font-family:{theme.font_mono};font-size:{font_h * 0.85:.1f}pt;color:{theme.accent};font-weight:700;">{escape(revealed)}</span>'
                            f'<span style="font-family:{theme.font_mono};font-size:{font_c * 0.88:.1f}pt;color:{theme.ink_muted};">{c_ch}</span>'
                            f"</span>"
                        )
                    elif ch == " ":
                        attr_chars.append(f'<span style="display:inline-block;width:{2.6 * s:.2f}mm;"></span>')
                    else:
                        attr_chars.append(f'<span style="font-weight:700;padding:0 0.5mm;">{escape(ch)}</span>')
                attr_html = (
                    f'<div style="display:flex;align-items:center;justify-content:flex-end;flex-wrap:wrap;margin-top:{1.2 * s:.2f}mm;">'
                    f'<span style="margin-right:2mm;font-weight:700;color:{theme.accent};">—</span>{"".join(attr_chars)}</div>'
                )
            else:
                attr_html = f'<div style="text-align:right;font-style:italic;color:{theme.ink_muted};font-size:{8.5 * s:.1f}pt;margin-top:1.5mm;">— {escape(item.attribution)}</div>'

        header_bits = []
        if count > 1:
            header_bits.append(f'<span class="section-heading" style="margin:0;">Quote #{idx}</span>')
        if item.theme_clue:
            header_bits.append(
                f'<span style="font-size:{8.0 * s:.1f}pt;color:{theme.ink_muted};font-style:italic;">Clue: {escape(item.theme_clue)}</span>'
            )
        if hints:
            hint_pairs = ", ".join(f"{cipher[h]} = {h}" for h in sorted(hints))
            header_bits.append(
                f'<span class="pill pill-muted" style="font-size:{6.4 * s:.1f}pt;">Hint: {escape(hint_pairs)}</span>'
            )
        card_top = (
            f'<div style="display:flex;align-items:center;justify-content:space-between;gap:2mm;margin-bottom:{2.2 * s:.2f}mm;flex-wrap:wrap;">{"".join(header_bits)}</div>'
            if header_bits
            else ""
        )

        puzzle_blocks.append(
            f'<div class="card" style="padding:{3.0 * s:.2f}mm {3.6 * s:.2f}mm;margin-bottom:{2.6 * s:.2f}mm;">'
            f"{card_top}"
            f'<div style="display:flex;flex-wrap:wrap;align-items:flex-end;">{"".join(word_htmls)}</div>'
            f"{attr_html}"
            f"</div>"
        )

        if spec.show_alphabet_tracker:
            label = "Cipher Decoder Scratchpad" if count == 1 else f"Quote #{idx} Decoder Scratchpad"
            puzzle_blocks.append(_cipher_tracker(counts, spec.show_letter_frequency, label, s, theme, count > 1 and not page.is_compact))

        # Build answer key block
        used_plain = sorted(p for p in cipher if cipher[p] in counts)
        key_chips = "".join(
            f'<span style="display:inline-block;padding:0.4mm 1.4mm;margin:0.4mm;border:0.5pt solid {theme.border};border-radius:1mm;font-family:{theme.font_mono};font-size:{7.2 * s:.1f}pt;background:{theme.panel_bg};">'
            f'<b style="color:{theme.accent};">{cipher[p]}</b>→{p}</span>'
            for p in used_plain
        )
        answer_blocks.append(
            f'<div class="card" style="margin-bottom:{3 * s:.2f}mm;padding:{3 * s:.2f}mm {4 * s:.2f}mm;">'
            f'<div class="section-heading">Quote #{idx} Solution</div>'
            f'<p style="font-family:{theme.font_display};font-size:{11.5 * s:.1f}pt;margin:1mm 0 1.5mm;line-height:1.45;">“{escape(item.plaintext)}”</p>'
            + (
                f'<div style="text-align:right;font-style:italic;color:{theme.ink_muted};font-size:{8.8 * s:.1f}pt;margin-bottom:2mm;">— {escape(item.attribution)}</div>'
                if item.attribution
                else ""
            )
            + f'<div style="margin-top:1.5mm;padding-top:1.5mm;border-top:0.5pt dashed {theme.border};">{key_chips}</div>'
            f"</div>"
        )

    body = f'<div style="display:flex;flex-direction:column;flex:1;min-height:0;justify-content:space-between;"><div>{"".join(puzzle_blocks)}</div></div>'
    pages = [
        RenderedPage(
            title=spec.title,
            subtitle=spec.subtitle,
            category="Cryptogram",
            instructions=spec.instructions,
            difficulty=spec.difficulty,
            body_html=body,
            footer_left=spec.author_credit or "Word & Letter Puzzles · Cryptogram",
        )
    ]
    if spec.include_answer_key:
        pages.append(
            RenderedPage(
                title=f"{spec.title} — Solutions",
                category="Cryptogram",
                is_answer_key=True,
                body_html=f'<div>{"".join(answer_blocks)}</div>',
                footer_left=spec.author_credit or "Cryptogram Answer Key",
            )
        )
    return pages


# ---------------------------------------------------------------------------
# 2. WORD LADDERS
# ---------------------------------------------------------------------------


def _render_single_ladder(
    ladder,
    idx: int,
    show_solution: bool,
    cols_layout: int,
    page: PageSpec,
    theme: ThemeSpec,
) -> str:
    s = page.scale
    steps = ladder.solution_steps
    n_steps = len(steps)
    wlen = len(ladder.start_word)
    compact = cols_layout >= 2 or n_steps >= 8 or page.is_compact
    box_w = min(11.5 * s, (52.0 if cols_layout == 2 else 82.0) * s / max(wlen, 4))
    box_h = min(10.0 * s, (125.0 if cols_layout == 1 else 86.0) * s / max(n_steps, 5))
    box_h = max(6.2 * s, box_h)
    font_sz = max(9.0 * s, min(14.5 * s, box_h * 1.45))

    rows_html: list[str] = []
    for r_idx, word in enumerate(steps):
        is_start = r_idx == 0
        is_end = r_idx == n_steps - 1
        prev_word = steps[r_idx - 1] if r_idx > 0 else None

        tiles = []
        for c_idx, ch in enumerate(word):
            changed = prev_word is not None and prev_word[c_idx] != ch
            if is_start or is_end:
                bg = theme.accent
                fg = "#FFFFFF"
                border = theme.accent
                display_ch = ch
            elif show_solution:
                bg = theme.accent_soft if changed else theme.paper
                fg = theme.accent if changed else theme.ink
                border = theme.accent if changed else theme.border_strong
                display_ch = ch
            else:
                bg = theme.paper
                fg = theme.ink
                border = theme.border_strong
                display_ch = ""
            tiles.append(
                f'<div style="width:{box_w:.2f}mm;height:{box_h:.2f}mm;border:1.1pt solid {border};border-radius:1.4mm;'
                f'background:{bg};color:{fg};display:flex;align-items:center;justify-content:center;'
                f'font-family:{theme.font_mono};font-size:{font_sz:.1f}pt;font-weight:800;">{display_ch}</div>'
            )

        clue_text = ""
        if is_start:
            clue_text = f'<span style="font-size:{7.2 * s:.1f}pt;font-weight:800;color:{theme.accent};text-transform:uppercase;letter-spacing:0.06em;">Start</span>'
        elif is_end:
            clue_text = f'<span style="font-size:{7.2 * s:.1f}pt;font-weight:800;color:{theme.accent};text-transform:uppercase;letter-spacing:0.06em;">Goal</span>'
        elif ladder.step_clues:
            clue = ladder.step_clues[r_idx - 1]
            clue_text = f'<span style="font-size:{(7.4 if compact else 8.4) * s:.1f}pt;color:{theme.ink_muted};">{escape(clue)}</span>'
        else:
            clue_text = f'<span style="font-size:{7.0 * s:.1f}pt;color:{theme.ink_muted};">Step {r_idx}</span>'

        connector = ""
        if r_idx < n_steps - 1:
            connector = (
                f'<div style="display:flex;justify-content:center;width:{wlen * box_w + (wlen - 1) * 1.4 * s:.2f}mm;">'
                f'<div style="width:1.2pt;height:{(1.6 if compact else 2.2) * s:.2f}mm;background:{theme.border_strong};opacity:0.45;"></div>'
                f"</div>"
            )

        rows_html.append(
            f'<div style="display:flex;align-items:center;gap:{2.8 * s:.2f}mm;">'
            f'<div style="display:flex;gap:{1.4 * s:.2f}mm;flex:0 0 auto;">{"".join(tiles)}</div>'
            f'<div style="flex:1;line-height:1.2;">{clue_text}</div>'
            f"</div>{connector}"
        )

    heading = ladder.label or f"Ladder #{idx}: {ladder.start_word} → {ladder.end_word}"
    return (
        f'<div class="card" style="display:flex;flex-direction:column;padding:{2.6 * s:.2f}mm {3.2 * s:.2f}mm;min-height:0;">'
        f'<div class="section-heading" style="margin-bottom:{1.8 * s:.2f}mm;display:flex;justify-content:space-between;align-items:center;">'
        f'<span>{escape(heading)}</span>'
        f'<span style="font-size:{7.0 * s:.1f}pt;color:{theme.ink_muted};font-family:{theme.font_body};">{n_steps - 1} steps</span>'
        f"</div>"
        f'<div style="flex:1;display:flex;flex-direction:column;justify-content:center;">{"".join(rows_html)}</div>'
        f"</div>"
    )


def render_word_ladder(spec: WordLadderSpec, page: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    s = page.scale
    n = len(spec.ladders)
    cols = 1 if n == 1 else 2
    grid_rows = 1 if n <= 2 else 2

    def build_grid(show_solution: bool) -> str:
        cards = [
            _render_single_ladder(lad, i + 1, show_solution, cols, page, theme)
            for i, lad in enumerate(spec.ladders)
        ]
        return (
            f'<div style="flex:1;min-height:0;display:grid;'
            f'grid-template-columns:repeat({cols}, 1fr);'
            f'grid-template-rows:repeat({grid_rows}, 1fr);'
            f'gap:{3.5 * s:.2f}mm;">{"".join(cards)}</div>'
        )

    pages = [
        RenderedPage(
            title=spec.title,
            subtitle=spec.subtitle,
            category="Word Ladders",
            instructions=spec.instructions,
            difficulty=spec.difficulty,
            body_html=build_grid(False),
            footer_left=spec.author_credit or "Word & Letter Puzzles · Word Ladders",
        )
    ]
    if spec.include_answer_key:
        pages.append(
            RenderedPage(
                title=f"{spec.title} — Solutions",
                category="Word Ladders",
                is_answer_key=True,
                instructions="Highlighted tiles mark the single letter changed at each rung.",
                body_html=build_grid(True),
                footer_left=spec.author_credit or "Word Ladders Answer Key",
            )
        )
    return pages


# ---------------------------------------------------------------------------
# 3. ANAGRAMS & WORD SCRAMBLES
# ---------------------------------------------------------------------------


def _scramble_word(answer: str, seed: int) -> str:
    rng = random.Random(seed)
    parts = answer.split(" ")
    out_parts = []
    for part in parts:
        letters = [c for c in part if c.isalpha()]
        if len(letters) <= 1:
            out_parts.append(part)
            continue
        scrambled = letters[:]
        for _ in range(40):
            rng.shuffle(scrambled)
            if "".join(scrambled) != "".join(letters):
                break
        if "".join(scrambled) == "".join(letters):
            scrambled = scrambled[1:] + scrambled[:1]
        out_parts.append("".join(scrambled))
    return " ".join(out_parts)


def render_anagram_scramble(
    spec: AnagramScrambleSpec, page: PageSpec, theme: ThemeSpec
) -> list[RenderedPage]:
    s = page.scale
    n = len(spec.items)
    two_col = n >= 7
    compact = n >= 12 or page.is_compact
    box_size = (5.4 if compact else 6.6) * s
    tile_font = (8.8 if compact else 10.4) * s

    def build_items(show_solution: bool) -> str:
        cards = []
        for idx, item in enumerate(spec.items, start=1):
            scrambled_text = (
                item.scrambled.upper()
                if item.scrambled
                else _scramble_word(item.answer, spec.seed + idx * 17)
            )
            circled = set(item.circled_indices)

            # Answer letter boxes
            boxes = []
            letter_pos = 0
            for ch in item.answer:
                if ch == " ":
                    boxes.append(f'<span style="display:inline-block;width:{2.4 * s:.2f}mm;"></span>')
                elif ch.isalpha():
                    is_circled = letter_pos in circled
                    radius = "50%" if is_circled else "1.1mm"
                    border_col = theme.accent if is_circled else theme.border_strong
                    bg = theme.accent_soft if is_circled else theme.paper
                    val = ch if show_solution else ""
                    boxes.append(
                        f'<span style="display:inline-flex;align-items:center;justify-content:center;'
                        f'width:{box_size:.2f}mm;height:{box_size:.2f}mm;border:{1.2 if is_circled else 0.9}pt solid {border_col};'
                        f'border-radius:{radius};background:{bg};font-family:{theme.font_mono};'
                        f'font-size:{tile_font * 0.92:.1f}pt;font-weight:800;color:{theme.accent if show_solution and is_circled else theme.ink};">{val}</span>'
                    )
                    letter_pos += 1
                else:
                    boxes.append(f'<span style="font-weight:700;padding:0 0.4mm;">{escape(ch)}</span>')

            # Scrambled letter tiles
            sc_tiles = "".join(
                (
                    f'<span style="display:inline-block;width:{2.2 * s:.2f}mm;"></span>'
                    if ch == " "
                    else f'<span style="display:inline-flex;align-items:center;justify-content:center;'
                    f'min-width:{box_size * 0.88:.2f}mm;height:{box_size * 0.88:.2f}mm;padding:0 0.6mm;'
                    f'background:{theme.panel_bg};border:0.7pt solid {theme.border};border-radius:1mm;'
                    f'font-family:{theme.font_mono};font-size:{tile_font * 0.88:.1f}pt;font-weight:800;color:{theme.accent};">{escape(ch)}</span>'
                )
                for ch in scrambled_text
            )
            clue_html = (
                f'<div style="font-size:{7.4 * s:.1f}pt;color:{theme.ink_muted};font-style:italic;margin-top:0.6mm;">{escape(item.clue)}</div>'
                if item.clue
                else ""
            )

            cards.append(
                f'<div class="card" style="padding:{(1.6 if compact else 2.2) * s:.2f}mm {2.5 * s:.2f}mm;display:flex;flex-direction:column;justify-content:center;gap:{1.1 * s:.2f}mm;">'
                f'<div style="display:flex;align-items:center;gap:1.8mm;flex-wrap:wrap;">'
                f'<span style="font-weight:800;font-size:{8.2 * s:.1f}pt;color:{theme.ink_muted};min-width:{4.2 * s:.1f}mm;">{idx}.</span>'
                f'<div style="display:flex;gap:{0.7 * s:.2f}mm;flex-wrap:wrap;">{sc_tiles}</div>'
                f"</div>"
                f"{clue_html}"
                f'<div style="display:flex;gap:{0.8 * s:.2f}mm;flex-wrap:wrap;padding-left:{5.5 * s:.1f}mm;">{"".join(boxes)}</div>'
                f"</div>"
            )

        grid = (
            f'<div style="display:grid;grid-template-columns:repeat({2 if two_col else 1}, 1fr);'
            f'gap:{(1.8 if compact else 2.6) * s:.2f}mm;flex:1;min-height:0;align-content:start;">{"".join(cards)}</div>'
        )

        extras = []
        if spec.bonus_phrase:
            bp = spec.bonus_phrase
            bp_boxes = []
            for ch in bp.answer.upper():
                if ch == " ":
                    bp_boxes.append(f'<span style="display:inline-block;width:{4.2 * s:.2f}mm;"></span>')
                elif ch.isalpha():
                    val = ch if show_solution else ""
                    bp_boxes.append(
                        f'<span style="display:inline-flex;align-items:center;justify-content:center;'
                        f'width:{box_size * 1.12:.2f}mm;height:{box_size * 1.12:.2f}mm;border:1.3pt solid {theme.accent};'
                        f'border-radius:50%;background:{theme.paper};font-family:{theme.font_mono};'
                        f'font-size:{tile_font:.1f}pt;font-weight:800;color:{theme.accent};">{val}</span>'
                    )
                else:
                    bp_boxes.append(f'<span style="font-weight:800;font-size:{tile_font:.1f}pt;padding:0 0.5mm;">{escape(ch)}</span>')
            extras.append(
                f'<div class="card-tinted" style="margin-top:{2.4 * s:.2f}mm;border:1.2pt solid {theme.accent};padding:{2.4 * s:.2f}mm {3.4 * s:.2f}mm;text-align:center;">'
                f'<div class="section-heading" style="margin-bottom:1mm;">★ Bonus Final Riddle</div>'
                f'<div style="font-size:{8.8 * s:.1f}pt;margin-bottom:{1.8 * s:.2f}mm;">{escape(bp.prompt)}</div>'
                f'<div style="display:flex;justify-content:center;gap:{1.0 * s:.2f}mm;flex-wrap:wrap;">{"".join(bp_boxes)}</div>'
                f"</div>"
            )

        if spec.show_word_bank and not show_solution:
            rng = random.Random(spec.seed + 999)
            bank = [it.answer for it in spec.items]
            rng.shuffle(bank)
            chips = "".join(
                f'<span style="padding:0.5mm 2.2mm;border:0.6pt solid {theme.border};border-radius:999px;background:{theme.paper};font-size:{7.8 * s:.1f}pt;font-weight:700;">{escape(w)}</span>'
                for w in bank
            )
            extras.append(
                f'<div class="card-tinted" style="margin-top:{2.0 * s:.2f}mm;padding:{1.8 * s:.2f}mm {2.6 * s:.2f}mm;">'
                f'<div style="font-size:{7.0 * s:.1f}pt;font-weight:800;text-transform:uppercase;color:{theme.accent};margin-bottom:1mm;">Word Bank</div>'
                f'<div style="display:flex;flex-wrap:wrap;gap:1.4mm;">{chips}</div>'
                f"</div>"
            )

        return f'<div style="display:flex;flex-direction:column;flex:1;min-height:0;">{grid}{"".join(extras)}</div>'

    pages = [
        RenderedPage(
            title=spec.title,
            subtitle=spec.subtitle,
            category="Anagrams & Scrambles",
            instructions=spec.instructions,
            difficulty=spec.difficulty,
            body_html=build_items(False),
            footer_left=spec.author_credit or "Word & Letter Puzzles · Anagrams & Scrambles",
        )
    ]
    if spec.include_answer_key:
        pages.append(
            RenderedPage(
                title=f"{spec.title} — Solutions",
                category="Anagrams & Scrambles",
                is_answer_key=True,
                body_html=build_items(True),
                footer_left=spec.author_credit or "Anagrams & Scrambles Answer Key",
            )
        )
    return pages


# ---------------------------------------------------------------------------
# 4. ACROSTICS
# ---------------------------------------------------------------------------


def _build_acrostic_mapping(spec: AcrosticSpec):
    """Assign each quote letter position (1..N) uniquely to a clue answer letter."""
    rng = random.Random(spec.seed)
    # Build tokens of the quote (letters + word breaks)
    quote_slots: list[dict] = []
    letter_positions_by_char: dict[str, list[int]] = {}
    num = 0
    for ch in spec.quote.upper():
        if ch.isalpha():
            num += 1
            quote_slots.append({"type": "letter", "num": num, "char": ch, "clue_label": ""})
            letter_positions_by_char.setdefault(ch, []).append(len(quote_slots) - 1)
        elif ch == " ":
            if quote_slots and quote_slots[-1]["type"] != "space":
                quote_slots.append({"type": "space"})
        else:
            # Attach punctuation to previous letter cell if possible
            if quote_slots and quote_slots[-1]["type"] == "letter":
                quote_slots[-1]["punct"] = quote_slots[-1].get("punct", "") + ch

    for positions in letter_positions_by_char.values():
        rng.shuffle(positions)

    clue_assignments: list[list[int]] = []
    for clue in spec.clues:
        nums_for_clue: list[int] = []
        for ch in clue.answer:
            slot_idx = letter_positions_by_char[ch].pop()
            quote_slots[slot_idx]["clue_label"] = clue.label.upper()
            nums_for_clue.append(quote_slots[slot_idx]["num"])
        clue_assignments.append(nums_for_clue)

    return quote_slots, clue_assignments


def render_acrostic(spec: AcrosticSpec, page: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    s = page.scale
    quote_slots, clue_assignments = _build_acrostic_mapping(spec)
    total_cells = len(quote_slots)
    # Choose columns to fit nicely across page width
    usable_w = page.content_width_mm - 12 * s
    cols = 18 if page.is_compact else 23
    if total_cells > 115:
        cols = 26 if not page.is_compact else 20
    if total_cells < 65:
        cols = min(cols, 19)
    cell_sz = min(8.2 * s, usable_w / cols)
    n_clues = len(spec.clues)
    clue_font = (7.2 if n_clues > 14 else 8.0) * s
    blank_w = (4.0 if n_clues > 14 else 4.7) * s

    def build_page_body(show_solution: bool) -> str:
        # Top quote grid
        grid_cells = []
        for slot in quote_slots:
            if slot["type"] == "space":
                grid_cells.append(
                    f'<div style="width:{cell_sz:.2f}mm;height:{cell_sz:.2f}mm;background:{theme.border_strong};border:0.5pt solid {theme.border_strong};"></div>'
                )
            else:
                val = slot["char"] if show_solution else ""
                punct = slot.get("punct", "")
                grid_cells.append(
                    f'<div style="width:{cell_sz:.2f}mm;height:{cell_sz:.2f}mm;border:0.6pt solid {theme.border_strong};'
                    f'background:{theme.paper};position:relative;display:flex;align-items:flex-end;justify-content:center;padding-bottom:0.4mm;">'
                    f'<span style="position:absolute;top:0.3mm;left:0.5mm;font-size:{max(4.6, cell_sz * 0.72):.1f}pt;line-height:1;color:{theme.ink_muted};font-family:{theme.font_mono};">{slot["num"]}</span>'
                    f'<span style="position:absolute;top:0.3mm;right:0.5mm;font-size:{max(4.6, cell_sz * 0.72):.1f}pt;line-height:1;font-weight:800;color:{theme.accent};">{escape(slot["clue_label"])}</span>'
                    f'<span style="font-family:{theme.font_mono};font-size:{max(7.2, cell_sz * 1.25):.1f}pt;font-weight:800;color:{theme.ink};line-height:1;">{val}{escape(punct) if show_solution else ""}</span>'
                    f"</div>"
                )
        # Pad final row with black squares
        rem = len(grid_cells) % cols
        if rem:
            for _ in range(cols - rem):
                grid_cells.append(
                    f'<div style="width:{cell_sz:.2f}mm;height:{cell_sz:.2f}mm;background:{theme.border_strong};border:0.5pt solid {theme.border_strong};"></div>'
                )

        grid_html = (
            f'<div style="display:grid;grid-template-columns:repeat({cols}, {cell_sz:.2f}mm);'
            f'justify-content:center;border:1pt solid {theme.border_strong};width:fit-content;margin:0 auto {2.8 * s:.2f}mm;">'
            f'{"".join(grid_cells)}</div>'
        )

        # Clues in 2 columns
        clue_cards = []
        for clue, nums in zip(spec.clues, clue_assignments):
            blanks = []
            for idx_c, (n_val, ans_ch) in enumerate(zip(nums, clue.answer)):
                first_style = (
                    f"background:{theme.accent_soft};border-bottom:1.4pt solid {theme.accent};"
                    if idx_c == 0 and spec.require_first_letters_spell_author
                    else f"border-bottom:0.9pt solid {theme.ink};"
                )
                blanks.append(
                    f'<span style="display:inline-flex;flex-direction:column;align-items:center;width:{blank_w:.2f}mm;margin-right:0.6mm;">'
                    f'<span style="width:100%;height:{3.8 * s:.2f}mm;{first_style}display:flex;align-items:flex-end;justify-content:center;font-family:{theme.font_mono};font-size:{clue_font * 1.08:.1f}pt;font-weight:800;color:{theme.accent if show_solution else theme.ink};">{ans_ch if show_solution else ""}</span>'
                    f'<span style="font-size:{5.2 * s:.1f}pt;color:{theme.ink_muted};font-family:{theme.font_mono};">{n_val}</span>'
                    f"</span>"
                )
            clue_cards.append(
                f'<div style="break-inside:avoid;margin-bottom:{1.4 * s:.2f}mm;">'
                f'<div style="font-size:{clue_font:.1f}pt;line-height:1.2;margin-bottom:0.6mm;">'
                f'<b style="color:{theme.accent};">{escape(clue.label.upper())}.</b> {escape(clue.clue)}'
                f"</div>"
                f'<div style="display:flex;flex-wrap:wrap;">{"".join(blanks)}</div>'
                f"</div>"
            )

        author_banner = ""
        if show_solution:
            author_banner = (
                f'<div class="card-tinted" style="margin-bottom:{2.2 * s:.2f}mm;text-align:center;font-size:{9.0 * s:.1f}pt;">'
                f'<b>Quote:</b> “{escape(spec.quote)}” — <i>{escape(spec.author_and_source)}</i>'
                f"</div>"
            )

        clues_html = (
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:{1.0 * s:.2f}mm {4.2 * s:.2f}mm;flex:1;min-height:0;align-content:start;">'
            f'{"".join(clue_cards)}</div>'
        )
        return f'<div style="display:flex;flex-direction:column;flex:1;min-height:0;">{author_banner}{grid_html}{clues_html}</div>'

    pages = [
        RenderedPage(
            title=spec.title,
            subtitle=spec.subtitle,
            category="Acrostic",
            instructions=spec.instructions,
            difficulty=spec.difficulty,
            body_html=build_page_body(False),
            footer_left=spec.author_credit or "Word & Letter Puzzles · Acrostic",
        )
    ]
    if spec.include_answer_key:
        pages.append(
            RenderedPage(
                title=f"{spec.title} — Solution",
                category="Acrostic",
                is_answer_key=True,
                body_html=build_page_body(True),
                footer_left=spec.author_credit or "Acrostic Answer Key",
            )
        )
    return pages


# ---------------------------------------------------------------------------
# 5. BOGGLE-STYLE GRIDS & WORD WHEELS
# ---------------------------------------------------------------------------


def _render_boggle_svg(grid: list[list[str]], theme: ThemeSpec) -> str:
    n = len(grid)
    pad = 18
    gap = 10
    cell = 66 if n == 4 else 54
    size = pad * 2 + n * cell + (n - 1) * gap
    parts = [
        f'<rect x="4" y="4" width="{size - 8}" height="{size - 8}" rx="18" fill="{theme.border_strong}"/>',
        f'<rect x="10" y="10" width="{size - 20}" height="{size - 20}" rx="14" fill="{theme.panel_bg}"/>',
    ]
    for r in range(n):
        for c in range(n):
            x = pad + c * (cell + gap)
            y = pad + r * (cell + gap)
            letter = str(grid[r][c]).strip()
            if letter.upper() == "QU":
                letter = "Qu"
            else:
                letter = letter.upper()
            fsize = 30 if len(letter) == 1 else 23
            parts.append(
                f'<rect x="{x + 2}" y="{y + 3}" width="{cell}" height="{cell}" rx="11" fill="{theme.border}" opacity="0.65"/>'
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="11" fill="#FFFFFF" stroke="{theme.border_strong}" stroke-width="2"/>'
                f'<circle cx="{x + cell / 2:.1f}" cy="{y + cell / 2:.1f}" r="{cell * 0.41:.1f}" fill="{theme.panel_bg}" stroke="{theme.border}" stroke-width="0.9"/>'
                f'<text x="{x + cell / 2:.1f}" y="{y + cell / 2 + 1:.1f}" text-anchor="middle" dominant-baseline="central" '
                f'font-size="{fsize}" font-weight="800" fill="{theme.ink}" style="font-family:{theme.font_display};">{escape(letter)}</text>'
            )
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" style="width:100%;height:100%;max-height:100%;">{"".join(parts)}</svg>'


def _render_word_wheel_svg(center: str, outer: list[str], theme: ThemeSpec) -> str:
    size = 320
    cx = cy = size / 2
    r_outer = 144
    r_inner = 52
    n = len(outer)
    parts = [
        f'<circle cx="{cx}" cy="{cy}" r="{r_outer + 6}" fill="{theme.panel_bg}" stroke="{theme.border_strong}" stroke-width="2.5"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{r_outer}" fill="#FFFFFF" stroke="{theme.border_strong}" stroke-width="2"/>',
    ]
    for i, letter in enumerate(outer):
        a0 = -math.pi / 2 + (2 * math.pi * i) / n - math.pi / n
        a1 = a0 + (2 * math.pi) / n
        amid = (a0 + a1) / 2
        # Alternating subtle petal tint
        if i % 2 == 0:
            x0o, y0o = cx + r_outer * math.cos(a0), cy + r_outer * math.sin(a0)
            x1o, y1o = cx + r_outer * math.cos(a1), cy + r_outer * math.sin(a1)
            x1i, y1i = cx + r_inner * math.cos(a1), cy + r_inner * math.sin(a1)
            x0i, y0i = cx + r_inner * math.cos(a0), cy + r_inner * math.sin(a0)
            parts.append(
                f'<path d="M {x0i:.2f} {y0i:.2f} L {x0o:.2f} {y0o:.2f} A {r_outer} {r_outer} 0 0 1 {x1o:.2f} {y1o:.2f} '
                f'L {x1i:.2f} {y1i:.2f} A {r_inner} {r_inner} 0 0 0 {x0i:.2f} {y0i:.2f} Z" fill="{theme.panel_bg}"/>'
            )
        # Spoke line
        sx0, sy0 = cx + r_inner * math.cos(a0), cy + r_inner * math.sin(a0)
        sx1, sy1 = cx + r_outer * math.cos(a0), cy + r_outer * math.sin(a0)
        parts.append(
            f'<line x1="{sx0:.2f}" y1="{sy0:.2f}" x2="{sx1:.2f}" y2="{sy1:.2f}" stroke="{theme.border_strong}" stroke-width="1.8"/>'
        )
        # Outer letter
        r_text = (r_inner + r_outer) / 2
        tx, ty = cx + r_text * math.cos(amid), cy + r_text * math.sin(amid)
        parts.append(
            f'<text x="{tx:.2f}" y="{ty:.2f}" text-anchor="middle" dominant-baseline="central" '
            f'font-size="32" font-weight="800" fill="{theme.ink}" style="font-family:{theme.font_display};">{escape(letter)}</text>'
        )

    # Center hub
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r_inner}" fill="{theme.accent}" stroke="{theme.border_strong}" stroke-width="2.5"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r_inner - 6}" fill="none" stroke="#FFFFFF" stroke-width="1" stroke-dasharray="3 3" opacity="0.7"/>'
        f'<text x="{cx}" y="{cy + 1}" text-anchor="middle" dominant-baseline="central" '
        f'font-size="40" font-weight="900" fill="#FFFFFF" style="font-family:{theme.font_display};">{escape(center)}</text>'
    )
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" style="width:100%;height:100%;max-height:100%;">{"".join(parts)}</svg>'


def render_boggle_word_wheel(
    spec: BoggleWordWheelSpec, page: PageSpec, theme: ThemeSpec
) -> list[RenderedPage]:
    s = page.scale
    is_wheel = spec.mode == "word_wheel"
    board_svg = (
        _render_word_wheel_svg(spec.center_letter or "A", spec.outer_letters or [], theme)
        if is_wheel
        else _render_boggle_svg(spec.grid or [], theme)
    )

    goals_html = "".join(
        f'<div style="flex:1;text-align:center;padding:{1.2 * s:.2f}mm;border:0.7pt solid {theme.border};border-radius:1.4mm;background:{theme.paper};">'
        f'<div style="font-size:{6.8 * s:.1f}pt;text-transform:uppercase;letter-spacing:0.06em;color:{theme.ink_muted};font-weight:700;">{escape(k)}</div>'
        f'<div style="font-size:{11 * s:.1f}pt;font-weight:800;color:{theme.accent};">{v}+</div>'
        f"</div>"
        for k, v in spec.target_goals.items()
    )

    scoring_html = ""
    if spec.scoring_table:
        rows = "".join(
            f'<span style="font-size:{7.6 * s:.1f}pt;padding:0.5mm 1.8mm;border:0.5pt solid {theme.border};border-radius:1mm;background:{theme.paper};"><b>{escape(k)} letters:</b> {escape(v)}</span>'
            for k, v in spec.scoring_table.items()
        )
        scoring_html = f'<div style="display:flex;flex-wrap:wrap;gap:1.2mm;margin-top:1.8mm;justify-content:center;">{rows}</div>'

    cols = 3
    per_col = math.ceil(spec.writing_lines / cols)
    col_htmls = []
    idx_counter = 1
    for _ in range(cols):
        lines = []
        for _ in range(per_col):
            if idx_counter > spec.writing_lines:
                break
            lines.append(
                f'<div style="display:flex;align-items:flex-end;gap:1.4mm;height:{(5.6 if per_col > 13 else 6.6) * s:.2f}mm;">'
                f'<span style="font-size:{6.6 * s:.1f}pt;color:{theme.ink_muted};min-width:{4.2 * s:.1f}mm;font-family:{theme.font_mono};">{idx_counter}.</span>'
                f'<span style="flex:1;border-bottom:0.7pt solid {theme.border_strong};height:100%;"></span>'
                f"</div>"
            )
            idx_counter += 1
        col_htmls.append(f'<div style="flex:1;">{"".join(lines)}</div>')

    top_h = (64 if page.orientation == "portrait" else 56) * s
    body = f"""
<div style="display:flex;flex-direction:column;flex:1;min-height:0;gap:{2.8 * s:.2f}mm;">
  <div style="display:flex;align-items:center;gap:{5 * s:.2f}mm;flex:0 0 auto;">
    <div style="width:{top_h:.1f}mm;height:{top_h:.1f}mm;flex:0 0 auto;">{board_svg}</div>
    <div style="flex:1;display:flex;flex-direction:column;gap:{2.0 * s:.2f}mm;">
      <div class="card-tinted">
        <div class="section-heading" style="margin-bottom:1.2mm;">Word Goals</div>
        <div style="display:flex;gap:{1.8 * s:.2f}mm;">{goals_html}</div>
        {scoring_html}
      </div>
      <div class="card" style="display:flex;justify-content:space-between;align-items:center;font-size:{8.2 * s:.1f}pt;">
        <span><b>Min length:</b> {spec.min_word_length} letters{" · Must use <b>" + escape(spec.center_letter or "") + "</b>" if is_wheel else ""}</span>
        <span><b>Total Found:</b> <span style="display:inline-block;width:{12 * s:.1f}mm;border-bottom:0.9pt solid {theme.ink};"></span></span>
      </div>
    </div>
  </div>
  <div class="card" style="flex:1;min-height:0;display:flex;flex-direction:column;padding:{2.4 * s:.2f}mm {3.2 * s:.2f}mm;">
    <div class="section-heading" style="margin-bottom:1.2mm;">Your Discovered Words</div>
    <div style="display:flex;gap:{4.0 * s:.2f}mm;flex:1;min-height:0;">{"".join(col_htmls)}</div>
  </div>
</div>"""

    extra_badges = [f"Timer: {spec.timer_suggestion}"] if spec.timer_suggestion else None
    cat = "Word Wheel" if is_wheel else "Boggle Grid"
    pages = [
        RenderedPage(
            title=spec.title,
            subtitle=spec.subtitle,
            category=cat,
            instructions=spec.instructions,
            difficulty=spec.difficulty,
            extra_badges=extra_badges,
            body_html=body,
            footer_left=spec.author_credit or f"Word & Letter Puzzles · {cat}",
        )
    ]
    if spec.include_answer_key:
        sorted_words = sorted({w.strip().upper() for w in spec.sample_words}, key=lambda x: (-len(x), x))
        chips = "".join(
            f'<span style="padding:0.8mm 2.4mm;border:0.7pt solid {theme.border};border-radius:1.2mm;background:{theme.paper};font-family:{theme.font_mono};font-size:{8.6 * s:.1f}pt;font-weight:700;">{escape(w)}</span>'
            for w in sorted_words
        )
        pangram_box = ""
        if spec.pangram_word:
            pangram_box = (
                f'<div class="card-tinted" style="border:1.2pt solid {theme.accent};text-align:center;margin-bottom:{3 * s:.2f}mm;">'
                f'<div class="section-heading" style="margin-bottom:0.8mm;">★ Full-Wheel Bonus Word</div>'
                f'<div style="font-family:{theme.font_mono};font-size:{14 * s:.1f}pt;font-weight:900;letter-spacing:0.14em;color:{theme.accent};">{escape(spec.pangram_word.upper())}</div>'
                f"</div>"
            )
        ans_body = (
            f"{pangram_box}"
            f'<div class="card"><div class="section-heading">Sample Valid Words ({len(sorted_words)})</div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:1.8mm;margin-top:2mm;">{chips}</div></div>'
        )
        pages.append(
            RenderedPage(
                title=f"{spec.title} — Word List",
                category=cat,
                is_answer_key=True,
                body_html=ans_body,
                footer_left=spec.author_credit or f"{cat} Answer Key",
            )
        )
    return pages


# ---------------------------------------------------------------------------
# 6. REBUS PUZZLES
# ---------------------------------------------------------------------------


def render_rebus(spec: RebusSpec, page: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    s = page.scale
    n = len(spec.puzzles)
    if spec.columns:
        cols = spec.columns
    elif n <= 4:
        cols = 2
    elif n <= 6:
        cols = 2 if page.orientation == "portrait" else 3
    else:
        cols = 3
    rows = math.ceil(n / cols)

    cards = []
    answer_rows = []
    for idx, card in enumerate(spec.puzzles, start=1):
        svg_elements = "".join(render_scene_element(el, default_ink=theme.ink) for el in card.elements)
        card_svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 150" '
            f'preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;display:block;">'
            f'<rect x="1" y="1" width="238" height="148" rx="8" fill="{theme.paper}" stroke="{theme.border}" stroke-width="1.2"/>'
            f"{svg_elements}</svg>"
        )
        hint_html = (
            f'<div style="font-size:{6.8 * s:.1f}pt;color:{theme.ink_muted};font-style:italic;text-align:center;">Hint: {escape(card.hint)}</div>'
            if card.hint
            else ""
        )
        cards.append(
            f'<div class="card" style="display:flex;flex-direction:column;padding:{1.8 * s:.2f}mm;min-height:0;position:relative;">'
            f'<span style="position:absolute;top:{2.2 * s:.2f}mm;left:{2.4 * s:.2f}mm;width:{5.2 * s:.2f}mm;height:{5.2 * s:.2f}mm;'
            f'border-radius:50%;background:{theme.accent};color:#FFFFFF;font-size:{7.2 * s:.1f}pt;font-weight:800;'
            f'display:flex;align-items:center;justify-content:center;z-index:2;">{idx}</span>'
            f'<div style="flex:1;min-height:0;overflow:hidden;">{card_svg}</div>'
            f"{hint_html}"
            f'<div style="margin-top:{1.4 * s:.2f}mm;height:{4.6 * s:.2f}mm;border-bottom:0.9pt solid {theme.border_strong};"></div>'
            f"</div>"
        )

        expl = f' <span style="color:{theme.ink_muted};font-style:italic;">— {escape(card.explanation)}</span>' if card.explanation else ""
        answer_rows.append(
            f'<div class="card" style="display:flex;align-items:baseline;gap:2.5mm;padding:{2.0 * s:.2f}mm {3.0 * s:.2f}mm;">'
            f'<span style="width:{5.6 * s:.2f}mm;height:{5.6 * s:.2f}mm;border-radius:50%;background:{theme.accent};color:#FFFFFF;'
            f'font-size:{7.6 * s:.1f}pt;font-weight:800;display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;">{idx}</span>'
            f'<div style="font-size:{9.4 * s:.1f}pt;"><b>{escape(card.answer)}</b>{expl}</div>'
            f"</div>"
        )

    body = (
        f'<div style="flex:1;min-height:0;display:grid;'
        f'grid-template-columns:repeat({cols}, 1fr);'
        f'grid-template-rows:repeat({rows}, 1fr);'
        f'gap:{2.8 * s:.2f}mm;">{"".join(cards)}</div>'
    )
    pages = [
        RenderedPage(
            title=spec.title,
            subtitle=spec.subtitle,
            category="Rebus Puzzles",
            instructions=spec.instructions,
            difficulty=spec.difficulty,
            body_html=body,
            footer_left=spec.author_credit or "Word & Letter Puzzles · Rebus Puzzles",
        )
    ]
    if spec.include_answer_key:
        pages.append(
            RenderedPage(
                title=f"{spec.title} — Solutions",
                category="Rebus Puzzles",
                is_answer_key=True,
                body_html=f'<div style="display:flex;flex-direction:column;gap:{2.0 * s:.2f}mm;">{"".join(answer_rows)}</div>',
                footer_left=spec.author_credit or "Rebus Puzzles Answer Key",
            )
        )
    return pages
