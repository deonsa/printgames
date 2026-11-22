"""Core layout, theming, vector art, and PDF rendering utilities for PrintGames."""

from .icons import ICONS, icon_names, render_icon_svg
from .pages import PAGE_SIZES, PageSpec, resolve_page_spec
from .themes import THEMES, ThemeSpec, build_base_css, get_theme

__all__ = [
    "ICONS",
    "PAGE_SIZES",
    "THEMES",
    "PageSpec",
    "ThemeSpec",
    "build_base_css",
    "get_theme",
    "icon_names",
    "render_icon_svg",
    "resolve_page_spec",
]
