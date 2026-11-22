"""Built-in library of 70+ crisp, uniform vector SVG icons (24x24 viewBox).

These icons power Rebus puzzles, Mazes (start/finish markers), Spot the Difference,
Hidden Pictures (I Spy), and Mad Libs header vignettes.
"""

from __future__ import annotations

from html import escape

# Each icon is SVG inner markup designed for viewBox="0 0 24 24" with
# stroke-linecap="round" and stroke-linejoin="round".
ICONS: dict[str, str] = {
    # Celestial & Weather
    "sun": (
        '<circle cx="12" cy="12" r="4.5"/>'
        '<path d="M12 2.5v2.5M12 19v2.5M2.5 12H5M19 12h2.5M5.3 5.3l1.8 1.8M16.9 16.9l1.8 1.8M18.7 5.3l-1.8 1.8M7.1 16.9l-1.8 1.8"/>'
    ),
    "moon": '<path d="M19 14.5A7.5 7.5 0 0 1 9.5 5a7.5 7.5 0 1 0 9.5 9.5z"/>',
    "star": '<polygon points="12,2.5 14.9,8.4 21.4,9.3 16.7,13.9 17.8,20.4 12,17.3 6.2,20.4 7.3,13.9 2.6,9.3 9.1,8.4"/>',
    "cloud": '<path d="M6.5 18h11a4 4 0 0 0 .8-7.9A5.5 5.5 0 0 0 7.6 8.5 3.8 3.8 0 0 0 6.5 18z"/>',
    "rain": (
        '<path d="M6 14h11.5a3.5 3.5 0 0 0 .7-6.9A5 5 0 0 0 8.4 5.8 3.5 3.5 0 0 0 6 14z"/>'
        '<path d="M8 17.5l-1 3M12 17.5l-1 3M16 17.5l-1 3"/>'
    ),
    "lightning": '<polygon points="13.5,2 5.5,13 11.5,13 10.5,22 18.5,11 12.5,11"/>',
    "snowflake": (
        '<path d="M12 2v20M2 12h20M4.9 4.9l14.2 14.2M19.1 4.9L4.9 19.1"/>'
        '<path d="M10 4l2 2 2-2M10 20l2-2 2 2M4 10l2 2-2 2M20 10l-2 2 2 2"/>'
    ),
    "umbrella": '<path d="M3 13a9 9 0 0 1 18 0zM12 4V2.5M12 13v6a2 2 0 0 1-4 0"/>',
    "fire": '<path d="M12 2.5c2 3.5 6 5.5 6 11a6 6 0 1 1-12 0c0-2.5 1.3-4.7 3-6.5 0 2 1 3 2 3 0-3 1-5.5 1-7.5z"/>',
    "water_drop": '<path d="M12 2.5C8 8 5.5 11.2 5.5 14.8a6.5 6.5 0 0 0 13 0C18.5 11.2 16 8 12 2.5z"/>',
    "rainbow": '<path d="M3 18a9 9 0 0 1 18 0M6 18a6 6 0 0 1 12 0M9 18a3 3 0 0 1 6 0"/>',
    # Nature & Animals
    "tree": '<path d="M12 2.5L5.5 12h3L5 17.5h14L15.5 12h3zM12 17.5V22"/>',
    "flower": (
        '<circle cx="12" cy="12" r="2.6"/>'
        '<circle cx="12" cy="6.5" r="2.6"/><circle cx="12" cy="17.5" r="2.6"/>'
        '<circle cx="6.5" cy="12" r="2.6"/><circle cx="17.5" cy="12" r="2.6"/>'
    ),
    "leaf": '<path d="M19.5 4.5C11 4.5 5 9 5 18.5c9.5 0 14.5-5.5 14.5-14zM5 18.5L14 9.5"/>',
    "mushroom": '<path d="M4 13a8 8 0 0 1 16 0zM9.5 13v6.5a2.5 2.5 0 0 0 5 0V13"/>',
    "acorn": '<path d="M6 10a6 6 0 0 1 12 0zM12 4V2.5M7 10v3a5 5 0 0 0 10 0v-3M12 18v2.5"/>',
    "fish": '<path d="M19 12c-3-4.5-8-5.5-12-2.5L3 7v10l4-2.5c4 3 9 2 12-2.5z"/><circle cx="15" cy="11" r="1"/>',
    "bird": '<path d="M3.5 16c4 0 6-2 8-5.5 1.5-2.6 4.5-3.5 7-2.5l2 1-2.2 1.2c.2 4.5-3.5 8.8-9.3 8.8-2.5 0-4.2-1-5.5-3zM12 11L7 6.5"/>',
    "cat": (
        '<path d="M5 10L6 4l4 3h4l4-3 1 6a7 7 0 0 1-14 0z"/>'
        '<circle cx="9.5" cy="11.5" r="0.8"/><circle cx="14.5" cy="11.5" r="0.8"/>'
        '<path d="M11 14l1 1 1-1M3 13h3M18 13h3M3.5 15.5L6.5 14.5M20.5 15.5l-3-1"/>'
    ),
    "dog": (
        '<path d="M7 9a5 5 0 0 1 10 0v5a5 5 0 0 1-10 0z"/>'
        '<path d="M7 7L3.5 11.5a2 2 0 0 0 3 2.5M17 7l3.5 4.5a2 2 0 0 1-3 2.5"/>'
        '<circle cx="10" cy="10.5" r="0.8"/><circle cx="14" cy="10.5" r="0.8"/>'
        '<path d="M11 13.5h2l-1 1.3z"/>'
    ),
    "bee": (
        '<ellipse cx="12" cy="13.5" rx="5.5" ry="4"/>'
        '<path d="M9.5 9.8v7.4M12 9.5v8M14.5 9.8v7.4"/>'
        '<path d="M10 9.5C8 5 5 6 7 9.5M14 9.5C16 5 19 6 17 9.5M17.5 13.5h2"/>'
    ),
    "butterfly": (
        '<path d="M12 6v12M12 10C9 5 3.5 5.5 4 10c.3 2.5 3.5 3 8 2M12 10c3-5 8.5-4.5 8 0-.3 2.5-3.5 3-8 2"/>'
        '<path d="M12 12c-4 .5-6.5 3-5.5 5.5 1 2 4.5 1 5.5-2.5M12 12c4 .5 6.5 3 5.5 5.5-1 2-4.5 1-5.5-2.5"/>'
        '<path d="M12 6l-1.8-2.5M12 6l1.8-2.5"/>'
    ),
    "shell": '<path d="M12 20c-6 0-9-4.5-9-9a9 9 0 0 1 18 0c0 4.5-3 9-9 9zM12 20V3M12 20L6 6M12 20l6-14M12 20L3.5 11.5M12 20l8.5-8.5"/>',
    "paw": (
        '<ellipse cx="12" cy="15.5" rx="4.2" ry="3.2"/>'
        '<circle cx="7" cy="10.5" r="1.6"/><circle cx="10.2" cy="8" r="1.6"/>'
        '<circle cx="13.8" cy="8" r="1.6"/><circle cx="17" cy="10.5" r="1.6"/>'
    ),
    "owl": (
        '<path d="M6 9a6 6 0 0 1 12 0v6a6 6 0 0 1-12 0zM6 5l2.5 2M18 5l-2.5 2"/>'
        '<circle cx="9.5" cy="10" r="2"/><circle cx="14.5" cy="10" r="2"/>'
        '<path d="M11 13l1 1.5 1-1.5M9.5 21v-1.5M14.5 21v-1.5"/>'
    ),
    # Food & Everyday Objects
    "apple": '<path d="M12 7.5c-2.5-2-6.5-.5-6.5 4.2 0 4.8 3 8.8 5.2 8.8 1 0 1.3-.6 1.3-.6s.3.6 1.3.6c2.2 0 5.2-4 5.2-8.8 0-4.7-4-6.2-6.5-4.2zM12 7.5C12 5 13.5 3.5 15.5 3"/>',
    "cup": '<path d="M4.5 8h11v7a4.5 4.5 0 0 1-4.5 4.5H9A4.5 4.5 0 0 1 4.5 15V8zM15.5 9.5h2.5a2.5 2.5 0 0 1 0 5h-2.5M8 4.5v1.5M11.5 4.5v1.5"/>',
    "cake": '<path d="M4 13h16v7H4zM4 16.5c2 1 3.5-1 5.5 0s3.5-1 5.5 0 3.5-1 5 0M8 13V9.5M12 13V9.5M16 13V9.5M8 7v.5M12 7v.5M16 7v.5"/>',
    "ice_cream": '<path d="M8.5 12h7L12 21.5z"/><path d="M7.5 12a4.5 4.5 0 0 1 9 0"/><circle cx="12" cy="5.5" r="2.2"/>',
    "key": '<circle cx="8" cy="12" r="4"/><path d="M12 12h9M17.5 12v3M20 12v2.2"/>',
    "lock": '<rect x="5" y="10.5" width="14" height="10" rx="2"/><path d="M8.5 10.5V7.5a3.5 3.5 0 0 1 7 0v3"/>',
    "crown": '<polygon points="3,18 4.5,7 9,12 12,5.5 15,12 19.5,7 21,18"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 6.5V12l3.8 2.2"/>',
    "hourglass": '<path d="M6 3h12M6 21h12M7.5 3v3.5L12 12l4.5-5.5V3M7.5 21v-3.5L12 12l4.5 5.5V21"/>',
    "book": '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v17H6.5A2.5 2.5 0 0 0 4 22V5.5zM4 18.5A2.5 2.5 0 0 1 6.5 16H20"/>',
    "pencil": '<path d="M4 20l4-1L19.5 7.5 16.5 4.5 5 16l-1 4zM14.5 6.5l3 3"/>',
    "scissors": '<circle cx="6.5" cy="7.5" r="2.5"/><circle cx="6.5" cy="16.5" r="2.5"/><path d="M8.6 9.2L19.5 17M8.6 14.8L19.5 7"/>',
    "magnifying_glass": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/>',
    "lightbulb": '<path d="M9 18h6M10 21h4M12 3a6.5 6.5 0 0 0-3.5 12v2h7v-2A6.5 6.5 0 0 0 12 3z"/>',
    "bell": '<path d="M18 16H6l1.5-2.5V10a4.5 4.5 0 0 1 9 0v3.5L18 16zM10 18.5a2 2 0 0 0 4 0"/>',
    "music": '<path d="M9 18V6l11-2v12"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>',
    "gift": '<rect x="4" y="9" width="16" height="12" rx="1"/><path d="M3 9h18M12 9v12M12 9c-2-3.5-5.5-3.5-5-1s3 1 5 1c2 0 4.5 1.5 5-1s-3-2.5-5 1z"/>',
    "diamond": '<polygon points="12,3 20,9.5 12,21 4,9.5"/><path d="M4 9.5h16M8.5 9.5L12 3l3.5 6.5L12 21z"/>',
    "glasses": '<circle cx="7" cy="13" r="3.5"/><circle cx="17" cy="13" r="3.5"/><path d="M10.5 13h3M3.5 12L5 7.5M20.5 12L19 7.5"/>',
    "hat": '<path d="M3 17h18M6.5 17l1.5-9h8l1.5 9M7.2 13.5h9.6"/>',
    "balloon": '<path d="M12 3a6 6.8 0 1 0 0 13.6A6 6.8 0 1 0 12 3zM12 16.6l-1.2 1.8h2.4zM12 18.4c0 2-1.5 2.5-1.5 3.6"/>',
    "envelope": '<rect x="3" y="5.5" width="18" height="13" rx="1.5"/><path d="M3.5 6.5L12 13l8.5-6.5"/>',
    "camera": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7l1.5-2.5h5L16 7"/><circle cx="12" cy="13.5" r="3.2"/>',
    "lantern": '<path d="M9 4h6M8 7h8v11H8zM9 21h6M12 4v3M12 18v3M12 10.5v4"/>',
    # Body, Symbols & Emotions
    "heart": '<path d="M12 20.5C6.5 16.2 3 13 3 8.8A4.8 4.8 0 0 1 12 6a4.8 4.8 0 0 1 9 2.8c0 4.2-3.5 7.4-9 11.7z"/>',
    "eye": '<path d="M2.5 12S6 6 12 6s9.5 6 9.5 6-3.5 6-9.5 6S2.5 12 2.5 12z"/><circle cx="12" cy="12" r="2.8"/>',
    "hand": '<path d="M7 13V6.5a1.2 1.2 0 0 1 2.4 0V11M9.4 11V5a1.2 1.2 0 0 1 2.4 0v6M11.8 11V5.5a1.2 1.2 0 0 1 2.4 0v5.5M14.2 11V7.5a1.2 1.2 0 0 1 2.4 0V15a5 5 0 0 1-5 5H10a4 4 0 0 1-4-4v-3.5"/>',
    "foot": '<path d="M10 19c-2.5 0-4-1.8-4-4.2 0-3 1.5-5.8 4.5-5.8 2.5 0 4.5 2 4.5 5 0 3-2 5-5 5z"/><circle cx="7" cy="6.5" r="1"/><circle cx="9.5" cy="5.5" r="1"/><circle cx="12" cy="5.8" r="0.9"/><circle cx="14.2" cy="6.8" r="0.8"/>',
    "smile": '<circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="0.9"/><circle cx="15" cy="10" r="0.9"/><path d="M8.5 14.5a4.2 4.2 0 0 0 7 0"/>',
    "skull": '<path d="M6 12a6 6 0 1 1 12 0c0 2.4-1.2 4-2 5v2.5H8V17c-.8-1-2-2.6-2-5z"/><circle cx="9.5" cy="11.5" r="1.4"/><circle cx="14.5" cy="11.5" r="1.4"/><path d="M10.5 19.5V17M13.5 19.5V17"/>',
    "ghost": '<path d="M6 20V11a6 6 0 0 1 12 0v9l-2-1.8L14 20l-2-1.8L10 20l-2-1.8z"/><circle cx="9.5" cy="11" r="0.9"/><circle cx="14.5" cy="11" r="0.9"/>',
    # Places, Travel & Adventure
    "house": '<path d="M3 11.5L12 4l9 7.5M5.5 10v10h13V10M10 20v-5.5h4V20"/>',
    "castle": '<path d="M4 20V9h3v2.5h2.5V6h5v5.5H17V9h3v11zM10 20v-4.5a2 2 0 0 1 4 0V20M12 6V3.5l2.5 1L12 5.5"/>',
    "mountain": '<polygon points="2.5,19.5 9.5,6.5 14,14 16.8,10 21.5,19.5"/><path d="M7.5 10.5l2 1.2 2-1.2"/>',
    "bridge": '<path d="M2.5 15h19M5 15v4M19 15v4M5 15c2-5.5 12-5.5 14 0M9 15v-3.6M12 15v-4.1M15 15v-3.6"/>',
    "door": '<rect x="6" y="3" width="12" height="18" rx="1"/><circle cx="15" cy="12" r="0.9"/>',
    "window": '<rect x="4" y="4" width="16" height="16" rx="1"/><path d="M12 4v16M4 12h16"/>',
    "car": '<path d="M3.5 14.5h17v-3l-2.5-4.5H6L3.5 11.5z"/><circle cx="7.5" cy="16.5" r="2"/><circle cx="16.5" cy="16.5" r="2"/>',
    "boat": '<path d="M3 16h18l-2.5 4h-13zM12 16V4l6 8.5H12M12 7l-5 5.5h5"/>',
    "plane": '<path d="M21 12l-7.5-2V4.5a1.5 1.5 0 0 0-3 0V10L3 12v2l7.5-1v4.5L8 19.5V21l4-1 4 1v-1.5l-2.5-2V13l7.5 1z"/>',
    "rocket": '<path d="M12 2.5c3.5 2.5 5 6.5 5 11l-2.5 2.5h-5L7 13.5c0-4.5 1.5-8.5 5-11zM7 13.5l-3 2v3l3.5-1M17 13.5l3 2v3l-3.5-1M10 18.5l2 3 2-3"/><circle cx="12" cy="9.5" r="1.6"/>',
    "anchor": '<circle cx="12" cy="5.5" r="2"/><path d="M12 7.5v13M8 10.5h8M5 14a7 7 0 0 0 14 0"/>',
    "compass": '<circle cx="12" cy="12" r="9"/><polygon points="15.5,8.5 13.3,13.3 8.5,15.5 10.7,10.7"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/>',
    "flag": '<path d="M6 21V4h12l-2.5 4.5L18 13H6"/>',
    "trophy": '<path d="M7 4h10v5a5 5 0 0 1-10 0V4zM7 6H4a2.5 2.5 0 0 0 2.5 4.5M17 6h3a2.5 2.5 0 0 1-2.5 4.5M12 14v5M8.5 20h7"/>',
    "sword": '<path d="M19.5 4.5L9 15M15.5 4.5h4v4M6.5 12.5l5 5M5 19l3-3"/>',
    "shield": '<path d="M12 3l7.5 3v6c0 4.5-3.2 7.6-7.5 9-4.3-1.4-7.5-4.5-7.5-9V6z"/>',
    "treasure": '<rect x="3.5" y="9" width="17" height="11" rx="1.5"/><path d="M3.5 9a8.5 5 0 0 1 17 0M3.5 13h17M10.5 11.5h3v3h-3z"/>',
    # Arrows & Math / Rebus Operators
    "arrow_up": '<path d="M12 20V4M6 10l6-6 6 6"/>',
    "arrow_down": '<path d="M12 4v16M6 14l6 6 6-6"/>',
    "arrow_left": '<path d="M20 12H4M10 6l-6 6 6 6"/>',
    "arrow_right": '<path d="M4 12h16M14 6l6 6-6 6"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "minus": '<path d="M5 12h14"/>',
    "equals": '<path d="M5 9h14M5 15h14"/>',
    "times": '<path d="M6 6l12 12M18 6L6 18"/>',
    "divide": '<path d="M5 12h14"/><circle cx="12" cy="7" r="1.2"/><circle cx="12" cy="17" r="1.2"/>',
}


def icon_names() -> list[str]:
    return sorted(ICONS.keys())


def render_icon_svg(
    name: str,
    *,
    x: float = 0.0,
    y: float = 0.0,
    size: float = 24.0,
    stroke: str = "currentColor",
    fill: str = "none",
    stroke_width: float = 1.8,
    rotate: float = 0.0,
    flip_x: bool = False,
    opacity: float = 1.0,
    standalone: bool = False,
) -> str:
    """Render a named icon either as a positioned SVG <g> or standalone <svg>."""
    key = name.strip().lower().replace(" ", "_").replace("-", "_")
    markup = ICONS.get(key)
    if markup is None:
        raise ValueError(
            f"Unknown icon '{name}'. Use list_capabilities or printgames://icons for valid names."
        )

    if standalone:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
            f'width="{size:.1f}" height="{size:.1f}" fill="{escape(fill)}" '
            f'stroke="{escape(stroke)}" stroke-width="{stroke_width:.2f}" '
            f'stroke-linecap="round" stroke-linejoin="round" opacity="{opacity:.2f}">'
            f"{markup}</svg>"
        )

    scale = size / 24.0
    transforms: list[str] = [f"translate({x:.2f},{y:.2f})"]
    if rotate:
        transforms.append(f"rotate({rotate:.2f})")
    sx = -scale if flip_x else scale
    transforms.append(f"scale({sx:.4f},{scale:.4f})")
    transforms.append("translate(-12,-12)")
    t_attr = " ".join(transforms)
    sw = stroke_width / max(scale, 0.25)
    return (
        f'<g transform="{t_attr}" fill="{escape(fill)}" stroke="{escape(stroke)}" '
        f'stroke-width="{sw:.2f}" stroke-linecap="round" stroke-linejoin="round" '
        f'opacity="{opacity:.2f}">{markup}</g>'
    )
