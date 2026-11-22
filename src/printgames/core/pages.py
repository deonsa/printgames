"""Physical page sizes, printable bounds, and adaptive typography scaling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PageSizeName = Literal[
    "letter",
    "a4",
    "a5",
    "half_letter",
    "kdp_6x9",
    "kdp_8x10",
    "square_8x8",
    "legal",
    "a3",
    "custom",
]

Orientation = Literal["portrait", "landscape"]


@dataclass(frozen=True)
class PagePreset:
    name: str
    label: str
    width_mm: float
    height_mm: float
    recommended_margin_mm: float
    description: str


PAGE_SIZES: dict[str, PagePreset] = {
    "letter": PagePreset(
        name="letter",
        label="US Letter (8.5 × 11 in)",
        width_mm=215.9,
        height_mm=279.4,
        recommended_margin_mm=12.7,
        description="Standard North American home & office printer sheet.",
    ),
    "a4": PagePreset(
        name="a4",
        label="ISO A4 (210 × 297 mm)",
        width_mm=210.0,
        height_mm=297.0,
        recommended_margin_mm=12.5,
        description="Standard international home & office printer sheet.",
    ),
    "a5": PagePreset(
        name="a5",
        label="ISO A5 (148 × 210 mm)",
        width_mm=148.0,
        height_mm=210.0,
        recommended_margin_mm=10.0,
        description="Compact travel puzzle booklet / half-A4 sheet.",
    ),
    "half_letter": PagePreset(
        name="half_letter",
        label="Half Letter (5.5 × 8.5 in)",
        width_mm=139.7,
        height_mm=215.9,
        recommended_margin_mm=10.0,
        description="Compact US digest / foldable booklet size.",
    ),
    "kdp_6x9": PagePreset(
        name="kdp_6x9",
        label="Trade Paperback (6 × 9 in)",
        width_mm=152.4,
        height_mm=228.6,
        recommended_margin_mm=11.0,
        description="Popular KDP / paperback puzzle book trim size.",
    ),
    "kdp_8x10": PagePreset(
        name="kdp_8x10",
        label="Activity Book (8 × 10 in)",
        width_mm=203.2,
        height_mm=254.0,
        recommended_margin_mm=12.0,
        description="Spacious children's activity and visual puzzle book trim.",
    ),
    "square_8x8": PagePreset(
        name="square_8x8",
        label="Square (8 × 8 in)",
        width_mm=203.2,
        height_mm=203.2,
        recommended_margin_mm=11.0,
        description="Balanced square format ideal for mazes, wheels, and visual art.",
    ),
    "legal": PagePreset(
        name="legal",
        label="US Legal (8.5 × 14 in)",
        width_mm=215.9,
        height_mm=355.6,
        recommended_margin_mm=13.0,
        description="Extra-tall sheet for dense word puzzles or multi-round sheets.",
    ),
    "a3": PagePreset(
        name="a3",
        label="ISO A3 (297 × 420 mm)",
        width_mm=297.0,
        height_mm=420.0,
        recommended_margin_mm=16.0,
        description="Poster-size activity sheet for tabletop group play.",
    ),
}


@dataclass(frozen=True)
class PageSpec:
    size_name: str
    label: str
    width_mm: float
    height_mm: float
    margin_mm: float
    orientation: Orientation

    @property
    def content_width_mm(self) -> float:
        return max(40.0, self.width_mm - 2.0 * self.margin_mm)

    @property
    def content_height_mm(self) -> float:
        return max(40.0, self.height_mm - 2.0 * self.margin_mm)

    @property
    def aspect_ratio(self) -> float:
        return self.content_width_mm / self.content_height_mm

    @property
    def is_compact(self) -> bool:
        return min(self.width_mm, self.height_mm) < 170.0

    @property
    def scale(self) -> float:
        """Relative typography/spacing scale compared to US Letter (215.9 x 279.4)."""
        letter_diag = (215.9**2 + 279.4**2) ** 0.5
        this_diag = (self.width_mm**2 + self.height_mm**2) ** 0.5
        ratio = this_diag / letter_diag
        return max(0.74, min(1.28, ratio))


def resolve_page_spec(
    page_size: str = "letter",
    orientation: Orientation = "portrait",
    margin_mm: float | None = None,
    custom_width_mm: float | None = None,
    custom_height_mm: float | None = None,
) -> PageSpec:
    """Resolve physical page dimensions in millimeters with orientation applied."""
    if page_size == "custom":
        if custom_width_mm is None or custom_height_mm is None:
            raise ValueError(
                "custom_width_mm and custom_height_mm are required when page_size='custom'."
            )
        if custom_width_mm < 80 or custom_height_mm < 80:
            raise ValueError("Custom page dimensions must be at least 80mm × 80mm.")
        if custom_width_mm > 600 or custom_height_mm > 600:
            raise ValueError("Custom page dimensions must not exceed 600mm × 600mm.")
        w, h = float(custom_width_mm), float(custom_height_mm)
        default_margin = max(8.0, min(16.0, min(w, h) * 0.06))
        label = f"Custom ({w:.1f} × {h:.1f} mm)"
    else:
        preset = PAGE_SIZES.get(page_size)
        if preset is None:
            valid = ", ".join([*PAGE_SIZES.keys(), "custom"])
            raise ValueError(f"Unknown page_size '{page_size}'. Valid values: {valid}")
        w, h = preset.width_mm, preset.height_mm
        default_margin = preset.recommended_margin_mm
        label = preset.label

    if orientation == "landscape" and h > w:
        w, h = h, w
    elif orientation == "portrait" and w > h and page_size != "custom":
        w, h = h, w

    final_margin = default_margin if margin_mm is None else float(margin_mm)
    max_margin = min(w, h) * 0.2
    if final_margin < 4.0 or final_margin > max_margin:
        raise ValueError(
            f"margin_mm ({final_margin}) must be between 4.0 and {max_margin:.1f} mm for this page size."
        )

    return PageSpec(
        size_name=page_size,
        label=label,
        width_mm=w,
        height_mm=h,
        margin_mm=final_margin,
        orientation=orientation,
    )
