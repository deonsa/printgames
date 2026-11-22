"""Declarative vector SVG scene engine for illustrations, Rebuses, Spot the Difference, and I Spy."""

from __future__ import annotations

import copy
import math
import re
from html import escape
from typing import Any

from .icons import render_icon_svg


def _points_str(points: list[list[float]] | list[tuple[float, float]]) -> str:
    return " ".join(f"{float(p[0]):.2f},{float(p[1]):.2f}" for p in points)


def _star_points(cx: float, cy: float, r_outer: float, r_inner: float, spikes: int = 5) -> str:
    pts: list[tuple[float, float]] = []
    for i in range(spikes * 2):
        angle = -math.pi / 2 + i * math.pi / spikes
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
    return _points_str(pts)


def element_center(el: dict[str, Any]) -> tuple[float, float]:
    """Estimate the visual center (x, y) of a scene element for markers & transforms."""
    etype = el.get("type", "")
    if etype in {"circle", "ellipse", "star"}:
        return float(el.get("cx", el.get("x", 0))), float(el.get("cy", el.get("y", 0)))
    if etype == "rect":
        x = float(el.get("x", 0))
        y = float(el.get("y", 0))
        w = float(el.get("width", 20))
        h = float(el.get("height", 20))
        return x + w / 2.0, y + h / 2.0
    if etype == "line":
        return (
            (float(el.get("x1", 0)) + float(el.get("x2", 0))) / 2.0,
            (float(el.get("y1", 0)) + float(el.get("y2", 0))) / 2.0,
        )
    if etype in {"polygon", "polyline"}:
        pts = el.get("points") or []
        if pts:
            xs = [float(p[0]) for p in pts]
            ys = [float(p[1]) for p in pts]
            return sum(xs) / len(xs), sum(ys) / len(ys)
    return float(el.get("x", 0)), float(el.get("y", 0))


def _path_marker(el: dict[str, Any]) -> tuple[float, float]:
    # Use the first point on the stroke when the author has not supplied an anchor.
    number = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
    match = re.match(rf"\s*[Mm]\s*({number})[\s,]*({number})", str(el.get("d", "")))
    x, y = map(float, match.groups()) if match else (0.0, 0.0)
    pivot_x, pivot_y = element_center(el)
    scale = float(el.get("scale", 1.0) or 1.0)
    x = (float(el.get("x", x)) - pivot_x) * scale * (-1 if el.get("flip_x") else 1)
    y = (float(el.get("y", y)) - pivot_y) * scale
    angle = math.radians(float(el.get("rotate", 0) or 0))
    return (
        pivot_x + x * math.cos(angle) - y * math.sin(angle) + float(el.get("translate_x", 0)),
        pivot_y + x * math.sin(angle) + y * math.cos(angle) + float(el.get("translate_y", 0)),
    )


def _wrap_transform(inner: str, el: dict[str, Any]) -> str:
    rotate = float(el.get("rotate", 0) or 0)
    flip_x = bool(el.get("flip_x", False))
    scale = float(el.get("scale", 1.0) or 1.0)
    if rotate == 0 and not flip_x and abs(scale - 1.0) < 1e-6:
        return inner
    cx, cy = element_center(el)
    sx = -scale if flip_x else scale
    parts = [f"translate({cx:.2f},{cy:.2f})"]
    if rotate:
        parts.append(f"rotate({rotate:.2f})")
    if flip_x or abs(scale - 1.0) >= 1e-6:
        parts.append(f"scale({sx:.4f},{scale:.4f})")
    parts.append(f"translate({-cx:.2f},{-cy:.2f})")
    return f'<g transform="{" ".join(parts)}">{inner}</g>'


def render_scene_element(el: dict[str, Any], default_ink: str = "#1F2421") -> str:
    """Render one declarative vector scene element into clean SVG markup."""
    etype = str(el.get("type", "")).lower()
    fill = str(el.get("fill", "none"))
    stroke = str(el.get("stroke", default_ink))
    sw = float(el.get("stroke_width", 1.8))
    opacity = float(el.get("opacity", 1.0))
    dash = f' stroke-dasharray="{escape(str(el["dash"]))}"' if el.get("dash") else ""

    if etype == "icon":
        icon_name = str(el.get("icon_name", "star"))
        x = float(el.get("x", 0))
        y = float(el.get("y", 0))
        size = float(el.get("size", 28)) * float(el.get("scale", 1.0) or 1.0)
        return render_icon_svg(
            icon_name,
            x=x,
            y=y,
            size=size,
            stroke=stroke,
            fill=fill,
            stroke_width=sw,
            rotate=float(el.get("rotate", 0) or 0),
            flip_x=bool(el.get("flip_x", False)),
            opacity=opacity,
        )

    if etype == "rect":
        rx = float(el.get("rx", 0))
        inner = (
            f'<rect x="{float(el.get("x", 0)):.2f}" y="{float(el.get("y", 0)):.2f}" '
            f'width="{float(el.get("width", 20)):.2f}" height="{float(el.get("height", 20)):.2f}" '
            f'rx="{rx:.2f}" fill="{escape(fill)}" stroke="{escape(stroke)}" '
            f'stroke-width="{sw:.2f}" opacity="{opacity:.2f}"{dash}/>'
        )
        return _wrap_transform(inner, el)

    if etype == "circle":
        cx = float(el.get("cx", el.get("x", 0)))
        cy = float(el.get("cy", el.get("y", 0)))
        r = float(el.get("r", el.get("size", 14)))
        inner = (
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" '
            f'fill="{escape(fill)}" stroke="{escape(stroke)}" '
            f'stroke-width="{sw:.2f}" opacity="{opacity:.2f}"{dash}/>'
        )
        return _wrap_transform(inner, el)

    if etype == "ellipse":
        cx = float(el.get("cx", el.get("x", 0)))
        cy = float(el.get("cy", el.get("y", 0)))
        rx = float(el.get("rx", 20))
        ry = float(el.get("ry", 12))
        inner = (
            f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" '
            f'fill="{escape(fill)}" stroke="{escape(stroke)}" '
            f'stroke-width="{sw:.2f}" opacity="{opacity:.2f}"{dash}/>'
        )
        return _wrap_transform(inner, el)

    if etype == "line":
        inner = (
            f'<line x1="{float(el.get("x1", 0)):.2f}" y1="{float(el.get("y1", 0)):.2f}" '
            f'x2="{float(el.get("x2", 40)):.2f}" y2="{float(el.get("y2", 0)):.2f}" '
            f'stroke="{escape(stroke)}" stroke-width="{sw:.2f}" '
            f'stroke-linecap="round" opacity="{opacity:.2f}"{dash}/>'
        )
        return _wrap_transform(inner, el)

    if etype == "polygon":
        pts = _points_str(el.get("points") or [])
        inner = (
            f'<polygon points="{pts}" fill="{escape(fill)}" stroke="{escape(stroke)}" '
            f'stroke-width="{sw:.2f}" stroke-linejoin="round" opacity="{opacity:.2f}"{dash}/>'
        )
        return _wrap_transform(inner, el)

    if etype == "polyline":
        pts = _points_str(el.get("points") or [])
        inner = (
            f'<polyline points="{pts}" fill="{escape(fill)}" stroke="{escape(stroke)}" '
            f'stroke-width="{sw:.2f}" stroke-linecap="round" stroke-linejoin="round" '
            f'opacity="{opacity:.2f}"{dash}/>'
        )
        return _wrap_transform(inner, el)

    if etype == "path":
        d = escape(str(el.get("d", "")))
        inner = (
            f'<path d="{d}" fill="{escape(fill)}" stroke="{escape(stroke)}" '
            f'stroke-width="{sw:.2f}" stroke-linecap="round" stroke-linejoin="round" '
            f'opacity="{opacity:.2f}"{dash}/>'
        )
        path = _wrap_transform(inner, el)
        dx, dy = el.get("translate_x", 0.0), el.get("translate_y", 0.0)
        if dx or dy:
            return f'<g transform="translate({float(dx):.2f},{float(dy):.2f})">{path}</g>'
        return path

    if etype == "star":
        cx = float(el.get("cx", el.get("x", 0)))
        cy = float(el.get("cy", el.get("y", 0)))
        r = float(el.get("r", el.get("size", 14)))
        r_in = float(el.get("inner_r", r * 0.45))
        spikes = int(el.get("spikes", 5))
        pts = _star_points(cx, cy, r, r_in, spikes)
        inner = (
            f'<polygon points="{pts}" fill="{escape(fill)}" stroke="{escape(stroke)}" '
            f'stroke-width="{sw:.2f}" stroke-linejoin="round" opacity="{opacity:.2f}"/>'
        )
        return _wrap_transform(inner, el)

    if etype == "text":
        x = float(el.get("x", 0))
        y = float(el.get("y", 0))
        text = escape(str(el.get("text", "")))
        font_size = float(el.get("font_size", 18))
        weight = str(el.get("weight", "700"))
        color = str(el.get("color", el.get("fill", default_ink)))
        if color == "none":
            color = default_ink
        anchor = str(el.get("align", "middle"))
        anchor_map = {"left": "start", "center": "middle", "middle": "middle", "right": "end"}
        svg_anchor = anchor_map.get(anchor, "middle")
        style_parts = [f"font-size:{font_size:.1f}px"]
        if el.get("italic"):
            style_parts.append("font-style:italic")
        if el.get("underline"):
            style_parts.append("text-decoration:underline")
        if el.get("strikethrough"):
            style_parts.append("text-decoration:line-through")
        if el.get("letter_spacing") is not None:
            style_parts.append(f"letter-spacing:{float(el['letter_spacing']):.2f}px")
        if el.get("vertical"):
            style_parts.append("writing-mode:vertical-rl;text-orientation:upright")
        font_family = el.get("font_family", "inherit")

        inner = (
            f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{svg_anchor}" '
            f'dominant-baseline="central" fill="{escape(color)}" '
            f'font-weight="{escape(weight)}" font-family="{escape(str(font_family))}" '
            f'opacity="{opacity:.2f}" style="{";".join(style_parts)}">{text}</text>'
        )
        return _wrap_transform(inner, el)

    # Rich multi-part scenic motifs for charming illustrations
    if etype == "scenic_tree":
        x = float(el.get("x", 0))
        y = float(el.get("y", 0))
        size = float(el.get("size", 60))
        trunk_fill = str(el.get("trunk_fill", "#8B5E3C"))
        canopy_fill = str(el.get("fill", "#4E8B63"))
        if canopy_fill == "none":
            canopy_fill = "#FFFFFF"
        w = size * 0.6
        inner = (
            f'<g opacity="{opacity:.2f}" stroke="{escape(stroke)}" stroke-width="{sw:.2f}" stroke-linejoin="round">'
            f'<rect x="{x - w * 0.14:.2f}" y="{y - size * 0.35:.2f}" width="{w * 0.28:.2f}" height="{size * 0.35:.2f}" fill="{escape(trunk_fill)}" rx="2"/>'
            f'<circle cx="{x:.2f}" cy="{y - size * 0.62:.2f}" r="{size * 0.30:.2f}" fill="{escape(canopy_fill)}"/>'
            f'<circle cx="{x - size * 0.20:.2f}" cy="{y - size * 0.48:.2f}" r="{size * 0.22:.2f}" fill="{escape(canopy_fill)}"/>'
            f'<circle cx="{x + size * 0.20:.2f}" cy="{y - size * 0.48:.2f}" r="{size * 0.22:.2f}" fill="{escape(canopy_fill)}"/>'
            f"</g>"
        )
        return _wrap_transform(inner, el)

    if etype == "scenic_pine":
        x = float(el.get("x", 0))
        y = float(el.get("y", 0))
        size = float(el.get("size", 64))
        trunk_fill = str(el.get("trunk_fill", "#7A5035"))
        canopy_fill = str(el.get("fill", "#2F6B4F"))
        if canopy_fill == "none":
            canopy_fill = "#FFFFFF"
        inner = (
            f'<g opacity="{opacity:.2f}" stroke="{escape(stroke)}" stroke-width="{sw:.2f}" stroke-linejoin="round">'
            f'<rect x="{x - size * 0.08:.2f}" y="{y - size * 0.22:.2f}" width="{size * 0.16:.2f}" height="{size * 0.22:.2f}" fill="{escape(trunk_fill)}"/>'
            f'<polygon points="{x:.2f},{y - size * 0.68:.2f} {x - size * 0.34:.2f},{y - size * 0.20:.2f} {x + size * 0.34:.2f},{y - size * 0.20:.2f}" fill="{escape(canopy_fill)}"/>'
            f'<polygon points="{x:.2f},{y - size * 0.88:.2f} {x - size * 0.27:.2f},{y - size * 0.44:.2f} {x + size * 0.27:.2f},{y - size * 0.44:.2f}" fill="{escape(canopy_fill)}"/>'
            f'<polygon points="{x:.2f},{y - size:.2f} {x - size * 0.20:.2f},{y - size * 0.66:.2f} {x + size * 0.20:.2f},{y - size * 0.66:.2f}" fill="{escape(canopy_fill)}"/>'
            f"</g>"
        )
        return _wrap_transform(inner, el)

    if etype == "scenic_house":
        x = float(el.get("x", 0))
        y = float(el.get("y", 0))
        w = float(el.get("width", 90))
        h = float(el.get("height", 70))
        wall_fill = str(el.get("fill", "#F5E6D3"))
        roof_fill = str(el.get("roof_fill", "#C25441"))
        door_fill = str(el.get("door_fill", "#7E4B32"))
        win_fill = str(el.get("window_fill", "#DDF1FA"))
        inner = (
            f'<g opacity="{opacity:.2f}" stroke="{escape(stroke)}" stroke-width="{sw:.2f}" stroke-linejoin="round">'
            f'<rect x="{x - w / 2:.2f}" y="{y - h * 0.62:.2f}" width="{w:.2f}" height="{h * 0.62:.2f}" fill="{escape(wall_fill)}"/>'
            f'<polygon points="{x - w * 0.58:.2f},{y - h * 0.62:.2f} {x:.2f},{y - h:.2f} {x + w * 0.58:.2f},{y - h * 0.62:.2f}" fill="{escape(roof_fill)}"/>'
            f'<rect x="{x - w * 0.13:.2f}" y="{y - h * 0.34:.2f}" width="{w * 0.26:.2f}" height="{h * 0.34:.2f}" fill="{escape(door_fill)}"/>'
            f'<rect x="{x - w * 0.38:.2f}" y="{y - h * 0.48:.2f}" width="{w * 0.18:.2f}" height="{h * 0.18:.2f}" fill="{escape(win_fill)}"/>'
            f'<rect x="{x + w * 0.20:.2f}" y="{y - h * 0.48:.2f}" width="{w * 0.18:.2f}" height="{h * 0.18:.2f}" fill="{escape(win_fill)}"/>'
            f"</g>"
        )
        return _wrap_transform(inner, el)

    if etype == "scenic_cloud":
        x = float(el.get("x", 0))
        y = float(el.get("y", 0))
        size = float(el.get("size", 46))
        cfill = str(el.get("fill", "#FFFFFF"))
        r = size * 0.28
        inner = (
            f'<g opacity="{opacity:.2f}" fill="{escape(cfill)}" stroke="{escape(stroke)}" stroke-width="{sw:.2f}">'
            f'<path d="M {x - r * 1.4:.2f} {y + r * 0.5:.2f} '
            f'A {r * 0.75:.2f} {r * 0.75:.2f} 0 0 1 {x - r * 1.1:.2f} {y - r * 0.4:.2f} '
            f'A {r * 1.05:.2f} {r * 1.05:.2f} 0 0 1 {x + r * 0.4:.2f} {y - r * 0.65:.2f} '
            f'A {r * 0.85:.2f} {r * 0.85:.2f} 0 0 1 {x + r * 1.45:.2f} {y + r * 0.5:.2f} Z"/>'
            f"</g>"
        )
        return _wrap_transform(inner, el)

    if etype == "scenic_mountain":
        x = float(el.get("x", 0))
        y = float(el.get("y", 0))
        w = float(el.get("width", 140))
        h = float(el.get("height", 95))
        mfill = str(el.get("fill", "#8EA3B0"))
        cap_fill = str(el.get("cap_fill", "#FFFFFF"))
        inner = (
            f'<g opacity="{opacity:.2f}" stroke="{escape(stroke)}" stroke-width="{sw:.2f}" stroke-linejoin="round">'
            f'<polygon points="{x - w / 2:.2f},{y:.2f} {x:.2f},{y - h:.2f} {x + w / 2:.2f},{y:.2f}" fill="{escape(mfill)}"/>'
            f'<polygon points="{x - w * 0.16:.2f},{y - h * 0.68:.2f} {x:.2f},{y - h:.2f} {x + w * 0.16:.2f},{y - h * 0.68:.2f} {x + w * 0.05:.2f},{y - h * 0.62:.2f} {x - w * 0.05:.2f},{y - h * 0.69:.2f}" fill="{escape(cap_fill)}"/>'
            f"</g>"
        )
        return _wrap_transform(inner, el)

    if etype == "scenic_bush":
        x = float(el.get("x", 0))
        y = float(el.get("y", 0))
        size = float(el.get("size", 40))
        bfill = str(el.get("fill", "#629C6A"))
        r = size * 0.35
        inner = (
            f'<g opacity="{opacity:.2f}" fill="{escape(bfill)}" stroke="{escape(stroke)}" stroke-width="{sw:.2f}">'
            f'<path d="M {x - r * 1.5:.2f} {y:.2f} '
            f'A {r * 0.7:.2f} {r * 0.7:.2f} 0 0 1 {x - r * 0.8:.2f} {y - r * 0.85:.2f} '
            f'A {r * 0.95:.2f} {r * 0.95:.2f} 0 0 1 {x + r * 0.8:.2f} {y - r * 0.85:.2f} '
            f'A {r * 0.7:.2f} {r * 0.7:.2f} 0 0 1 {x + r * 1.5:.2f} {y:.2f} Z"/>'
            f"</g>"
        )
        return _wrap_transform(inner, el)

    if etype == "scenic_fence":
        x = float(el.get("x", 0))
        y = float(el.get("y", 0))
        w = float(el.get("width", 100))
        h = float(el.get("height", 26))
        pickets = max(3, int(el.get("pickets", 6)))
        ffill = str(el.get("fill", "#F4EDE1"))
        step = w / pickets
        pw = step * 0.56
        parts = [
            f'<rect x="{x:.2f}" y="{y - h * 0.72:.2f}" width="{w:.2f}" height="{h * 0.14:.2f}" fill="{escape(ffill)}"/>',
            f'<rect x="{x:.2f}" y="{y - h * 0.32:.2f}" width="{w:.2f}" height="{h * 0.14:.2f}" fill="{escape(ffill)}"/>',
        ]
        for i in range(pickets):
            px = x + i * step + (step - pw) / 2
            parts.append(
                f'<polygon points="{px:.2f},{y:.2f} {px:.2f},{y - h * 0.82:.2f} '
                f'{px + pw / 2:.2f},{y - h:.2f} {px + pw:.2f},{y - h * 0.82:.2f} '
                f'{px + pw:.2f},{y:.2f}" fill="{escape(ffill)}"/>'
            )
        inner = (
            f'<g opacity="{opacity:.2f}" stroke="{escape(stroke)}" stroke-width="{sw:.2f}" stroke-linejoin="round">'
            + "".join(parts)
            + "</g>"
        )
        return _wrap_transform(inner, el)

    if etype == "scenic_wave":
        x = float(el.get("x", 0))
        y = float(el.get("y", 0))
        w = float(el.get("width", 80))
        amp = float(el.get("amplitude", 6))
        cycles = max(1, int(el.get("cycles", 3)))
        seg = w / cycles
        d_parts = [f"M {x:.2f} {y:.2f}"]
        for i in range(cycles):
            x0 = x + i * seg
            d_parts.append(
                f"Q {x0 + seg * 0.25:.2f} {y - amp:.2f}, {x0 + seg * 0.5:.2f} {y:.2f} "
                f"T {x0 + seg:.2f} {y:.2f}"
            )
        inner = (
            f'<path d="{" ".join(d_parts)}" fill="none" stroke="{escape(stroke)}" '
            f'stroke-width="{sw:.2f}" stroke-linecap="round" opacity="{opacity:.2f}"/>'
        )
        return _wrap_transform(inner, el)

    raise ValueError(f"Unsupported scene element type: '{etype}'")


def apply_spot_differences(
    base_elements: list[dict[str, Any]],
    differences: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Apply exact programmatic mutations to build Picture B + marker coordinates.

    Returns (modified_elements, resolved_markers).
    """
    elements = [copy.deepcopy(el) for el in base_elements]
    by_id: dict[str, int] = {
        str(el["id"]): idx for idx, el in enumerate(elements) if el.get("id") is not None
    }
    markers: list[dict[str, Any]] = []
    removed_ids: set[str] = set()

    for diff in differences:
        num = int(diff["number"])
        target_id = str(diff["target_id"])
        ctype = str(diff["change_type"]).lower()
        params = dict(diff.get("params") or {})
        mx = diff.get("marker_x")
        my = diff.get("marker_y")

        if ctype == "add":
            new_el = copy.deepcopy(params.get("element"))
            if not isinstance(new_el, dict):
                raise ValueError(
                    f"Difference #{num} with change_type='add' requires params.element dict."
                )
            elements.append(new_el)
            marker_element = new_el
        else:
            if target_id not in by_id:
                raise ValueError(
                    f"Difference #{num} references unknown target_id '{target_id}'."
                )
            el = elements[by_id[target_id]]
            marker_element = el

            if ctype == "remove":
                removed_ids.add(target_id)
            elif ctype == "recolor":
                for k in ("fill", "stroke", "roof_fill", "door_fill", "window_fill", "color"):
                    if k in params:
                        el[k] = params[k]
            elif ctype == "move":
                dx = float(params.get("dx", 0))
                dy = float(params.get("dy", 0))
                if str(el.get("type", "")).lower() == "path":
                    el["translate_x"] = float(el.get("translate_x", 0)) + dx
                    el["translate_y"] = float(el.get("translate_y", 0)) + dy
                else:
                    for key in ("x", "cx", "x1", "x2"):
                        if key in el:
                            el[key] = float(el[key]) + dx
                    for key in ("y", "cy", "y1", "y2"):
                        if key in el:
                            el[key] = float(el[key]) + dy
                    if "points" in el and isinstance(el["points"], list):
                        el["points"] = [[float(p[0]) + dx, float(p[1]) + dy] for p in el["points"]]
            elif ctype == "resize":
                factor = float(params.get("scale", 1.35))
                if "size" in el:
                    el["size"] = float(el["size"]) * factor
                elif "r" in el:
                    el["r"] = float(el["r"]) * factor
                else:
                    el["scale"] = float(el.get("scale", 1.0)) * factor
            elif ctype == "rotate":
                el["rotate"] = float(el.get("rotate", 0)) + float(params.get("angle", 45))
            elif ctype == "flip_x":
                el["flip_x"] = not bool(el.get("flip_x", False))
            elif ctype == "replace_icon":
                new_icon = params.get("icon_name")
                if not new_icon:
                    raise ValueError(f"Difference #{num} 'replace_icon' requires params.icon_name.")
                el["icon_name"] = str(new_icon)
            elif ctype == "change_text":
                new_text = params.get("text")
                if new_text is None:
                    raise ValueError(f"Difference #{num} 'change_text' requires params.text.")
                el["text"] = str(new_text)
            else:
                raise ValueError(f"Unsupported change_type '{ctype}' on difference #{num}.")

        if str(marker_element.get("type", "")).lower() == "path":
            cx, cy = _path_marker(marker_element)
        else:
            cx, cy = element_center(marker_element)
        markers.append(
            {
                "number": num,
                "x": float(mx) if mx is not None else cx,
                "y": float(my) if my is not None else cy,
                "description": str(diff.get("description", "")),
            }
        )

    final_elements = [el for el in elements if str(el.get("id", "")) not in removed_ids]
    return final_elements, markers
