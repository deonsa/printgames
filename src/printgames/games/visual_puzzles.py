"""Category 2: Visual & Spatial Activities.

7. Mazes (Rectangular, Circular/Polar, and Hexagonal + guaranteed BFS solver)
8. Spot the Difference
9. Hidden Pictures (I Spy)
10. Dot-to-Dot (with automatic non-overlapping label placement)
11. Color-by-Number (with automatic region centroid label placement)
"""

from __future__ import annotations

import math
import random
from collections import deque
from html import escape

from ..core.icons import ICONS, render_icon_svg
from ..core.pages import PageSpec
from ..core.renderer import RenderedPage
from ..core.scene_svg import apply_spot_differences, render_scene_element
from ..core.themes import ThemeSpec
from ..models import (
    ColorByNumberSpec,
    DotToDotSpec,
    HiddenPicturesSpec,
    MazeSpec,
    SpotTheDifferenceSpec,
)


# ---------------------------------------------------------------------------
# 7. MAZES (Rectangular, Circular/Polar, Hexagonal)
# ---------------------------------------------------------------------------


def _carve_graph_maze(
    nodes: list,
    neighbors_fn,
    start,
    algorithm: str,
    braid_ratio: float,
    seed: int,
) -> dict:
    """Generic graph maze carver supporting Recursive Backtracker, Prim's, and Braid."""
    rng = random.Random(seed)
    adj: dict = {n: set() for n in nodes}
    visited = {start}

    if algorithm == "prims":
        frontier: list[tuple] = []
        for nb in neighbors_fn(start):
            frontier.append((start, nb))
        while frontier:
            idx = rng.randrange(len(frontier))
            u, v = frontier.pop(idx)
            if v in visited:
                continue
            visited.add(v)
            adj[u].add(v)
            adj[v].add(u)
            for nb in neighbors_fn(v):
                if nb not in visited:
                    frontier.append((v, nb))
    else:
        stack = [start]
        while stack:
            curr = stack[-1]
            unvisited = [nb for nb in neighbors_fn(curr) if nb not in visited]
            if unvisited:
                nxt = rng.choice(unvisited)
                visited.add(nxt)
                adj[curr].add(nxt)
                adj[nxt].add(curr)
                stack.append(nxt)
            else:
                stack.pop()

    if algorithm == "braid" and braid_ratio > 0:
        dead_ends = [n for n in nodes if len(adj[n]) == 1]
        rng.shuffle(dead_ends)
        for n in dead_ends:
            if len(adj[n]) == 1 and rng.random() < braid_ratio:
                cands = [nb for nb in neighbors_fn(n) if nb not in adj[n]]
                if cands:
                    pick = rng.choice(cands)
                    adj[n].add(pick)
                    adj[pick].add(n)
    return adj


def _solve_bfs(adj: dict, start, goal) -> list:
    q = deque([[start]])
    seen = {start}
    while q:
        path = q.popleft()
        curr = path[-1]
        if curr == goal:
            return path
        for nb in adj.get(curr, ()):
            if nb not in seen:
                seen.add(nb)
                q.append([*path, nb])
    return []


def _render_rectangular_maze_svg(spec: MazeSpec, theme: ThemeSpec, show_solution: bool) -> str:
    cols, rows = spec.cols, spec.rows
    nodes = [(r, c) for r in range(rows) for c in range(cols)]

    def neighbors(cell):
        r, c = cell
        out = []
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                out.append((nr, nc))
        return out

    start, goal = (0, 0), (rows - 1, cols - 1)
    adj = _carve_graph_maze(nodes, neighbors, start, spec.algorithm, spec.braid_ratio, spec.seed)
    sol = _solve_bfs(adj, start, goal) if show_solution else []

    cell = 24.0
    pad_x = 34.0
    pad_y = 42.0
    w = cols * cell + pad_x * 2
    h = rows * cell + pad_y * 2
    cap = "round" if spec.wall_style == "rounded" else "square"
    sw = max(1.8, min(3.2, 46.0 / max(cols, rows)))

    wall_lines: list[str] = []
    for r in range(rows):
        for c in range(cols):
            x = pad_x + c * cell
            y = pad_y + r * cell
            # Top wall (open at start)
            if r == 0 and c != 0:
                wall_lines.append(f"M{x:.1f},{y:.1f}H{x + cell:.1f}")
            elif r > 0 and (r - 1, c) not in adj[(r, c)]:
                wall_lines.append(f"M{x:.1f},{y:.1f}H{x + cell:.1f}")
            # Left wall
            if c == 0:
                wall_lines.append(f"M{x:.1f},{y:.1f}V{y + cell:.1f}")
            elif (r, c - 1) not in adj[(r, c)]:
                wall_lines.append(f"M{x:.1f},{y:.1f}V{y + cell:.1f}")
            # Bottom border (open at goal)
            if r == rows - 1 and c != cols - 1:
                wall_lines.append(f"M{x:.1f},{y + cell:.1f}H{x + cell:.1f}")
            # Right border
            if c == cols - 1:
                wall_lines.append(f"M{x + cell:.1f},{y:.1f}V{y + cell:.1f}")

    sol_svg = ""
    if sol:
        pts = [
            f"{pad_x + (c + 0.5) * cell:.1f},{pad_y + (r + 0.5) * cell:.1f}"
            for r, c in sol
        ]
        sol_svg = (
            f'<polyline points="{" ".join(pts)}" fill="none" stroke="{theme.answer_highlight}" '
            f'stroke-width="{max(2.6, cell * 0.24):.1f}" stroke-linecap="round" stroke-linejoin="round" opacity="0.82"/>'
        )

    sx, sy = pad_x + cell * 0.5, pad_y - 18
    ex, ey = pad_x + (cols - 0.5) * cell, pad_y + rows * cell + 20
    start_mark = (
        render_icon_svg(spec.start_icon, x=sx - 18, y=sy, size=18, stroke=theme.accent, stroke_width=2.0)
        if spec.start_icon
        else f'<polygon points="{sx:.1f},{pad_y - 4:.1f} {sx - 6:.1f},{pad_y - 13:.1f} {sx + 6:.1f},{pad_y - 13:.1f}" fill="{theme.accent}"/>'
    )
    end_mark = (
        render_icon_svg(spec.end_icon, x=ex + 18, y=ey, size=18, stroke=theme.accent, stroke_width=2.0)
        if spec.end_icon
        else f'<polygon points="{ex:.1f},{pad_y + rows * cell + 14:.1f} {ex - 6:.1f},{pad_y + rows * cell + 5:.1f} {ex + 6:.1f},{pad_y + rows * cell + 5:.1f}" fill="{theme.accent}"/>'
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
        f'preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;">'
        f'<rect x="{pad_x:.1f}" y="{pad_y:.1f}" width="{cols * cell:.1f}" height="{rows * cell:.1f}" fill="#FFFFFF"/>'
        f"{sol_svg}"
        f'<path d="{" ".join(wall_lines)}" fill="none" stroke="{theme.ink}" stroke-width="{sw:.2f}" stroke-linecap="{cap}"/>'
        f"{start_mark}"
        f'<text x="{sx + (4 if spec.start_icon else 12):.1f}" y="{sy:.1f}" text-anchor="start" dominant-baseline="central" font-size="13" font-weight="800" fill="{theme.accent}">{escape(spec.start_label)}</text>'
        f"{end_mark}"
        f'<text x="{ex - (4 if spec.end_icon else 12):.1f}" y="{ey:.1f}" text-anchor="end" dominant-baseline="central" font-size="13" font-weight="800" fill="{theme.accent}">{escape(spec.end_label)}</text>'
        f"</svg>"
    )


def _render_circular_maze_svg(spec: MazeSpec, theme: ThemeSpec, show_solution: bool) -> str:
    rings = spec.rings
    # Ring 0 is center hub (1 cell); outer rings double sector counts when arc grows
    ring_counts = [1]
    for r in range(1, rings):
        prev = ring_counts[-1]
        if r == 1:
            ring_counts.append(6)
        elif (2 * math.pi * r) / prev >= 1.9:
            ring_counts.append(prev * 2)
        else:
            ring_counts.append(prev)

    nodes = [(r, i) for r in range(rings) for i in range(ring_counts[r])]

    def neighbors(cell):
        r, i = cell
        out = []
        if r == 0:
            for j in range(ring_counts[1]):
                out.append((1, j))
            return out
        cnt = ring_counts[r]
        # CW / CCW
        out.append((r, (i - 1) % cnt))
        out.append((r, (i + 1) % cnt))
        # Inward
        prev_cnt = ring_counts[r - 1]
        ratio_in = cnt // prev_cnt
        out.append((r - 1, i // ratio_in))
        # Outward
        if r + 1 < rings:
            nxt_cnt = ring_counts[r + 1]
            ratio_out = nxt_cnt // cnt
            for k in range(ratio_out):
                out.append((r + 1, i * ratio_out + k))
        return out

    exit_cell = (rings - 1, 0)
    center_cell = (0, 0)
    adj = _carve_graph_maze(nodes, neighbors, center_cell, spec.algorithm, spec.braid_ratio, spec.seed)
    sol = _solve_bfs(adj, exit_cell, center_cell) if show_solution else []

    step = 24.0
    max_r = rings * step
    pad = 44.0
    size = (max_r + pad) * 2
    cx = cy = size / 2
    sw = max(1.8, min(3.0, 26.0 / rings))
    cap = "round" if spec.wall_style == "rounded" else "square"

    walls: list[str] = []
    for r in range(1, rings):
        cnt = ring_counts[r]
        r_in = r * step
        r_out = (r + 1) * step
        prev_cnt = ring_counts[r - 1]
        ratio_in = cnt // prev_cnt
        for i in range(cnt):
            a0 = -math.pi / 2 + (2 * math.pi * i) / cnt
            a1 = -math.pi / 2 + (2 * math.pi * (i + 1)) / cnt
            # Inward arc wall
            parent = (r - 1, i // ratio_in)
            if parent not in adj[(r, i)]:
                x0, y0 = cx + r_in * math.cos(a0), cy + r_in * math.sin(a0)
                x1, y1 = cx + r_in * math.cos(a1), cy + r_in * math.sin(a1)
                walls.append(f"M{x0:.2f},{y0:.2f} A{r_in:.2f},{r_in:.2f} 0 0 1 {x1:.2f},{y1:.2f}")
            # CCW radial wall
            ccw = (r, (i - 1) % cnt)
            if ccw not in adj[(r, i)]:
                x0, y0 = cx + r_in * math.cos(a0), cy + r_in * math.sin(a0)
                x1, y1 = cx + r_out * math.cos(a0), cy + r_out * math.sin(a0)
                walls.append(f"M{x0:.2f},{y0:.2f} L{x1:.2f},{y1:.2f}")
            # Outer boundary (open at exit_cell)
            if r == rings - 1 and (r, i) != exit_cell:
                x0, y0 = cx + r_out * math.cos(a0), cy + r_out * math.sin(a0)
                x1, y1 = cx + r_out * math.cos(a1), cy + r_out * math.sin(a1)
                walls.append(f"M{x0:.2f},{y0:.2f} A{r_out:.2f},{r_out:.2f} 0 0 1 {x1:.2f},{y1:.2f}")

    sol_svg = ""
    if sol:
        pts = []
        for r, i in sol:
            if r == 0:
                pts.append(f"{cx:.1f},{cy:.1f}")
            else:
                cnt = ring_counts[r]
                amid = -math.pi / 2 + (2 * math.pi * (i + 0.5)) / cnt
                rm = (r + 0.5) * step
                pts.append(f"{cx + rm * math.cos(amid):.1f},{cy + rm * math.sin(amid):.1f}")
        sol_svg = (
            f'<polyline points="{" ".join(pts)}" fill="none" stroke="{theme.answer_highlight}" '
            f'stroke-width="4.2" stroke-linecap="round" stroke-linejoin="round" opacity="0.82"/>'
        )

    a_entry = -math.pi / 2 + math.pi / ring_counts[rings - 1]
    sx = cx + (max_r + 22) * math.cos(a_entry)
    sy = cy + (max_r + 22) * math.sin(a_entry)
    center_mark = (
        render_icon_svg(spec.end_icon, x=cx, y=cy, size=step * 1.1, stroke=theme.accent, stroke_width=2.0)
        if spec.end_icon
        else f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" dominant-baseline="central" font-size="10" font-weight="800" fill="{theme.accent}">{escape(spec.end_label[:8])}</text>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size:.1f} {size:.1f}" '
        f'preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;">'
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{max_r:.1f}" fill="#FFFFFF"/>'
        f"{sol_svg}"
        f'<path d="{" ".join(walls)}" fill="none" stroke="{theme.ink}" stroke-width="{sw:.2f}" stroke-linecap="{cap}"/>'
        f"{center_mark}"
        f'<text x="{sx:.1f}" y="{sy:.1f}" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="800" fill="{theme.accent}">↓ {escape(spec.start_label)}</text>'
        f"</svg>"
    )


def _render_hex_maze_svg(spec: MazeSpec, theme: ThemeSpec, show_solution: bool) -> str:
    cols = min(spec.cols, 24)
    rows = min(spec.rows, 26)
    nodes = [(r, c) for r in range(rows) for c in range(cols)]

    # Flat-top odd-q hex coordinates
    def hex_dirs(c: int):
        if c % 2 == 0:
            return [(-1, 0), (-1, 1), (0, 1), (1, 0), (0, -1), (-1, -1)]
        return [(-1, 0), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]

    def neighbors(cell):
        r, c = cell
        out = []
        for dr, dc in hex_dirs(c):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                out.append((nr, nc))
        return out

    start, goal = (0, 0), (rows - 1, cols - 1)
    adj = _carve_graph_maze(nodes, neighbors, start, spec.algorithm, spec.braid_ratio, spec.seed)
    sol = _solve_bfs(adj, start, goal) if show_solution else []

    rad = 16.0
    dx = rad * 1.5
    dy = rad * math.sqrt(3)
    pad = 36.0
    w = pad * 2 + (cols - 1) * dx + rad * 2
    h = pad * 2 + rows * dy + dy * 0.5

    def center(r, c):
        cx = pad + rad + c * dx
        cy = pad + dy * 0.5 + r * dy + (dy * 0.5 if c % 2 == 1 else 0)
        return cx, cy

    def corners(cx, cy):
        return [
            (cx + rad * math.cos(math.radians(60 * k)), cy + rad * math.sin(math.radians(60 * k)))
            for k in range(6)
        ]

    # Map edge index (between corner k and k+1) to direction index in hex_dirs
    # Corner 0=0deg, 1=60deg, 2=120deg, 3=180deg, 4=240deg, 5=300deg
    # Midpoints: 0-1=30deg(SE), 1-2=90deg(S), 2-3=150deg(SW), 3-4=210deg(NW), 4-5=270deg(N), 5-0=330deg(NE)
    # hex_dirs order: 0:N, 1:NE, 2:SE, 3:S, 4:SW, 5:NW
    edge_to_dir = {4: 0, 5: 1, 0: 2, 1: 3, 2: 4, 3: 5}

    walls: list[str] = []
    for r in range(rows):
        for c in range(cols):
            cx, cy = center(r, c)
            pts = corners(cx, cy)
            dirs = hex_dirs(c)
            for edge_idx, dir_idx in edge_to_dir.items():
                dr, dc = dirs[dir_idx]
                nb = (r + dr, c + dc)
                # Leave north edge of start and south edge of goal open
                if (r, c) == start and dir_idx == 0:
                    continue
                if (r, c) == goal and dir_idx == 3:
                    continue
                if nb not in adj[(r, c)]:
                    p1 = pts[edge_idx]
                    p2 = pts[(edge_idx + 1) % 6]
                    walls.append(f"M{p1[0]:.1f},{p1[1]:.1f}L{p2[0]:.1f},{p2[1]:.1f}")

    sol_svg = ""
    if sol:
        pts = [f"{center(r, c)[0]:.1f},{center(r, c)[1]:.1f}" for r, c in sol]
        sol_svg = (
            f'<polyline points="{" ".join(pts)}" fill="none" stroke="{theme.answer_highlight}" '
            f'stroke-width="4.2" stroke-linecap="round" stroke-linejoin="round" opacity="0.82"/>'
        )
    scx, scy = center(*start)
    ecx, ecy = center(*goal)
    sw = max(1.6, min(2.6, 36.0 / max(cols, rows)))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
        f'preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;">'
        f"{sol_svg}"
        f'<path d="{" ".join(walls)}" fill="none" stroke="{theme.ink}" stroke-width="{sw:.2f}" stroke-linecap="round"/>'
        f'<text x="{scx:.1f}" y="{scy - dy * 0.8:.1f}" text-anchor="middle" font-size="12" font-weight="800" fill="{theme.accent}">↓ {escape(spec.start_label)}</text>'
        f'<text x="{ecx:.1f}" y="{ecy + dy * 0.95:.1f}" text-anchor="middle" font-size="12" font-weight="800" fill="{theme.accent}">★ {escape(spec.end_label)}</text>'
        f"</svg>"
    )


def render_maze(spec: MazeSpec, page: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    s = page.scale

    def make_svg(show_sol: bool) -> str:
        if spec.shape == "circular":
            return _render_circular_maze_svg(spec, theme, show_sol)
        if spec.shape == "hexagonal":
            return _render_hex_maze_svg(spec, theme, show_sol)
        return _render_rectangular_maze_svg(spec, theme, show_sol)

    story_html = (
        f'<div class="card-tinted" style="margin-bottom:{2.2 * s:.2f}mm;font-size:{8.8 * s:.1f}pt;font-style:italic;text-align:center;">{escape(spec.story_prompt)}</div>'
        if spec.story_prompt
        else ""
    )

    body = (
        f'<div style="display:flex;flex-direction:column;flex:1;min-height:0;">'
        f"{story_html}"
        f'<div class="card" style="flex:1;min-height:0;display:flex;align-items:center;justify-content:center;padding:{2.4 * s:.2f}mm;">'
        f"{make_svg(False)}</div></div>"
    )
    pages = [
        RenderedPage(
            title=spec.title,
            subtitle=spec.subtitle,
            category=f"{spec.shape.title()} Maze",
            instructions=spec.instructions,
            difficulty=spec.difficulty,
            body_html=body,
            footer_left=spec.author_credit or "Visual & Spatial Activities · Maze",
        )
    ]
    if spec.include_answer_key:
        ans_body = (
            f'<div class="card" style="flex:1;min-height:0;display:flex;align-items:center;justify-content:center;padding:{2.4 * s:.2f}mm;">'
            f"{make_svg(True)}</div>"
        )
        pages.append(
            RenderedPage(
                title=f"{spec.title} — Solution Path",
                category=f"{spec.shape.title()} Maze",
                is_answer_key=True,
                body_html=ans_body,
                footer_left=spec.author_credit or "Maze Answer Key",
            )
        )
    return pages


# ---------------------------------------------------------------------------
# 8. SPOT THE DIFFERENCE
# ---------------------------------------------------------------------------


def _render_spot_canvas(
    spec: SpotTheDifferenceSpec,
    elements: list[dict],
    theme: ThemeSpec,
    markers: list[dict] | None = None,
) -> str:
    w, h = spec.canvas_width, spec.canvas_height
    sky = "#FFFFFF" if theme.name.endswith("_inksaver") else spec.sky_color
    ground = "#F8F8F8" if theme.name.endswith("_inksaver") else spec.ground_color
    bg_parts = [f'<rect x="0" y="0" width="{w:.1f}" height="{h:.1f}" fill="{escape(sky)}"/>']
    if ground and spec.horizon_y is not None:
        hy = max(0.0, min(h, spec.horizon_y))
        bg_parts.append(
            f'<rect x="0" y="{hy:.1f}" width="{w:.1f}" height="{h - hy:.1f}" fill="{escape(ground)}"/>'
            f'<line x1="0" y1="{hy:.1f}" x2="{w:.1f}" y2="{hy:.1f}" stroke="{theme.border_strong}" stroke-width="1.2" opacity="0.5"/>'
        )
    els_svg = "".join(render_scene_element(el, default_ink=theme.ink) for el in elements)

    marker_svg = ""
    if markers:
        m_parts = []
        for m in markers:
            mx, my, num = m["x"], m["y"], m["number"]
            m_parts.append(
                f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="18" fill="none" stroke="{theme.answer_highlight}" stroke-width="3" stroke-dasharray="5 3"/>'
                f'<circle cx="{mx + 14:.1f}" cy="{my - 14:.1f}" r="9.5" fill="{theme.answer_highlight}"/>'
                f'<text x="{mx + 14:.1f}" y="{my - 14:.1f}" text-anchor="middle" dominant-baseline="central" font-size="10.5" font-weight="800" fill="#FFFFFF">{num}</text>'
            )
        marker_svg = "".join(m_parts)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
        f'preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;display:block;">'
        f'<defs><clipPath id="spotClip"><rect x="0" y="0" width="{w:.1f}" height="{h:.1f}" rx="8"/></clipPath></defs>'
        f'<g clip-path="url(#spotClip)">{"".join(bg_parts)}{els_svg}{marker_svg}</g>'
        f'<rect x="1" y="1" width="{w - 2:.1f}" height="{h - 2:.1f}" rx="8" fill="none" stroke="{theme.border_strong}" stroke-width="2"/>'
        f"</svg>"
    )


def render_spot_the_difference(
    spec: SpotTheDifferenceSpec, page: PageSpec, theme: ThemeSpec
) -> list[RenderedPage]:
    s = page.scale
    diff_dicts = [d.model_dump() for d in spec.differences]
    mod_elements, markers = apply_spot_differences(spec.base_elements, diff_dicts)

    svg_a = _render_spot_canvas(spec, spec.base_elements, theme)
    svg_b = _render_spot_canvas(spec, mod_elements, theme)
    svg_ans = _render_spot_canvas(spec, mod_elements, theme, markers=markers)

    layout = spec.layout
    if layout == "auto":
        layout = "side_by_side" if page.orientation == "landscape" else "stacked"
    flex_dir = "row" if layout == "side_by_side" else "column"

    checklist = ""
    if spec.show_checklist:
        boxes = "".join(
            f'<div style="display:inline-flex;align-items:center;gap:1.2mm;padding:0.7mm 2.2mm;border:0.7pt solid {theme.border};border-radius:1.2mm;background:{theme.paper};font-size:{8.0 * s:.1f}pt;font-weight:700;">'
            f'<span style="display:inline-block;width:{3.2 * s:.1f}mm;height:{3.2 * s:.1f}mm;border:1pt solid {theme.border_strong};border-radius:0.6mm;"></span>'
            f"#{d.number}</div>"
            for d in spec.differences
        )
        checklist = (
            f'<div class="card-tinted" style="flex:0 0 auto;margin-top:{2.0 * s:.2f}mm;padding:{1.6 * s:.2f}mm {2.4 * s:.2f}mm;display:flex;align-items:center;gap:2.5mm;flex-wrap:wrap;">'
            f'<span style="font-size:{7.6 * s:.1f}pt;font-weight:800;text-transform:uppercase;color:{theme.accent};">Found ({len(spec.differences)} Total):</span>'
            f"{boxes}</div>"
        )

    body = f"""
<div style="display:flex;flex-direction:column;flex:1;min-height:0;">
  <div style="display:flex;flex-direction:{flex_dir};gap:{2.6 * s:.2f}mm;flex:1;min-height:0;">
    <div class="card" style="flex:1;min-height:0;min-width:0;display:flex;flex-direction:column;padding:{1.8 * s:.2f}mm;">
      <div style="font-size:{7.6 * s:.1f}pt;font-weight:800;text-transform:uppercase;letter-spacing:0.06em;color:{theme.accent};margin-bottom:1mm;">Picture A · Original</div>
      <div style="flex:1;min-height:0;">{svg_a}</div>
    </div>
    <div class="card" style="flex:1;min-height:0;min-width:0;display:flex;flex-direction:column;padding:{1.8 * s:.2f}mm;">
      <div style="font-size:{7.6 * s:.1f}pt;font-weight:800;text-transform:uppercase;letter-spacing:0.06em;color:{theme.accent};margin-bottom:1mm;">Picture B · Spot {len(spec.differences)} Differences</div>
      <div style="flex:1;min-height:0;">{svg_b}</div>
    </div>
  </div>
  {checklist}
</div>"""

    pages = [
        RenderedPage(
            title=spec.title,
            subtitle=spec.subtitle or spec.scene_description,
            category="Spot the Difference",
            instructions=spec.instructions,
            difficulty=spec.difficulty,
            extra_badges=[f"{len(spec.differences)} Differences"],
            body_html=body,
            footer_left=spec.author_credit or "Visual & Spatial Activities · Spot the Difference",
        )
    ]

    if spec.include_answer_key:
        legend_items = "".join(
            f'<div style="display:flex;align-items:baseline;gap:1.8mm;font-size:{8.4 * s:.1f}pt;">'
            f'<span style="width:{4.8 * s:.1f}mm;height:{4.8 * s:.1f}mm;border-radius:50%;background:{theme.answer_highlight};color:#FFFFFF;font-size:{7.0 * s:.1f}pt;font-weight:800;display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;">{m["number"]}</span>'
            f'<span>{escape(m["description"])}</span></div>'
            for m in markers
        )
        ans_body = f"""
<div style="display:flex;flex-direction:column;flex:1;min-height:0;gap:{2.8 * s:.2f}mm;">
  <div class="card" style="flex:1.25;min-height:0;padding:{2.2 * s:.2f}mm;">{svg_ans}</div>
  <div class="card-tinted" style="flex:0 0 auto;display:grid;grid-template-columns:1fr 1fr;gap:{1.4 * s:.2f}mm {4 * s:.2f}mm;padding:{2.4 * s:.2f}mm {3 * s:.2f}mm;">
    {legend_items}
  </div>
</div>"""
        pages.append(
            RenderedPage(
                title=f"{spec.title} — All {len(spec.differences)} Differences",
                category="Spot the Difference",
                is_answer_key=True,
                body_html=ans_body,
                footer_left=spec.author_credit or "Spot the Difference Answer Key",
            )
        )
    return pages


# ---------------------------------------------------------------------------
# 9. HIDDEN PICTURES (I SPY)
# ---------------------------------------------------------------------------


def _render_hidden_object_svg(item, default_ink: str, highlight: str | None = None) -> str:
    stroke = highlight or item.stroke or default_ink
    sw = item.stroke_width * (1.45 if highlight else 1.0)
    op = 1.0 if highlight else item.opacity
    if item.icon_name:
        return render_icon_svg(
            item.icon_name,
            x=item.x,
            y=item.y,
            size=item.size,
            stroke=stroke,
            fill=item.fill,
            stroke_width=sw,
            rotate=item.rotate,
            flip_x=item.flip_x,
            opacity=op,
        )
    scale = item.size / 24.0
    sx = -scale if item.flip_x else scale
    t = f"translate({item.x:.2f},{item.y:.2f}) rotate({item.rotate:.2f}) scale({sx:.4f},{scale:.4f}) translate(-12,-12)"
    return (
        f'<g transform="{t}" fill="{escape(item.fill)}" stroke="{escape(stroke)}" '
        f'stroke-width="{sw / max(scale, 0.25):.2f}" stroke-linecap="round" stroke-linejoin="round" opacity="{op:.2f}">'
        f'<path d="{escape(item.custom_svg_path or "")}"/></g>'
    )


def render_hidden_pictures(
    spec: HiddenPicturesSpec, page: PageSpec, theme: ThemeSpec
) -> list[RenderedPage]:
    s = page.scale
    w, h = spec.canvas_width, spec.canvas_height
    bg_fill = "#FFFFFF" if theme.name.endswith("_inksaver") else spec.background_color
    bg_svg = "".join(render_scene_element(el, default_ink=theme.ink) for el in spec.background_elements)
    hidden_svg = "".join(_render_hidden_object_svg(obj, theme.ink) for obj in spec.hidden_objects)

    puzzle_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
        f'preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;display:block;">'
        f'<rect x="0" y="0" width="{w:.1f}" height="{h:.1f}" rx="8" fill="{escape(bg_fill)}"/>'
        f"{bg_svg}{hidden_svg}"
        f'<rect x="1" y="1" width="{w - 2:.1f}" height="{h - 2:.1f}" rx="8" fill="none" stroke="{theme.border_strong}" stroke-width="2"/>'
        f"</svg>"
    )

    # Checklist cards
    n_items = len(spec.hidden_objects)
    cols = 4 if n_items >= 8 else 3
    check_items = []
    for idx, obj in enumerate(spec.hidden_objects, start=1):
        mini_icon = ""
        if spec.checklist_style == "icon_and_label":
            if obj.icon_name:
                mini_icon = render_icon_svg(
                    obj.icon_name, size=18 * s, stroke=theme.accent, stroke_width=1.8, standalone=True
                )
            else:
                mini_icon = (
                    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{18 * s:.1f}" height="{18 * s:.1f}" '
                    f'fill="none" stroke="{theme.accent}" stroke-width="1.8"><path d="{escape(obj.custom_svg_path or "")}"/></svg>'
                )
        check_items.append(
            f'<div style="display:flex;align-items:center;gap:1.5mm;padding:{1.1 * s:.2f}mm {1.6 * s:.2f}mm;border:0.7pt solid {theme.border};border-radius:1.4mm;background:{theme.paper};">'
            f'<span style="width:{3.2 * s:.1f}mm;height:{3.2 * s:.1f}mm;border:1pt solid {theme.border_strong};border-radius:0.6mm;flex:0 0 auto;"></span>'
            f"{mini_icon}"
            f'<span style="font-size:{7.8 * s:.1f}pt;font-weight:700;line-height:1.15;">{escape(obj.name)}</span>'
            f"</div>"
        )

    body = f"""
<div style="display:flex;flex-direction:column;flex:1;min-height:0;gap:{2.4 * s:.2f}mm;">
  <div class="card" style="flex:1;min-height:0;padding:{1.8 * s:.2f}mm;">{puzzle_svg}</div>
  <div class="card-tinted" style="flex:0 0 auto;padding:{2.0 * s:.2f}mm {2.4 * s:.2f}mm;">
    <div class="section-heading" style="margin-bottom:1.4mm;">Objects to Find ({n_items})</div>
    <div style="display:grid;grid-template-columns:repeat({cols}, 1fr);gap:{1.4 * s:.2f}mm;">{"".join(check_items)}</div>
  </div>
</div>"""

    pages = [
        RenderedPage(
            title=spec.title,
            subtitle=spec.subtitle or spec.scene_description,
            category="Hidden Pictures (I Spy)",
            instructions=spec.instructions,
            difficulty=spec.difficulty,
            extra_badges=[f"Find {n_items} Objects"],
            body_html=body,
            footer_left=spec.author_credit or "Visual & Spatial Activities · Hidden Pictures",
        )
    ]

    if spec.include_answer_key:
        highlights = []
        legend = []
        for idx, obj in enumerate(spec.hidden_objects, start=1):
            highlights.append(_render_hidden_object_svg(obj, theme.ink, highlight=theme.answer_highlight))
            r_ring = max(16.0, obj.size * 0.72)
            highlights.append(
                f'<circle cx="{obj.x:.1f}" cy="{obj.y:.1f}" r="{r_ring:.1f}" fill="none" stroke="{theme.answer_highlight}" stroke-width="2.4" stroke-dasharray="4 3"/>'
                f'<circle cx="{obj.x + r_ring * 0.72:.1f}" cy="{obj.y - r_ring * 0.72:.1f}" r="9.5" fill="{theme.answer_highlight}"/>'
                f'<text x="{obj.x + r_ring * 0.72:.1f}" y="{obj.y - r_ring * 0.72:.1f}" text-anchor="middle" dominant-baseline="central" font-size="10" font-weight="800" fill="#FFFFFF">{idx}</text>'
            )
            hint_txt = f" ({escape(obj.hint)})" if obj.hint else ""
            legend.append(
                f'<div style="font-size:{8.0 * s:.1f}pt;"><b style="color:{theme.answer_highlight};">{idx}.</b> {escape(obj.name)}{hint_txt}</div>'
            )
        ans_svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
            f'preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;display:block;">'
            f'<rect x="0" y="0" width="{w:.1f}" height="{h:.1f}" rx="8" fill="#FFFFFF"/>'
            f'<g opacity="0.32">{bg_svg}</g>'
            f'{"".join(highlights)}'
            f'<rect x="1" y="1" width="{w - 2:.1f}" height="{h - 2:.1f}" rx="8" fill="none" stroke="{theme.border_strong}" stroke-width="2"/>'
            f"</svg>"
        )
        ans_body = f"""
<div style="display:flex;flex-direction:column;flex:1;min-height:0;gap:{2.4 * s:.2f}mm;">
  <div class="card" style="flex:1;min-height:0;padding:{2.0 * s:.2f}mm;">{ans_svg}</div>
  <div class="card-tinted" style="flex:0 0 auto;display:grid;grid-template-columns:repeat(3, 1fr);gap:1.2mm 3mm;padding:{2.0 * s:.2f}mm {2.6 * s:.2f}mm;">{"".join(legend)}</div>
</div>"""
        pages.append(
            RenderedPage(
                title=f"{spec.title} — Hidden Object Locations",
                category="Hidden Pictures (I Spy)",
                is_answer_key=True,
                body_html=ans_body,
                footer_left=spec.author_credit or "Hidden Pictures Answer Key",
            )
        )
    return pages


# ---------------------------------------------------------------------------
# 10. DOT-TO-DOT (CONNECT THE DOTS)
# ---------------------------------------------------------------------------


def _dot_label(index_0: int, spec: DotToDotSpec) -> str:
    if spec.sequence_type == "uppercase_letters":
        return chr(ord("A") + index_0)
    if spec.sequence_type == "lowercase_letters":
        return chr(ord("a") + index_0)
    if spec.sequence_type == "skip_count":
        return str((index_0 + 1) * spec.skip_step)
    return str(index_0 + 1)


def _auto_label_offset(
    pt_xy: tuple[float, float],
    prev_xy: tuple[float, float] | None,
    next_xy: tuple[float, float] | None,
    all_pts: list[tuple[float, float]],
    placed_labels: list[tuple[float, float]],
    w: float,
    h: float,
) -> tuple[float, float]:
    """Choose a crisp non-overlapping (dx, dy) label position around a dot."""
    px, py = pt_xy
    dist = 13.5
    candidates: list[tuple[float, float]] = []
    for deg in range(0, 360, 30):
        rad = math.radians(deg)
        candidates.append((math.cos(rad) * dist, math.sin(rad) * dist))

    best = (10.0, -10.0)
    best_score = -1e9
    for dx, dy in candidates:
        lx, ly = px + dx, py + dy
        score = 0.0
        # Stay safely inside canvas
        if lx < 14 or lx > w - 14 or ly < 14 or ly > h - 14:
            score -= 500.0
        # Distance from all other dots
        for ox, oy in all_pts:
            if abs(ox - px) < 1e-4 and abs(oy - py) < 1e-4:
                continue
            d = math.hypot(lx - ox, ly - oy)
            if d < 16:
                score -= (16 - d) * 14.0
        # Distance from already placed labels
        for olx, oly in placed_labels:
            d = math.hypot(lx - olx, ly - oly)
            if d < 19:
                score -= (19 - d) * 18.0
        # Push away from adjacent line segments
        for neighbor in (prev_xy, next_xy):
            if neighbor is not None:
                mx = (px + neighbor[0]) / 2.0
                my = (py + neighbor[1]) / 2.0
                d_mid = math.hypot(lx - mx, ly - my)
                score += min(d_mid, 25.0) * 0.6
        if score > best_score:
            best_score = score
            best = (dx, dy)
    return best


def render_dot_to_dot(spec: DotToDotSpec, page: PageSpec, theme: ThemeSpec) -> list[RenderedPage]:
    s = page.scale
    w, h = spec.canvas_width, spec.canvas_height
    all_pts = [(pt.x, pt.y) for sp in spec.paths for pt in sp.points]
    bg_svg = "".join(render_scene_element(el, default_ink=theme.ink_muted) for el in spec.background_elements)

    placed_labels: list[tuple[float, float]] = []
    dot_nodes: list[str] = []
    sol_paths: list[str] = []
    idx_global = 0

    for sp_idx, sp in enumerate(spec.paths):
        pts = sp.points
        if len(pts) >= 2:
            coords = " ".join(f"{p.x:.1f},{p.y:.1f}" for p in pts)
            fill = (spec.solution_fill or theme.accent_soft) if sp.close_path else "none"
            tag = "polygon" if sp.close_path else "polyline"
            sol_paths.append(
                f'<{tag} points="{coords}" fill="{escape(fill)}" stroke="{theme.ink}" '
                f'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'
            )

        for i, pt in enumerate(pts):
            label = _dot_label(idx_global, spec)
            prev_xy = (pts[i - 1].x, pts[i - 1].y) if i > 0 else None
            next_xy = (pts[i + 1].x, pts[i + 1].y) if i + 1 < len(pts) else None
            if pt.label_dx is not None and pt.label_dy is not None:
                dx, dy = pt.label_dx, pt.label_dy
            else:
                dx, dy = _auto_label_offset((pt.x, pt.y), prev_xy, next_xy, all_pts, placed_labels, w, h)
            lx, ly = pt.x + dx, pt.y + dy
            placed_labels.append((lx, ly))

            is_start = i == 0
            if is_start:
                dot_nodes.append(
                    f'<circle cx="{pt.x:.1f}" cy="{pt.y:.1f}" r="5.6" fill="{theme.accent}" stroke="#FFFFFF" stroke-width="1.4"/>'
                )
            else:
                dot_nodes.append(
                    f'<circle cx="{pt.x:.1f}" cy="{pt.y:.1f}" r="3.6" fill="{theme.ink}"/>'
                )

            # Star indicator if lifting pencil for a new sub-path
            extra_mark = " ★" if (is_start and sp_idx > 0) else ""
            dot_nodes.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="central" '
                f'font-size="11.5" font-weight="800" fill="{theme.accent if is_start else theme.ink}" '
                f'paint-order="stroke" stroke="#FFFFFF" stroke-width="3">{escape(label + extra_mark)}</text>'
            )
            idx_global += 1

    puzzle_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
        f'preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;display:block;">'
        f'<rect x="0" y="0" width="{w:.1f}" height="{h:.1f}" rx="8" fill="#FFFFFF"/>'
        f'<g opacity="0.65">{bg_svg}</g>'
        f'{"".join(dot_nodes)}'
        f'<rect x="1" y="1" width="{w - 2:.1f}" height="{h - 2:.1f}" rx="8" fill="none" stroke="{theme.border}" stroke-width="1.4"/>'
        f"</svg>"
    )

    sol_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
        f'preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;display:block;">'
        f'<rect x="0" y="0" width="{w:.1f}" height="{h:.1f}" rx="8" fill="#FFFFFF"/>'
        f"{bg_svg}"
        f'{"".join(sol_paths)}'
        f'<rect x="1" y="1" width="{w - 2:.1f}" height="{h - 2:.1f}" rx="8" fill="none" stroke="{theme.border_strong}" stroke-width="1.8"/>'
        f"</svg>"
    )

    note_lift = (
        f' · <b style="color:{theme.accent};">★</b> marks where to lift your pencil for a new line.'
        if len(spec.paths) > 1
        else ""
    )
    seq_desc = {
        "numbers": f"1 to {idx_global}",
        "uppercase_letters": f"A to {_dot_label(idx_global - 1, spec)}",
        "lowercase_letters": f"a to {_dot_label(idx_global - 1, spec)}",
        "skip_count": f"Skip by {spec.skip_step}s ({spec.skip_step} to {idx_global * spec.skip_step})",
    }[spec.sequence_type]

    body = f"""
<div style="display:flex;flex-direction:column;flex:1;min-height:0;gap:{2.0 * s:.2f}mm;">
  <div class="card" style="flex:1;min-height:0;padding:{2.0 * s:.2f}mm;">{puzzle_svg}</div>
  <div class="card-tinted" style="flex:0 0 auto;display:flex;justify-content:space-between;align-items:center;font-size:{8.0 * s:.1f}pt;padding:{1.5 * s:.2f}mm {2.8 * s:.2f}mm;">
    <span><b>Sequence:</b> {escape(seq_desc)}{note_lift}</span>
    <span><b>Hidden Picture:</b> {escape(spec.subject) if spec.reveal_subject_on_puzzle else '<span style="display:inline-block;width:30mm;border-bottom:0.8pt solid currentColor;"></span>'}</span>
  </div>
</div>"""

    pages = [
        RenderedPage(
            title=spec.title,
            subtitle=spec.subtitle,
            category="Dot-to-Dot",
            instructions=spec.instructions,
            difficulty=spec.difficulty,
            extra_badges=[f"{idx_global} Dots"],
            body_html=body,
            footer_left=spec.author_credit or "Visual & Spatial Activities · Dot-to-Dot",
        )
    ]
    if spec.include_answer_key:
        ans_body = f"""
<div style="display:flex;flex-direction:column;flex:1;min-height:0;gap:{2.4 * s:.2f}mm;">
  <div class="card-tinted" style="text-align:center;font-size:{11 * s:.1f}pt;font-family:{theme.font_display};font-weight:700;color:{theme.accent};">
    Completed Picture: {escape(spec.subject)}
  </div>
  <div class="card" style="flex:1;min-height:0;padding:{2.4 * s:.2f}mm;">{sol_svg}</div>
</div>"""
        pages.append(
            RenderedPage(
                title=f"{spec.title} — Completed Reveal",
                category="Dot-to-Dot",
                is_answer_key=True,
                body_html=ans_body,
                footer_left=spec.author_credit or "Dot-to-Dot Answer Key",
            )
        )
    return pages


# ---------------------------------------------------------------------------
# 11. COLOR-BY-NUMBER / PAINT-BY-NUMBER
# ---------------------------------------------------------------------------


def _polygon_centroid(pts: list[list[float]]) -> tuple[float, float]:
    n = len(pts)
    if n == 0:
        return 0.0, 0.0
    area2 = 0.0
    cx = 0.0
    cy = 0.0
    for i in range(n):
        x0, y0 = float(pts[i][0]), float(pts[i][1])
        x1, y1 = float(pts[(i + 1) % n][0]), float(pts[(i + 1) % n][1])
        cross = x0 * y1 - x1 * y0
        area2 += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    if abs(area2) < 1e-6:
        return sum(float(p[0]) for p in pts) / n, sum(float(p[1]) for p in pts) / n
    return cx / (3.0 * area2), cy / (3.0 * area2)


def _region_center(r) -> tuple[float, float]:
    if r.label_x is not None and r.label_y is not None:
        return float(r.label_x), float(r.label_y)
    if r.shape_type == "polygon" and r.points:
        return _polygon_centroid(r.points)
    if r.shape_type in {"circle", "ellipse"}:
        return float(r.cx or 0), float(r.cy or 0)
    if r.shape_type == "rect":
        return float(r.x or 0) + float(r.width or 0) / 2.0, float(r.y or 0) + float(r.height or 0) / 2.0
    return 0.0, 0.0


def _render_color_region(r, fill: str, stroke: str) -> str:
    if r.shape_type == "polygon" and r.points:
        pts = " ".join(f"{float(p[0]):.1f},{float(p[1]):.1f}" for p in r.points)
        return f'<polygon points="{pts}" fill="{escape(fill)}" stroke="{escape(stroke)}" stroke-width="1.6" stroke-linejoin="round"/>'
    if r.shape_type == "path" and r.d:
        return f'<path d="{escape(r.d)}" fill="{escape(fill)}" stroke="{escape(stroke)}" stroke-width="1.6" stroke-linejoin="round"/>'
    if r.shape_type == "circle":
        return f'<circle cx="{float(r.cx or 0):.1f}" cy="{float(r.cy or 0):.1f}" r="{float(r.r or 15):.1f}" fill="{escape(fill)}" stroke="{escape(stroke)}" stroke-width="1.6"/>'
    if r.shape_type == "ellipse":
        return f'<ellipse cx="{float(r.cx or 0):.1f}" cy="{float(r.cy or 0):.1f}" rx="{float(r.rx or 20):.1f}" ry="{float(r.ry or 12):.1f}" fill="{escape(fill)}" stroke="{escape(stroke)}" stroke-width="1.6"/>'
    if r.shape_type == "rect":
        return (
            f'<rect x="{float(r.x or 0):.1f}" y="{float(r.y or 0):.1f}" '
            f'width="{float(r.width or 30):.1f}" height="{float(r.height or 30):.1f}" '
            f'fill="{escape(fill)}" stroke="{escape(stroke)}" stroke-width="1.6"/>'
        )
    return ""


def render_color_by_number(
    spec: ColorByNumberSpec, page: PageSpec, theme: ThemeSpec
) -> list[RenderedPage]:
    s = page.scale
    w, h = spec.canvas_width, spec.canvas_height
    palette_map = {p.number: p for p in spec.palette}
    deco_svg = "".join(render_scene_element(el, default_ink=theme.ink) for el in spec.decorative_elements)

    blank_shapes: list[str] = []
    num_labels: list[str] = []
    colored_shapes: list[str] = []

    for r in spec.regions:
        pal = palette_map[r.color_number]
        blank_shapes.append(_render_color_region(r, "#FFFFFF", theme.ink))
        colored_shapes.append(_render_color_region(r, pal.hex_color, theme.ink))
        cx, cy = _region_center(r)
        fs = r.label_size or 12.0
        num_labels.append(
            f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'font-size="{fs:.1f}" font-weight="800" fill="{theme.ink_muted}" '
            f'paint-order="stroke" stroke="#FFFFFF" stroke-width="2.5">{r.color_number}</text>'
        )

    puzzle_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
        f'preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;display:block;">'
        f'<rect x="0" y="0" width="{w:.1f}" height="{h:.1f}" rx="8" fill="#FFFFFF"/>'
        f'{"".join(blank_shapes)}{deco_svg}{"".join(num_labels)}'
        f'<rect x="1" y="1" width="{w - 2:.1f}" height="{h - 2:.1f}" rx="8" fill="none" stroke="{theme.border_strong}" stroke-width="2"/>'
        f"</svg>"
    )
    colored_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
        f'preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;display:block;">'
        f'<rect x="0" y="0" width="{w:.1f}" height="{h:.1f}" rx="8" fill="#FFFFFF"/>'
        f'{"".join(colored_shapes)}{deco_svg}'
        f'<rect x="1" y="1" width="{w - 2:.1f}" height="{h - 2:.1f}" rx="8" fill="none" stroke="{theme.border_strong}" stroke-width="2"/>'
        f"</svg>"
    )

    is_bw = theme.name.endswith("_inksaver")
    swatches = []
    for p in sorted(spec.palette, key=lambda x: x.number):
        swatch_dot = ""
        if spec.show_color_swatches:
            bg = "#FFFFFF" if is_bw else p.hex_color
            swatch_dot = (
                f'<span style="display:inline-flex;align-items:center;justify-content:center;'
                f'width:{5.6 * s:.1f}mm;height:{5.6 * s:.1f}mm;border-radius:50%;background:{escape(bg)};'
                f'border:1pt solid {theme.border_strong};font-size:{7.6 * s:.1f}pt;font-weight:900;'
                f'color:{theme.ink};flex:0 0 auto;">'
                f'{" " if not is_bw else p.number}</span>'
            )
        swatches.append(
            f'<div style="display:flex;align-items:center;gap:1.6mm;padding:{1.0 * s:.2f}mm {2.0 * s:.2f}mm;border:0.7pt solid {theme.border};border-radius:1.4mm;background:{theme.paper};">'
            f'<span style="font-family:{theme.font_mono};font-weight:900;font-size:{9.0 * s:.1f}pt;color:{theme.accent};min-width:4mm;">{p.number}</span>'
            f"{swatch_dot}"
            f'<span style="font-size:{8.0 * s:.1f}pt;font-weight:700;">{escape(p.color_name)}</span>'
            f"</div>"
        )

    pal_cols = 4 if len(spec.palette) >= 7 else 3
    palette_bar = (
        f'<div class="card-tinted" style="flex:0 0 auto;padding:{1.8 * s:.2f}mm {2.4 * s:.2f}mm;">'
        f'<div class="section-heading" style="margin-bottom:1.2mm;">Color Palette Key</div>'
        f'<div style="display:grid;grid-template-columns:repeat({pal_cols}, 1fr);gap:{1.4 * s:.2f}mm;">{"".join(swatches)}</div>'
        f"</div>"
    )

    body = f"""
<div style="display:flex;flex-direction:column;flex:1;min-height:0;gap:{2.2 * s:.2f}mm;">
  <div class="card" style="flex:1;min-height:0;padding:{1.8 * s:.2f}mm;">{puzzle_svg}</div>
  {palette_bar}
</div>"""

    pages = [
        RenderedPage(
            title=spec.title,
            subtitle=spec.subtitle or spec.subject,
            category="Color-by-Number",
            instructions=spec.instructions,
            difficulty=spec.difficulty,
            extra_badges=[f"{len(spec.palette)} Colors"],
            body_html=body,
            footer_left=spec.author_credit or "Visual & Spatial Activities · Color-by-Number",
        )
    ]
    if spec.include_answer_key:
        ans_body = f"""
<div style="display:flex;flex-direction:column;flex:1;min-height:0;gap:{2.2 * s:.2f}mm;">
  <div class="card" style="flex:1;min-height:0;padding:{1.8 * s:.2f}mm;">{colored_svg}</div>
  {palette_bar}
</div>"""
        pages.append(
            RenderedPage(
                title=f"{spec.title} — Completed Artwork",
                category="Color-by-Number",
                is_answer_key=True,
                body_html=ans_body,
                footer_left=spec.author_credit or "Color-by-Number Answer Key",
            )
        )
    return pages
