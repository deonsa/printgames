"""Category 3: Multi-Player Pen & Paper Games.

12. Dots and Boxes
13. Battleship
14. Categories (Scattergories)
15. Hangman (Classic Gallows, Snowman, Flower, or Rocket)
16. Mad Libs (with optional spoiler-free Word Collector sheet)
"""

from __future__ import annotations

import re
import string
from html import escape

from ..core.icons import render_icon_svg
from ..core.pages import PageSpec
from ..core.renderer import RenderedPage
from ..core.themes import ThemeSpec
from ..models import (
    BattleshipSpec,
    CategoriesSpec,
    DotsAndBoxesSpec,
    HangmanSpec,
    MadLibsSpec,
)


# ---------------------------------------------------------------------------
# 12. DOTS AND BOXES
# ---------------------------------------------------------------------------


def _render_dots_board_svg(spec: DotsAndBoxesSpec, theme: ThemeSpec) -> str:
    rows, cols = spec.rows, spec.cols
    spacing = 32.0
    pad = 22.0
    w = pad * 2 + (cols - 1) * spacing
    h = pad * 2 + (rows - 1) * spacing
    parts: list[str] = []

    if spec.show_guide_lines:
        for r in range(rows):
            y = pad + r * spacing
            parts.append(
                f'<line x1="{pad:.1f}" y1="{y:.1f}" x2="{pad + (cols - 1) * spacing:.1f}" y2="{y:.1f}" '
                f'stroke="{theme.border}" stroke-width="0.9" stroke-dasharray="3 4"/>'
            )
        for c in range(cols):
            x = pad + c * spacing
            parts.append(
                f'<line x1="{x:.1f}" y1="{pad:.1f}" x2="{x:.1f}" y2="{pad + (rows - 1) * spacing:.1f}" '
                f'stroke="{theme.border}" stroke-width="0.9" stroke-dasharray="3 4"/>'
            )

    for edge in spec.pre_drawn_edges:
        if len(edge) == 4:
            r1, c1, r2, c2 = edge
            if 0 <= r1 < rows and 0 <= c1 < cols and 0 <= r2 < rows and 0 <= c2 < cols:
                parts.append(
                    f'<line x1="{pad + c1 * spacing:.1f}" y1="{pad + r1 * spacing:.1f}" '
                    f'x2="{pad + c2 * spacing:.1f}" y2="{pad + r2 * spacing:.1f}" '
                    f'stroke="{theme.accent}" stroke-width="3.2" stroke-linecap="round"/>'
                )

    for r in range(rows):
        for c in range(cols):
            cx = pad + c * spacing
            cy = pad + r * spacing
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.0" fill="{theme.ink}"/>')

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
        f'preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;display:block;">'
        f"{''.join(parts)}</svg>"
    )


def render_dots_and_boxes(
    spec: DotsAndBoxesSpec, page: PageSpec, theme: ThemeSpec
) -> list[RenderedPage]:
    s = page.scale
    labels = spec.player_labels or [f"Player {i + 1}" for i in range(spec.player_count)]
    labels = labels[: spec.player_count]

    def make_board_card(board_num: int) -> str:
        score_boxes = "".join(
            f'<div style="flex:1;display:flex;align-items:center;justify-content:space-between;padding:{1.0 * s:.2f}mm {2.0 * s:.2f}mm;'
            f'border:0.7pt solid {theme.border};border-radius:1.2mm;background:{theme.paper};font-size:{7.6 * s:.1f}pt;">'
            f'<span style="font-weight:700;color:{theme.ink};">{escape(lbl)}</span>'
            f'<span style="display:inline-block;width:{8 * s:.1f}mm;height:{4.4 * s:.1f}mm;border:0.7pt solid {theme.border_strong};border-radius:0.8mm;"></span>'
            f"</div>"
            for lbl in labels
        )
        header = (
            f'<div style="font-size:{7.2 * s:.1f}pt;font-weight:800;text-transform:uppercase;color:{theme.accent};margin-bottom:1mm;">Game #{board_num}</div>'
            if spec.boards_per_page > 1
            else ""
        )
        return (
            f'<div class="card" style="display:flex;flex-direction:column;min-height:0;min-width:0;padding:{2.0 * s:.2f}mm;">'
            f"{header}"
            f'<div style="display:flex;gap:{1.5 * s:.2f}mm;margin-bottom:{1.6 * s:.2f}mm;">{score_boxes}</div>'
            f'<div style="flex:1;min-height:0;display:flex;align-items:center;justify-content:center;">{_render_dots_board_svg(spec, theme)}</div>'
            f"</div>"
        )

    if spec.boards_per_page == 1:
        grid_style = "grid-template-columns:1fr;grid-template-rows:1fr;"
    elif spec.boards_per_page == 2:
        grid_style = (
            "grid-template-columns:1fr 1fr;grid-template-rows:1fr;"
            if page.orientation == "landscape"
            else "grid-template-columns:1fr;grid-template-rows:1fr 1fr;"
        )
    else:
        grid_style = "grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;"

    cards = "".join(make_board_card(i + 1) for i in range(spec.boards_per_page))
    body = f'<div style="flex:1;min-height:0;display:grid;{grid_style}gap:{2.8 * s:.2f}mm;">{cards}</div>'

    return [
        RenderedPage(
            title=spec.title,
            subtitle=spec.subtitle,
            category="Dots and Boxes",
            instructions=spec.instructions,
            difficulty=spec.difficulty,
            extra_badges=[f"{spec.rows}×{spec.cols} Dots", f"{spec.player_count} Players"],
            body_html=body,
            footer_left=spec.author_credit or "Multi-Player Pen & Paper · Dots and Boxes",
        )
    ]


# ---------------------------------------------------------------------------
# 13. BATTLESHIP
# ---------------------------------------------------------------------------


def _render_battleship_grid_svg(size: int, title: str, theme: ThemeSpec) -> str:
    cell = 24.0
    left = 26.0
    top = 28.0
    w = left + size * cell + 8
    h = top + size * cell + 8
    parts = [
        f'<rect x="{left}" y="{top}" width="{size * cell}" height="{size * cell}" fill="#FFFFFF" stroke="{theme.border_strong}" stroke-width="2"/>'
    ]
    for i in range(size):
        # Column header 1..N
        cx = left + (i + 0.5) * cell
        parts.append(
            f'<text x="{cx:.1f}" y="{top - 10:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'font-size="11" font-weight="800" fill="{theme.accent}">{i + 1}</text>'
        )
        # Row header A..J
        cy = top + (i + 0.5) * cell
        parts.append(
            f'<text x="{left - 12:.1f}" y="{cy:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'font-size="11" font-weight="800" fill="{theme.accent}">{chr(ord("A") + i)}</text>'
        )
        if i > 0:
            x = left + i * cell
            y = top + i * cell
            parts.append(
                f'<line x1="{x:.1f}" y1="{top:.1f}" x2="{x:.1f}" y2="{top + size * cell:.1f}" stroke="{theme.border}" stroke-width="0.9"/>'
                f'<line x1="{left:.1f}" y1="{y:.1f}" x2="{left + size * cell:.1f}" y2="{y:.1f}" stroke="{theme.border}" stroke-width="0.9"/>'
            )
    # Subtle water dots in cell centers
    for r in range(size):
        for c in range(size):
            parts.append(
                f'<circle cx="{left + (c + 0.5) * cell:.1f}" cy="{top + (r + 0.5) * cell:.1f}" r="1.1" fill="{theme.border}" opacity="0.7"/>'
            )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
        f'preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;display:block;">'
        f"{''.join(parts)}</svg>"
    )


def render_battleship(spec: BattleshipSpec, page: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    s = page.scale
    two_up = spec.sheets_per_page == 2

    def make_fleet_rows(compact: bool) -> str:
        rows = []
        for ship in spec.fleet:
            for copy_idx in range(ship.count):
                label = f"{ship.name} #{copy_idx + 1}" if ship.count > 1 else ship.name
                segs = "".join(
                    f'<span style="display:inline-block;width:{(3.0 if compact else 3.8) * s:.2f}mm;height:{(3.0 if compact else 3.8) * s:.2f}mm;'
                    f'border:0.9pt solid {theme.border_strong};background:{theme.paper};margin-right:0.6mm;border-radius:0.5mm;"></span>'
                    for _ in range(ship.length)
                )
                rows.append(
                    f'<div style="display:flex;align-items:center;justify-content:space-between;gap:1.5mm;font-size:{(6.8 if compact else 7.8) * s:.1f}pt;">'
                    f'<span style="font-weight:700;">{escape(label)} ({ship.length})</span>'
                    f'<span style="display:inline-flex;align-items:center;">{segs}</span>'
                    f"</div>"
                )
        return "".join(rows)

    def make_player_sheet(player_idx: int) -> str:
        grids_side = (page.orientation == "landscape" and not two_up)
        grid_dir = "row" if grids_side else "column"
        fleet_html = make_fleet_rows(two_up)
        salvo_note = (
            f' · <b>Salvo Mode:</b> Fire 1 shot per surviving ship.'
            if spec.salvo_mode
            else ""
        )
        return f"""
<div style="flex:1;min-height:0;min-width:0;display:flex;flex-direction:column;gap:{1.8 * s:.2f}mm;">
  <div style="display:flex;justify-content:space-between;align-items:center;padding:{1.0 * s:.2f}mm {2.0 * s:.2f}mm;background:{theme.panel_bg};border:0.7pt solid {theme.border};border-radius:1.4mm;font-size:{(7.2 if two_up else 8.2) * s:.1f}pt;">
    <span><b style="color:{theme.accent};">{escape(spec.theme_flavor)}</b>{f" · Sheet {player_idx}" if two_up else ""}</span>
    <span>Commander: <span style="display:inline-block;width:{(18 if two_up else 28) * s:.1f}mm;border-bottom:0.8pt solid {theme.ink};"></span></span>
  </div>
  <div style="flex:1;min-height:0;display:flex;flex-direction:{grid_dir};gap:{2.2 * s:.2f}mm;">
    <div class="card" style="flex:1;min-height:0;min-width:0;display:flex;flex-direction:column;padding:{1.5 * s:.2f}mm;">
      <div style="font-size:{(7.0 if two_up else 8.0) * s:.1f}pt;font-weight:800;color:{theme.accent};text-transform:uppercase;text-align:center;margin-bottom:0.6mm;">{escape(spec.target_grid_label)}</div>
      <div style="flex:1;min-height:0;">{_render_battleship_grid_svg(spec.grid_size, spec.target_grid_label, theme)}</div>
    </div>
    <div class="card" style="flex:1;min-height:0;min-width:0;display:flex;flex-direction:column;padding:{1.5 * s:.2f}mm;">
      <div style="font-size:{(7.0 if two_up else 8.0) * s:.1f}pt;font-weight:800;color:{theme.ink};text-transform:uppercase;text-align:center;margin-bottom:0.6mm;">{escape(spec.defense_grid_label)}</div>
      <div style="flex:1;min-height:0;">{_render_battleship_grid_svg(spec.grid_size, spec.defense_grid_label, theme)}</div>
    </div>
  </div>
  <div class="card-tinted" style="flex:0 0 auto;padding:{1.4 * s:.2f}mm {2.2 * s:.2f}mm;">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:{1.0 * s:.2f}mm {3.5 * s:.2f}mm;">{fleet_html}</div>
    <div style="margin-top:1.2mm;padding-top:1mm;border-top:0.5pt dotted {theme.border};font-size:{(6.4 if two_up else 7.2) * s:.1f}pt;color:{theme.ink_muted};text-align:center;">
      <b>Key:</b> Mark <b>X</b> = Hit · <b>•</b> = Miss · Cross off boxes as ships sink{salvo_note}
    </div>
  </div>
</div>"""

    if two_up:
        body = (
            f'<div style="flex:1;min-height:0;display:flex;gap:0;">'
            f"{make_player_sheet(1)}"
            f'<div class="cut-divider-v"></div>'
            f"{make_player_sheet(2)}</div>"
        )
    else:
        body = make_player_sheet(1)

    return [
        RenderedPage(
            title=spec.title,
            subtitle=spec.subtitle,
            category="Battleship",
            instructions=spec.instructions,
            difficulty=spec.difficulty,
            extra_badges=[f"{spec.grid_size}×{spec.grid_size} Grid", "2 Sheets (Cut)" if two_up else "Command Sheet"],
            body_html=body,
            footer_left=spec.author_credit or "Multi-Player Pen & Paper · Battleship",
        )
    ]


# ---------------------------------------------------------------------------
# 14. CATEGORIES (SCATTERGORIES)
# ---------------------------------------------------------------------------


def render_categories(spec: CategoriesSpec, page: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    s = page.scale
    two_up = spec.sheets_per_page == 2
    n_cats = len(spec.categories)
    rounds = spec.rounds
    row_font = (7.2 if two_up or n_cats >= 14 else 8.6) * s

    def make_sheet() -> str:
        round_headers = []
        for r in range(rounds):
            letter = spec.round_letters[r].upper() if spec.round_letters else ""
            round_headers.append(
                f'<th style="padding:{1.2 * s:.2f}mm;border:0.8pt solid {theme.border_strong};background:{theme.panel_bg};text-align:center;">'
                f'<div style="font-size:{6.2 * s:.1f}pt;text-transform:uppercase;color:{theme.ink_muted};">Round {r + 1}</div>'
                f'<div style="margin:0.8mm auto 0;width:{(5.4 if two_up else 7.2) * s:.1f}mm;height:{(5.4 if two_up else 7.2) * s:.1f}mm;'
                f'border:1.1pt solid {theme.accent};border-radius:1.2mm;background:#FFFFFF;display:flex;align-items:center;justify-content:center;'
                f'font-family:{theme.font_mono};font-size:{(9.0 if two_up else 11.0) * s:.1f}pt;font-weight:900;color:{theme.accent};">{escape(letter)}</div>'
                f"</th>"
            )

        body_rows = []
        for idx, cat in enumerate(spec.categories, start=1):
            bg = theme.panel_bg if idx % 2 == 0 else "#FFFFFF"
            cells = "".join(
                f'<td style="border:0.7pt solid {theme.border};background:{bg};"></td>'
                for _ in range(rounds)
            )
            body_rows.append(
                f"<tr>"
                f'<td style="border:0.7pt solid {theme.border_strong};background:{bg};padding:{0.8 * s:.2f}mm {1.6 * s:.2f}mm;font-size:{row_font:.1f}pt;font-weight:700;width:{(42 if two_up else 36)}%;">'
                f'<span style="color:{theme.accent};font-family:{theme.font_mono};margin-right:1.2mm;">{idx:02d}.</span>{escape(cat)}</td>'
                f"{cells}</tr>"
            )

        score_cells = "".join(
            f'<td style="border:0.9pt solid {theme.border_strong};background:{theme.accent_soft};height:{6.4 * s:.1f}mm;text-align:center;font-size:{6.8 * s:.1f}pt;color:{theme.ink_muted};">Pts</td>'
            for _ in range(rounds)
        )

        timer_str = f" · Timer: {spec.timer_minutes} min/round" if spec.timer_minutes else ""
        return f"""
<div style="flex:1;min-height:0;min-width:0;display:flex;flex-direction:column;gap:{1.8 * s:.2f}mm;">
  <div style="display:flex;justify-content:space-between;align-items:center;font-size:{(7.4 if two_up else 8.4) * s:.1f}pt;">
    <span><b>Player:</b> <span style="display:inline-block;width:{(24 if two_up else 44) * s:.1f}mm;border-bottom:0.9pt solid {theme.ink};"></span></span>
    <span style="color:{theme.ink_muted};"><b>Grand Total:</b> <span style="display:inline-block;width:{12 * s:.1f}mm;border-bottom:1.1pt solid {theme.accent};"></span></span>
  </div>
  <table style="width:100%;flex:1;border-collapse:collapse;table-layout:fixed;">
    <thead>
      <tr>
        <th style="padding:{1.4 * s:.2f}mm;border:0.8pt solid {theme.border_strong};background:{theme.accent};color:#FFFFFF;text-align:left;font-size:{(7.6 if two_up else 8.8) * s:.1f}pt;text-transform:uppercase;letter-spacing:0.05em;">Category</th>
        {''.join(round_headers)}
      </tr>
    </thead>
    <tbody>
      {''.join(body_rows)}
      <tr>
        <td style="border:0.9pt solid {theme.border_strong};background:{theme.accent_soft};padding:1.2mm 1.8mm;font-size:{row_font:.1f}pt;font-weight:900;color:{theme.accent};text-transform:uppercase;">Round Score</td>
        {score_cells}
      </tr>
    </tbody>
  </table>
  <div style="font-size:{(6.4 if two_up else 7.4) * s:.1f}pt;color:{theme.ink_muted};text-align:center;">
    {escape(spec.scoring_rules)}{escape(timer_str)}
  </div>
</div>"""

    if two_up:
        body = (
            f'<div style="flex:1;min-height:0;display:flex;">'
            f"{make_sheet()}<div class=\"cut-divider-v\"></div>{make_sheet()}</div>"
        )
    else:
        body = make_sheet()

    return [
        RenderedPage(
            title=spec.title,
            subtitle=spec.subtitle,
            category="Categories (Scattergories)",
            instructions=spec.instructions,
            difficulty=spec.difficulty,
            extra_badges=[f"{n_cats} Categories", f"{rounds} Rounds"],
            body_html=body,
            footer_left=spec.author_credit or "Multi-Player Pen & Paper · Categories",
        )
    ]


# ---------------------------------------------------------------------------
# 15. HANGMAN
# ---------------------------------------------------------------------------


def _render_hangman_canvas_svg(style: str, max_wrong: int, theme: ThemeSpec) -> str:
    if style == "snowman":
        base = (
            f'<line x1="20" y1="150" x2="150" y2="150" stroke="{theme.border_strong}" stroke-width="2.2" stroke-linecap="round"/>'
            f'<circle cx="85" cy="122" r="26" fill="none" stroke="{theme.border}" stroke-width="1.4" stroke-dasharray="4 4"/>'
            f'<circle cx="85" cy="84" r="19" fill="none" stroke="{theme.border}" stroke-width="1.4" stroke-dasharray="4 4"/>'
            f'<circle cx="85" cy="54" r="13" fill="none" stroke="{theme.border}" stroke-width="1.4" stroke-dasharray="4 4"/>'
        )
        legend = "1. Base · 2. Torso · 3. Head · 4. Arms · 5. Hat · 6. Face"
    elif style == "flower":
        base = (
            f'<path d="M55 150h60l-8-26H63z" fill="{theme.panel_bg}" stroke="{theme.border_strong}" stroke-width="2"/>'
            f'<line x1="85" y1="124" x2="85" y2="74" stroke="{theme.border_strong}" stroke-width="2.2"/>'
            f'<circle cx="85" cy="64" r="11" fill="{theme.accent_soft}" stroke="{theme.accent}" stroke-width="1.8"/>'
        )
        legend = "Draw 1 petal or leaf per wrong guess!"
    elif style == "rocket":
        base = (
            f'<line x1="25" y1="150" x2="145" y2="150" stroke="{theme.border_strong}" stroke-width="2.4"/>'
            f'<rect x="65" y="136" width="40" height="14" rx="2" fill="{theme.panel_bg}" stroke="{theme.border_strong}" stroke-width="1.8"/>'
            f'<path d="M85 32c14 14 20 34 20 68H65c0-34 6-54 20-68z" fill="none" stroke="{theme.border}" stroke-width="1.3" stroke-dasharray="4 4"/>'
        )
        legend = "1. Body · 2. Nose · 3. Window · 4-5. Fins · 6. Flame"
    else:
        base = (
            f'<path d="M26 148h64M46 148V24h62v18" fill="none" stroke="{theme.border_strong}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<line x1="46" y1="44" x2="66" y2="24" stroke="{theme.border_strong}" stroke-width="2.4"/>'
            f'<circle cx="108" cy="54" r="12" fill="none" stroke="{theme.border}" stroke-width="1.2" stroke-dasharray="3 3"/>'
        )
        legend = "1. Head · 2. Body · 3-4. Arms · 5-6. Legs"

    checks = "".join(
        f'<rect x="{18 + i * 21}" y="158" width="13" height="13" rx="2" fill="#FFFFFF" stroke="{theme.border_strong}" stroke-width="1.1"/>'
        f'<text x="{24.5 + i * 21}" y="164.8" text-anchor="middle" dominant-baseline="central" font-size="8" font-weight="700" fill="{theme.ink_muted}">{i + 1}</text>'
        for i in range(min(max_wrong, 7))
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 170 184" preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;display:block;">'
        f'<rect x="1" y="1" width="168" height="182" rx="8" fill="#FFFFFF" stroke="{theme.border}" stroke-width="1.2"/>'
        f"{base}{checks}"
        f'<text x="85" y="179" text-anchor="middle" font-size="6.4" fill="{theme.ink_muted}">{escape(legend)}</text>'
        f"</svg>"
    )


def render_hangman(spec: HangmanSpec, page: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    s = page.scale
    n = spec.games_per_page
    compact = n == 4

    def make_board(idx: int) -> str:
        round_data = spec.pre_filled_puzzles[idx] if spec.pre_filled_puzzles else None
        cat_text = (
            f'<b>Category:</b> {escape(round_data.category)}'
            if round_data
            else f'<b>Category:</b> <span style="display:inline-block;width:{(22 if compact else 34) * s:.1f}mm;border-bottom:0.8pt solid {theme.ink};"></span>'
        )

        # Secret word blanks (grouped by word so words never split awkwardly mid-word)
        if round_data:
            word_groups = []
            for word in round_data.secret_word.upper().split(" "):
                if not word:
                    continue
                letters = []
                for ch in word:
                    if ch.isalpha():
                        letters.append(
                            f'<span style="display:inline-block;width:{(3.8 if compact else 5.2) * s:.1f}mm;height:{(4.8 if compact else 6.4) * s:.1f}mm;border-bottom:1.4pt solid {theme.ink};margin:0 0.5mm;"></span>'
                        )
                    else:
                        letters.append(f'<span style="font-weight:800;padding:0 0.5mm;">{escape(ch)}</span>')
                word_groups.append(
                    f'<span style="display:inline-flex;align-items:flex-end;white-space:nowrap;">{"".join(letters)}</span>'
                )
            word_area = (
                f'<div style="display:flex;flex-wrap:wrap;justify-content:center;align-items:flex-end;'
                f'gap:{(2.2 if compact else 3.2) * s:.1f}mm {(3.6 if compact else 5.4) * s:.1f}mm;">{"".join(word_groups)}</div>'
            )
        else:
            blank_count = 10 if compact else 14
            blanks = "".join(
                f'<span style="display:inline-block;width:{(4.4 if compact else 6.0) * s:.1f}mm;height:{(5.4 if compact else 7.0) * s:.1f}mm;border-bottom:1.1pt dashed {theme.border_strong};margin:0 0.7mm;"></span>'
                for _ in range(blank_count)
            )
            word_area = (
                f'<div style="font-size:{6.6 * s:.1f}pt;text-transform:uppercase;color:{theme.ink_muted};text-align:center;margin-bottom:1mm;">Secret Word / Phrase</div>'
                f'<div style="display:flex;flex-wrap:wrap;justify-content:center;">{blanks}</div>'
            )

        alpha_html = ""
        if spec.show_alphabet_bank:
            chips = "".join(
                f'<span style="display:inline-flex;align-items:center;justify-content:center;'
                f'width:{(4.6 if compact else 6.0) * s:.1f}mm;height:{(4.6 if compact else 5.8) * s:.1f}mm;'
                f'border:0.6pt solid {theme.border};border-radius:0.9mm;background:#FFFFFF;'
                f'font-family:{theme.font_mono};font-size:{(7.2 if compact else 8.8) * s:.1f}pt;font-weight:800;">{ch}</span>'
                for ch in string.ascii_uppercase
            )
            alpha_html = (
                f'<div style="margin-top:auto;">'
                f'<div style="font-size:{6.4 * s:.1f}pt;font-weight:800;text-transform:uppercase;color:{theme.ink_muted};margin-bottom:0.8mm;">Letter Bank (Cross Off Guesses)</div>'
                f'<div style="display:flex;flex-wrap:wrap;gap:{(0.7 if compact else 1.0) * s:.2f}mm;">{chips}</div>'
                f"</div>"
            )

        canvas_w = (30 if compact else (54 if n == 1 else 42)) * s
        return f"""
<div class="card" style="display:flex;flex-direction:column;min-height:0;min-width:0;padding:{(1.8 if compact else 2.8) * s:.2f}mm;gap:{1.8 * s:.2f}mm;">
  <div style="display:flex;justify-content:space-between;align-items:center;font-size:{(7.4 if compact else 8.6) * s:.1f}pt;border-bottom:0.6pt solid {theme.border};padding-bottom:1mm;">
    <span class="section-heading" style="margin:0;font-size:{(8.4 if compact else 10.2) * s:.1f}pt;">Round #{idx + 1}</span>
    <span>{cat_text}</span>
  </div>
  <div style="flex:1;min-height:0;display:flex;gap:{2.8 * s:.2f}mm;">
    <div style="width:{canvas_w:.1f}mm;flex:0 0 auto;min-height:0;">{_render_hangman_canvas_svg(spec.visual_style, spec.max_wrong_guesses, theme)}</div>
    <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:{2.2 * s:.2f}mm;">
      <div class="card-tinted" style="padding:{(1.6 if compact else 2.6) * s:.2f}mm;">{word_area}</div>
      {alpha_html}
    </div>
  </div>
</div>"""

    if n == 1:
        grid = "grid-template-columns:1fr;grid-template-rows:1fr;"
    elif n == 2:
        grid = (
            "grid-template-columns:1fr 1fr;grid-template-rows:1fr;"
            if page.orientation == "landscape"
            else "grid-template-columns:1fr;grid-template-rows:1fr 1fr;"
        )
    else:
        grid = "grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;"

    boards = "".join(make_board(i) for i in range(n))
    pages = [
        RenderedPage(
            title=spec.title,
            subtitle=spec.subtitle,
            category="Hangman",
            instructions=spec.instructions,
            difficulty=spec.difficulty,
            extra_badges=[f"{n} Round{'s' if n > 1 else ''}", f"{spec.max_wrong_guesses} Guesses"],
            body_html=f'<div style="flex:1;min-height:0;display:grid;{grid}gap:{2.6 * s:.2f}mm;">{boards}</div>',
            footer_left=spec.author_credit or "Multi-Player Pen & Paper · Hangman",
        )
    ]

    if spec.pre_filled_puzzles:
        rows = "".join(
            f'<div class="card" style="display:flex;justify-content:space-between;align-items:center;padding:{2.6 * s:.2f}mm {3.6 * s:.2f}mm;">'
            f'<div><b style="color:{theme.accent};">Round #{i + 1}</b> · <span style="color:{theme.ink_muted};">{escape(r.category)}</span></div>'
            f'<div style="font-family:{theme.font_mono};font-size:{12 * s:.1f}pt;font-weight:900;letter-spacing:0.08em;">{escape(r.secret_word.upper())}</div>'
            f"</div>"
            for i, r in enumerate(spec.pre_filled_puzzles)
        )
        pages.append(
            RenderedPage(
                title=f"{spec.title} — Host Secret Key",
                category="Hangman",
                is_answer_key=True,
                instructions="Keep this page hidden from guessers! Use it to verify letters for each pre-filled round.",
                body_html=f'<div style="display:flex;flex-direction:column;gap:{2.2 * s:.2f}mm;">{rows}</div>',
                footer_left=spec.author_credit or "Hangman Host Key",
            )
        )
    return pages


# ---------------------------------------------------------------------------
# 16. MAD LIBS
# ---------------------------------------------------------------------------


def _parse_mad_libs(template: str) -> tuple[list[dict], list[dict]]:
    """Parse paragraphs and extract numbered {{PART OF SPEECH|optional hint}} blanks."""
    blanks: list[dict] = []
    paragraphs: list[dict] = []
    pattern = re.compile(r"\{\{([^{}]+)\}\}")

    for para_raw in re.split(r"\n\s*\n", template.strip()):
        tokens: list[dict] = []
        pos = 0
        for m in pattern.finditer(para_raw):
            if m.start() > pos:
                tokens.append({"type": "text", "text": para_raw[pos : m.start()]})
            raw_spec = m.group(1).strip()
            if "|" in raw_spec:
                pos_label, hint = [p.strip() for p in raw_spec.split("|", 1)]
            else:
                pos_label, hint = raw_spec, None
            num = len(blanks) + 1
            blank = {"number": num, "pos": pos_label.upper(), "hint": hint}
            blanks.append(blank)
            tokens.append({"type": "blank", **blank})
            pos = m.end()
        if pos < len(para_raw):
            tokens.append({"type": "text", "text": para_raw[pos:]})
        paragraphs.append({"tokens": tokens})
    return paragraphs, blanks


def render_mad_libs(spec: MadLibsSpec, page: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    s = page.scale
    paragraphs, blanks = _parse_mad_libs(spec.story_template)
    n_blanks = len(blanks)
    story_len = len(spec.story_template)
    dense = story_len > 1100 or n_blanks > 18 or page.is_compact
    story_font = (9.6 if dense else 11.0) * s
    line_h = 2.45 if dense else 2.75
    blank_w = (23.0 if dense else 28.0) * s

    grammar_box = ""
    if spec.show_grammar_guide:
        grammar_box = (
            f'<div class="card-tinted" style="flex:0 0 auto;padding:{1.5 * s:.2f}mm {2.4 * s:.2f}mm;font-size:{7.3 * s:.1f}pt;line-height:1.35;">'
            f'<b style="color:{theme.accent};text-transform:uppercase;letter-spacing:0.05em;">Quick Grammar Guide:</b> '
            f"<b>Noun</b> (person/place/thing: <i>penguin</i>) · "
            f"<b>Verb</b> (action: <i>juggle</i>) · "
            f"<b>Adjective</b> (describes: <i>sparkly</i>) · "
            f"<b>Adverb</b> (how: <i>loudly</i>) · "
            f"<b>Exclamation</b> (<i>Zoinks!</i>)"
            f"</div>"
        )

    pages: list[RenderedPage] = []

    # Optional Page 1: Spoiler-Free Word Collector Sheet
    if spec.include_word_collector_sheet:
        cols = 2 if n_blanks > 10 else 1
        rows_html = []
        for b in blanks:
            hint_str = f' <span style="font-style:italic;color:{theme.ink_muted};font-weight:400;">({escape(b["hint"])})</span>' if b["hint"] else ""
            rows_html.append(
                f'<div style="display:flex;flex-direction:column;gap:0.8mm;padding:{(1.4 if n_blanks > 16 else 2.0) * s:.2f}mm {2.4 * s:.2f}mm;border:0.7pt solid {theme.border};border-radius:1.4mm;background:#FFFFFF;">'
                f'<div style="font-size:{7.6 * s:.1f}pt;font-weight:800;color:{theme.accent};">'
                f'<span style="font-family:{theme.font_mono};margin-right:1.2mm;">#{b["number"]:02d}</span>{escape(b["pos"])}{hint_str}</div>'
                f'<div style="height:{(4.6 if n_blanks > 16 else 5.8) * s:.1f}mm;border-bottom:1pt solid {theme.ink};"></div>'
                f"</div>"
            )
        collector_body = f"""
<div style="display:flex;flex-direction:column;flex:1;min-height:0;gap:{2.2 * s:.2f}mm;">
  <div style="display:grid;grid-template-columns:repeat({cols}, 1fr);gap:{(1.6 if n_blanks > 16 else 2.2) * s:.2f}mm;flex:1;min-height:0;align-content:start;">
    {''.join(rows_html)}
  </div>
  {grammar_box}
</div>"""
        pages.append(
            RenderedPage(
                title=f"{spec.title} — Word Collector",
                subtitle=f"Part 1 of 2 · Ask players for {n_blanks} words WITHOUT showing them the story!",
                category="Mad Libs",
                instructions="Ask another player for a word matching each part of speech below and write it on the line. When finished, transfer the numbered words onto the Story Sheet and read aloud!",
                difficulty=spec.difficulty,
                extra_badges=[f"{n_blanks} Blanks"],
                body_html=collector_body,
                footer_left=spec.author_credit or "Multi-Player Pen & Paper · Mad Libs (Word Collector)",
            )
        )

    # Story Sheet
    icon_html = (
        render_icon_svg(spec.illustration_icon, size=24 * s, stroke=theme.accent, stroke_width=1.8, standalone=True)
        if spec.illustration_icon
        else ""
    )
    para_htmls = []
    for p_idx, para in enumerate(paragraphs):
        pieces = []
        for tok in para["tokens"]:
            if tok["type"] == "text":
                pieces.append(escape(tok["text"]))
            else:
                hint_sub = f" ({tok['hint']})" if tok["hint"] and not spec.include_word_collector_sheet else ""
                pieces.append(
                    f'<span style="display:inline-block;position:relative;min-width:{blank_w:.1f}mm;'
                    f'border-bottom:1.1pt solid {theme.ink};margin:0 1.0mm;line-height:1.05;vertical-align:baseline;text-align:center;">'
                    f'&nbsp;'
                    f'<span style="position:absolute;left:0;right:0;top:100%;margin-top:0.6mm;font-size:{5.8 * s:.1f}pt;'
                    f'font-weight:800;line-height:1.05;color:{theme.accent};text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
                    f'({tok["number"]}) {escape(tok["pos"] + hint_sub)}</span>'
                    f"</span>"
                )
        para_htmls.append(
            f'<p style="margin:0 0 {(3.0 if dense else 4.2) * s:.2f}mm 0;font-family:{theme.font_display};font-size:{story_font:.1f}pt;line-height:{line_h:.2f};text-align:left;">'
            f'{"".join(pieces)}</p>'
        )

    story_body = f"""
<div style="display:flex;flex-direction:column;flex:1;min-height:0;gap:{2.2 * s:.2f}mm;">
  <div class="card" style="flex:1;min-height:0;padding:{3.5 * s:.2f}mm {4.6 * s:.2f}mm;overflow:hidden;">
    <div style="display:flex;align-items:center;justify-content:center;gap:2.5mm;margin-bottom:{3.0 * s:.2f}mm;padding-bottom:{1.8 * s:.2f}mm;border-bottom:0.9pt double {theme.border_strong};">
      {icon_html}
      <h2 style="margin:0;font-family:{theme.font_display};font-size:{14.5 * s:.1f}pt;color:{theme.accent};text-align:center;">{escape(spec.story_title)}</h2>
      {icon_html}
    </div>
    {''.join(para_htmls)}
  </div>
  {"" if spec.include_word_collector_sheet else grammar_box}
</div>"""

    pages.append(
        RenderedPage(
            title=spec.title,
            subtitle=("Part 2 of 2 · Transfer your numbered words and read aloud!" if spec.include_word_collector_sheet else spec.subtitle),
            category="Mad Libs",
            instructions=spec.instructions,
            difficulty=spec.difficulty,
            extra_badges=[f"{n_blanks} Blanks"],
            body_html=story_body,
            footer_left=spec.author_credit or "Multi-Player Pen & Paper · Mad Libs",
        )
    )
    return pages
