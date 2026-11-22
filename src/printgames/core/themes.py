"""Publication-grade visual themes and print-exact CSS styling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .pages import PageSpec

ThemeName = Literal[
    "editorial_classic",
    "botanical_ink",
    "playful_studio",
    "vintage_press",
    "clean_minimal",
    "ocean_breeze",
]


@dataclass(frozen=True)
class ThemeSpec:
    name: str
    label: str
    description: str
    paper: str
    ink: str
    ink_muted: str
    accent: str
    accent_soft: str
    accent_2: str
    border: str
    border_strong: str
    panel_bg: str
    answer_highlight: str
    font_display: str
    font_body: str
    font_mono: str


THEMES: dict[str, ThemeSpec] = {
    "editorial_classic": ThemeSpec(
        name="editorial_classic",
        label="Editorial Classic",
        description="Refined magazine puzzle press: crisp charcoal ink, terracotta crimson accent, warm ivory panels.",
        paper="#FFFFFF",
        ink="#1F2421",
        ink_muted="#5C635F",
        accent="#B54434",
        accent_soft="#F9ECE9",
        accent_2="#2B5B6C",
        border="#D5CFC5",
        border_strong="#2C312E",
        panel_bg="#FAF7F2",
        answer_highlight="#D9483B",
        font_display="'Noto Serif Display', 'Noto Serif', 'P052', Georgia, serif",
        font_body="'Lato', 'Noto Sans', 'Liberation Sans', sans-serif",
        font_mono="'Ubuntu Mono', 'DejaVu Sans Mono', monospace",
    ),
    "botanical_ink": ThemeSpec(
        name="botanical_ink",
        label="Botanical Ink",
        description="Serene heritage print: deep forest green ink, sage accents, soft meadow cream panels.",
        paper="#FFFFFF",
        ink="#1A3329",
        ink_muted="#526B60",
        accent="#3C7A5E",
        accent_soft="#EAF3EE",
        accent_2="#B67A3D",
        border="#C8D8CF",
        border_strong="#224436",
        panel_bg="#F5F9F6",
        answer_highlight="#C8533B",
        font_display="'P052', 'Noto Serif', Georgia, serif",
        font_body="'Lato', 'Noto Sans', sans-serif",
        font_mono="'Ubuntu Mono', 'Liberation Mono', monospace",
    ),
    "playful_studio": ThemeSpec(
        name="playful_studio",
        label="Playful Studio",
        description="Vibrant family & kids activity book: friendly ink navy, coral and sunny amber highlights.",
        paper="#FFFFFF",
        ink="#1D2B44",
        ink_muted="#566785",
        accent="#E05A47",
        accent_soft="#FEF0ED",
        accent_2="#2D7DD2",
        border="#C9D6EA",
        border_strong="#263B5E",
        panel_bg="#F5F8FD",
        answer_highlight="#E05A47",
        font_display="'Ubuntu', 'Lato', 'Noto Sans', sans-serif",
        font_body="'Lato', 'Ubuntu', 'Noto Sans', sans-serif",
        font_mono="'Ubuntu Mono', 'DejaVu Sans Mono', monospace",
    ),
    "vintage_press": ThemeSpec(
        name="vintage_press",
        label="Vintage Press",
        description="Nostalgic Sunday newspaper & broadsheet feel: warm espresso ink and antique ochre brass.",
        paper="#FFFFFF",
        ink="#2B2118",
        ink_muted="#6B5C4E",
        accent="#9C6B23",
        accent_soft="#F7F0E2",
        accent_2="#6D3B32",
        border="#D8CCB8",
        border_strong="#3E3023",
        panel_bg="#FAF6EE",
        answer_highlight="#B33B2E",
        font_display="'C059', 'URW Bookman', 'Noto Serif', Georgia, serif",
        font_body="'Bitstream Charter', 'Noto Serif', Georgia, serif",
        font_mono="'Liberation Mono', 'DejaVu Sans Mono', monospace",
    ),
    "clean_minimal": ThemeSpec(
        name="clean_minimal",
        label="Clean Minimal",
        description="Swiss typographic precision: jet black ink, cool slate grays, ultra-clean geometric rules.",
        paper="#FFFFFF",
        ink="#141619",
        ink_muted="#5A626E",
        accent="#2F3B4C",
        accent_soft="#EEF1F5",
        accent_2="#586B82",
        border="#CFD5DD",
        border_strong="#141619",
        panel_bg="#F7F8FA",
        answer_highlight="#C93B3B",
        font_display="'Lato', 'Noto Sans', sans-serif",
        font_body="'Lato', 'Noto Sans', sans-serif",
        font_mono="'DejaVu Sans Mono', 'Liberation Mono', monospace",
    ),
    "ocean_breeze": ThemeSpec(
        name="ocean_breeze",
        label="Ocean Breeze",
        description="Crisp maritime chart aesthetic: deep harbor slate, seafoam teal accent, misty aqua tint.",
        paper="#FFFFFF",
        ink="#13313D",
        ink_muted="#4F6D78",
        accent="#1E7B85",
        accent_soft="#E8F5F6",
        accent_2="#D16B4B",
        border="#C0D8DC",
        border_strong="#174454",
        panel_bg="#F3FAFA",
        answer_highlight="#D1493B",
        font_display="'Noto Serif', 'P052', Georgia, serif",
        font_body="'Lato', 'Noto Sans', sans-serif",
        font_mono="'Ubuntu Mono', 'DejaVu Sans Mono', monospace",
    ),
}


def get_theme(name: str = "editorial_classic", ink_saver: bool = False) -> ThemeSpec:
    theme = THEMES.get(name)
    if theme is None:
        valid = ", ".join(THEMES.keys())
        raise ValueError(f"Unknown theme '{name}'. Valid themes: {valid}")
    if not ink_saver:
        return theme
    return ThemeSpec(
        name=f"{theme.name}_inksaver",
        label=f"{theme.label} (Ink Saver)",
        description=theme.description,
        paper="#FFFFFF",
        ink="#111111",
        ink_muted="#4A4A4A",
        accent="#222222",
        accent_soft="#FFFFFF",
        accent_2="#333333",
        border="#9A9A9A",
        border_strong="#111111",
        panel_bg="#FFFFFF",
        answer_highlight="#222222",
        font_display=theme.font_display,
        font_body=theme.font_body,
        font_mono=theme.font_mono,
    )


def build_base_css(page: PageSpec, theme: ThemeSpec, *, print_layout: bool = False) -> str:
    """Build print-exact CSS locking every .page strictly to the physical page size."""
    s = page.scale
    return f"""
@page {{
  size: {page.width_mm:.2f}mm {page.height_mm:.2f}mm;
  margin: 0;
}}

* {{
  box-sizing: border-box;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}}

html, body {{
  margin: 0;
  padding: 0;
  background: #E5E7EB;
  color: {theme.ink};
  font-family: {theme.font_body};
  font-size: {10.2 * s:.2f}pt;
  line-height: 1.38;
}}

@media {"all" if print_layout else "print"} {{
  html, body {{
    background: #FFFFFF;
  }}
  .page {{
    margin: 0 !important;
    box-shadow: none !important;
  }}
}}

.page {{
  width: {page.width_mm:.2f}mm;
  height: {page.height_mm:.2f}mm;
  padding: {page.margin_mm:.2f}mm;
  background: {theme.paper};
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  page-break-after: always;
  break-after: page;
  margin: 10mm auto;
  box-shadow: 0 4px 20px rgba(0,0,0,0.14);
}}

.page:last-child {{
  page-break-after: auto;
  break-after: auto;
}}

.page-frame {{
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border: 1.4pt solid {theme.border_strong};
  border-radius: {3.0 * s:.2f}mm;
  padding: {4.2 * s:.2f}mm {5.0 * s:.2f}mm {3.4 * s:.2f}mm {5.0 * s:.2f}mm;
  position: relative;
  background: {theme.paper};
  overflow: hidden;
}}

.page-frame::before {{
  content: "";
  position: absolute;
  inset: {1.1 * s:.2f}mm;
  border: 0.5pt solid {theme.border};
  border-radius: {2.1 * s:.2f}mm;
  pointer-events: none;
}}

.page-header {{
  flex: 0 0 auto;
  position: relative;
  z-index: 1;
  margin-bottom: {2.8 * s:.2f}mm;
}}

.header-meta {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 3mm;
  margin-bottom: {1.2 * s:.2f}mm;
}}

.badge-group {{
  display: flex;
  align-items: center;
  gap: {1.8 * s:.2f}mm;
  flex-wrap: wrap;
}}

.pill {{
  display: inline-flex;
  align-items: center;
  padding: {0.6 * s:.2f}mm {2.4 * s:.2f}mm;
  border-radius: 999px;
  font-size: {6.8 * s:.2f}pt;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  background: {theme.accent_soft};
  color: {theme.accent};
  border: 0.6pt solid {theme.accent};
}}

.pill-muted {{
  background: {theme.panel_bg};
  color: {theme.ink_muted};
  border-color: {theme.border};
}}

.pill-key {{
  background: {theme.accent};
  color: #FFFFFF;
  border-color: {theme.accent};
}}

.title-row {{
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 4mm;
  border-bottom: 1.2pt solid {theme.border_strong};
  padding-bottom: {1.4 * s:.2f}mm;
}}

.game-title {{
  margin: 0;
  font-family: {theme.font_display};
  font-size: {19.5 * s:.2f}pt;
  font-weight: 700;
  line-height: 1.12;
  letter-spacing: -0.01em;
  color: {theme.ink};
}}

.game-subtitle {{
  margin: {0.6 * s:.2f}mm 0 0 0;
  font-size: {8.8 * s:.2f}pt;
  color: {theme.ink_muted};
  font-style: italic;
}}

.instructions-box {{
  margin-top: {2.0 * s:.2f}mm;
  padding: {1.8 * s:.2f}mm {2.8 * s:.2f}mm;
  background: {theme.panel_bg};
  border-left: 2.4pt solid {theme.accent};
  border-top: 0.5pt solid {theme.border};
  border-right: 0.5pt solid {theme.border};
  border-bottom: 0.5pt solid {theme.border};
  border-radius: 0 {1.4 * s:.2f}mm {1.4 * s:.2f}mm 0;
  font-size: {8.4 * s:.2f}pt;
  line-height: 1.32;
  color: {theme.ink};
}}

.instructions-label {{
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: {7.4 * s:.2f}pt;
  color: {theme.accent};
  margin-right: 1.5mm;
}}

.page-body {{
  flex: 1 1 auto;
  min-height: 0;
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}}

.page-footer {{
  flex: 0 0 auto;
  position: relative;
  z-index: 1;
  margin-top: {2.0 * s:.2f}mm;
  padding-top: {1.3 * s:.2f}mm;
  border-top: 0.6pt solid {theme.border};
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: {7.2 * s:.2f}pt;
  color: {theme.ink_muted};
}}

.section-heading {{
  font-family: {theme.font_display};
  font-size: {10.5 * s:.2f}pt;
  font-weight: 700;
  color: {theme.accent};
  letter-spacing: 0.03em;
  text-transform: uppercase;
  margin: 0 0 {1.4 * s:.2f}mm 0;
}}

.card {{
  background: {theme.paper};
  border: 0.9pt solid {theme.border};
  border-radius: {2.0 * s:.2f}mm;
  padding: {2.2 * s:.2f}mm {2.8 * s:.2f}mm;
}}

.card-tinted {{
  background: {theme.panel_bg};
  border: 0.8pt solid {theme.border};
  border-radius: {2.0 * s:.2f}mm;
  padding: {2.2 * s:.2f}mm {2.8 * s:.2f}mm;
}}

.svg-fit {{
  width: 100%;
  height: 100%;
  display: block;
}}

.answer-banner {{
  display: inline-block;
  padding: 0.5mm 2.2mm;
  background: {theme.accent};
  color: #FFFFFF;
  border-radius: 1mm;
  font-size: {7.4 * s:.2f}pt;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}

.cut-divider-h {{
  border-top: 0.9pt dashed {theme.ink_muted};
  margin: {2.2 * s:.2f}mm 0;
  position: relative;
}}

.cut-divider-v {{
  border-left: 0.9pt dashed {theme.ink_muted};
  margin: 0 {2.2 * s:.2f}mm;
}}

.mono {{
  font-family: {theme.font_mono};
}}

.player-line {{
  display: inline-flex;
  align-items: baseline;
  gap: 1.5mm;
  font-size: {8.2 * s:.2f}pt;
  color: {theme.ink_muted};
}}

.player-line span.blank {{
  display: inline-block;
  min-width: {26 * s:.1f}mm;
  border-bottom: 0.8pt solid {theme.ink};
}}
"""
