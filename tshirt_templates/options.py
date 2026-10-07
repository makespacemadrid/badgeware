"""Request option parsing and validation for template generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping

DEFAULT_SIDES = ("front", "back")
VALID_SIDES = frozenset(DEFAULT_SIDES)
VALID_PAGE_SIZES = frozenset({"letter", "a4", "a3"})
VALID_ORIENTATIONS = frozenset({"portrait", "landscape"})
VALID_LAYOUT_MODES = frozenset(
    {
        "grid",
        "rows",
        "diagonal",
        "scatter",
        "circle",
        "spiral",
        "wave",
        "border",
        "m-pixels",
        "m-pixels-no-shrink",
    }
)
VALID_ORDER_MODES = frozenset({"selected", "alphabetical", "category"})
VALID_UNITS = frozenset({"cm", "in"})
VALID_TEXT_FONTS = frozenset({"ubuntu", "fredoka-one", "helvetica", "times", "courier", "dejavu"})
VALID_CURVE_DEVICES = frozenset({"custom", "mug", "skinny-tumbler", "canteen"})
MAX_PANEL_TEXT_LENGTH = 64
CENTIMETERS_PER_INCH = 2.54
DEFAULT_PAGE_SIZE = "a4"
DEFAULT_UNIT = "cm"
DEFAULT_BADGE_AMOUNTS = {"cm": "3.5", "in": "1.4"}
DEFAULT_SPACING_AMOUNTS = {"cm": "0.5", "in": "0.2"}
DEFAULT_PAGE_MARGIN_AMOUNTS = {"cm": "1.25", "in": "0.5"}
DEFAULT_PANEL_GAP_AMOUNTS = {"cm": "0.85", "in": "0.33"}
DEFAULT_LOGO_AMOUNTS = {"cm": "5.0", "in": "2.0"}
DEFAULT_CURVE_DEVICE = "custom"
DEFAULT_CURVE_DIAMETER_AMOUNTS = {"cm": "8.0", "in": "3.15"}
DEFAULT_TEXT_SIZE = "28"
CURVE_DEVICE_DIAMETERS = {
    "custom": DEFAULT_CURVE_DIAMETER_AMOUNTS,
    "mug": {"cm": "8.2", "in": "3.23"},
    "skinny-tumbler": {"cm": "7.3", "in": "2.87"},
    "canteen": {"cm": "9.0", "in": "3.54"},
}
BADGE_AMOUNTS = {
    "cm": frozenset(
        {
            "1.0",
            "1.5",
            "2.0",
            "2.5",
            "3.0",
            "3.5",
            "4.0",
            "4.5",
            "5.0",
            "6.0",
            "7.5",
            "10.0",
        }
    ),
    "in": frozenset(
        {
            "0.4",
            "0.6",
            "0.8",
            "1.0",
            "1.2",
            "1.4",
            "1.6",
            "1.8",
            "2.0",
            "2.5",
            "3.0",
            "4.0",
        }
    ),
}
SPACING_AMOUNTS = {
    "cm": frozenset({"0.0", "0.2", "0.5", "0.8", "1.0", "1.5", "2.0", "3.0", "4.0", "5.0"}),
    "in": frozenset(
        {"0.0", "0.1", "0.2", "0.3", "0.4", "0.6", "0.8", "1.2", "1.6", "2.0"}
    ),
}
LOGO_AMOUNTS = {
    "cm": frozenset({"2.5", "3.5", "5.0", "7.5", "10.0", "12.5", "15.0", "20.0", "25.0"}),
    "in": frozenset({"1.0", "1.4", "2.0", "3.0", "4.0", "5.0", "6.0"}),
}


@dataclass(frozen=True)
class LayoutOptions:
    """Validated options used to generate a template layout."""

    sides: list[str]
    page_size: str = DEFAULT_PAGE_SIZE
    orientation: str = "portrait"
    mode: str = "grid"
    unit: str = DEFAULT_UNIT
    badge_size: str = DEFAULT_BADGE_AMOUNTS[DEFAULT_UNIT]
    spacing: str = DEFAULT_SPACING_AMOUNTS[DEFAULT_UNIT]
    page_margin: str = DEFAULT_PAGE_MARGIN_AMOUNTS[DEFAULT_UNIT]
    panel_gap: str = DEFAULT_PANEL_GAP_AMOUNTS[DEFAULT_UNIT]
    include_logo: bool = False
    logo_sides: list[str] = field(default_factory=list)
    logo_size: str = DEFAULT_LOGO_AMOUNTS[DEFAULT_UNIT]
    front_logo_size: str = DEFAULT_LOGO_AMOUNTS[DEFAULT_UNIT]
    back_logo_size: str = DEFAULT_LOGO_AMOUNTS[DEFAULT_UNIT]
    badge_size_inches: float = 3.5 / CENTIMETERS_PER_INCH
    spacing_inches: float = 0.5 / CENTIMETERS_PER_INCH
    page_margin_inches: float = 1.25 / CENTIMETERS_PER_INCH
    panel_gap_inches: float = 0.85 / CENTIMETERS_PER_INCH
    logo_size_inches: float = 5.0 / CENTIMETERS_PER_INCH
    front_logo_size_inches: float = 5.0 / CENTIMETERS_PER_INCH
    back_logo_size_inches: float = 5.0 / CENTIMETERS_PER_INCH
    copies: int = 1
    order: str = "selected"
    mirror: bool = True
    include_print_marks: bool = False
    include_cut_lines: bool = False
    include_yellow_unifier: bool = False
    color_mode: str = "full_color"
    ink_contrast: float = 1.0
    front_text: str = ""
    back_text: str = ""
    text_font: str = "ubuntu"
    text_size: str = DEFAULT_TEXT_SIZE
    include_curve_effect: bool = False
    curve_device: str = DEFAULT_CURVE_DEVICE
    curve_diameter: str = DEFAULT_CURVE_DIAMETER_AMOUNTS[DEFAULT_UNIT]
    curve_diameter_inches: float = 8.0 / CENTIMETERS_PER_INCH


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value in {"1", "true", "on", "yes"}


def _safe_int(value: str | None, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value if value not in {None, ""} else default)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(parsed, maximum))


def _valid_choice(value: str | None, valid_choices: frozenset[str], default: str) -> str:
    return value if value in valid_choices else default


def _valid_sides(raw_sides: list[str]) -> list[str]:
    sides = [side for side in DEFAULT_SIDES if side in raw_sides]
    return sides or list(DEFAULT_SIDES)


def _selected_sides(raw_sides: list[str]) -> list[str]:
    """Return explicitly selected valid panel sides without applying defaults."""

    return [side for side in DEFAULT_SIDES if side in raw_sides]


def _unit_amount_inches(amount: str, unit: str) -> float:
    parsed = float(amount)
    if unit == "cm":
        return parsed / CENTIMETERS_PER_INCH
    return parsed


def _safe_positive_amount(
    value: str | None,
    default: str,
    minimum: float,
    maximum: float,
) -> str:
    try:
        parsed = float(value if value not in {None, ""} else default)
    except (TypeError, ValueError):
        parsed = float(default)
    parsed = max(minimum, min(parsed, maximum))
    return f"{parsed:.2f}".rstrip("0").rstrip(".")


def _safe_panel_text(value: str | None) -> str:
    """Return text safe for shirt-panel labels, keeping it short enough to fit."""

    if value is None:
        return ""
    return " ".join(value.split())[:MAX_PANEL_TEXT_LENGTH]


def _valid_unit_amount(
    value: str | None,
    valid_amounts: dict[str, frozenset[str]],
    defaults: dict[str, str],
    unit: str,
) -> str:
    default = defaults[unit]
    return _valid_choice(value, valid_amounts[unit], default)


def parse_layout_options(
    values: Mapping[str, str],
    getlist: Callable[[str], list[str]],
) -> LayoutOptions:
    """Parse request-like values into safe layout options."""

    unit = _valid_choice(values.get("unit"), VALID_UNITS, DEFAULT_UNIT)
    badge_size = _valid_unit_amount(
        values.get("badge_size"), BADGE_AMOUNTS, DEFAULT_BADGE_AMOUNTS, unit
    )
    spacing = _valid_unit_amount(
        values.get("spacing"), SPACING_AMOUNTS, DEFAULT_SPACING_AMOUNTS, unit
    )
    logo_size = _valid_unit_amount(
        values.get("logo_size"), LOGO_AMOUNTS, DEFAULT_LOGO_AMOUNTS, unit
    )
    front_logo_size = _valid_unit_amount(
        values.get("front_logo_size", logo_size), LOGO_AMOUNTS, DEFAULT_LOGO_AMOUNTS, unit
    )
    back_logo_size = _valid_unit_amount(
        values.get("back_logo_size", logo_size), LOGO_AMOUNTS, DEFAULT_LOGO_AMOUNTS, unit
    )
    page_margin = _safe_positive_amount(
        values.get("page_margin"),
        DEFAULT_PAGE_MARGIN_AMOUNTS[unit],
        0.0,
        5.0 if unit == "cm" else 2.0,
    )
    panel_gap = _safe_positive_amount(
        values.get("panel_gap"),
        DEFAULT_PANEL_GAP_AMOUNTS[unit],
        0.0,
        10.0 if unit == "cm" else 4.0,
    )
    text_size = _safe_positive_amount(values.get("text_size"), DEFAULT_TEXT_SIZE, 8.0, 72.0)
    curve_device = _valid_choice(values.get("curve_device"), VALID_CURVE_DEVICES, DEFAULT_CURVE_DEVICE)
    curve_diameter_default = CURVE_DEVICE_DIAMETERS[curve_device][unit]
    curve_diameter = _safe_positive_amount(
        values.get("curve_diameter"),
        curve_diameter_default,
        2.5 if unit == "cm" else 1.0,
        50.0 if unit == "cm" else 20.0,
    )

    selected_logo_sides = _selected_sides(getlist("logo_sides"))
    include_logo = _truthy(values.get("include_logo")) or bool(selected_logo_sides)

    return LayoutOptions(
        sides=_valid_sides(getlist("sides")),
        page_size=_valid_choice(values.get("page_size"), VALID_PAGE_SIZES, DEFAULT_PAGE_SIZE),
        orientation=_valid_choice(values.get("orientation"), VALID_ORIENTATIONS, "portrait"),
        mode=_valid_choice(values.get("mode"), VALID_LAYOUT_MODES, "grid"),
        unit=unit,
        badge_size=badge_size,
        spacing=spacing,
        page_margin=page_margin,
        panel_gap=panel_gap,
        include_logo=include_logo,
        logo_sides=selected_logo_sides or (list(DEFAULT_SIDES) if include_logo else []),
        logo_size=logo_size,
        front_logo_size=front_logo_size,
        back_logo_size=back_logo_size,
        badge_size_inches=_unit_amount_inches(badge_size, unit),
        spacing_inches=_unit_amount_inches(spacing, unit),
        page_margin_inches=_unit_amount_inches(page_margin, unit),
        panel_gap_inches=_unit_amount_inches(panel_gap, unit),
        logo_size_inches=_unit_amount_inches(logo_size, unit),
        front_logo_size_inches=_unit_amount_inches(front_logo_size, unit),
        back_logo_size_inches=_unit_amount_inches(back_logo_size, unit),
        copies=_safe_int(values.get("copies"), 1, 1, 24),
        order=_valid_choice(values.get("order"), VALID_ORDER_MODES, "selected"),
        mirror=_truthy(values.get("mirror"), default=True),
        include_print_marks=_truthy(values.get("include_print_marks")),
        include_cut_lines=_truthy(values.get("include_cut_lines")),
        include_yellow_unifier=_truthy(values.get("include_yellow_unifier")),
        color_mode=_valid_choice(
            values.get("color_mode"),
            frozenset({"full_color", "yellow_black", "black_only"}),
            "yellow_black" if _truthy(values.get("include_yellow_unifier")) else "full_color",
        ),
        ink_contrast=float(_valid_choice(str(values.get("ink_contrast", "1")), frozenset({"0.5", "1", "1.0", "1.5", "2", "2.0"}), "1")),
        front_text=_safe_panel_text(values.get("front_text")),
        back_text=_safe_panel_text(values.get("back_text")),
        text_font=_valid_choice(values.get("text_font"), VALID_TEXT_FONTS, "ubuntu"),
        text_size=text_size,
        include_curve_effect=_truthy(values.get("include_curve_effect")),
        curve_device=curve_device,
        curve_diameter=curve_diameter,
        curve_diameter_inches=_unit_amount_inches(curve_diameter, unit),
    )
