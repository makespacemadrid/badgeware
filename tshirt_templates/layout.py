"""Automatic badge placement for t-shirt sublimation panels."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from math import ceil, cos, pi, radians, sin, sqrt
from random import Random

PAGE_SIZES = {
    "letter": (612.0, 792.0),
    "a4": (595.28, 841.89),
    "a3": (841.89, 1190.55),
}
PANEL_MARGIN = 36.0
POINTS_PER_INCH = 72.0


@dataclass(frozen=True)
class Placement:
    """A single badge placement in PDF points."""

    badge_id: str
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0.0


@dataclass(frozen=True)
class PanelLayout:
    """Computed layout for one print side."""

    side: str
    x: float
    y: float
    width: float
    height: float
    placements: list[Placement]


def page_size_points(page_size: str = "a4", orientation: str = "portrait") -> tuple[float, float]:
    """Return a supported PDF page size in points for the requested orientation."""

    width, height = PAGE_SIZES.get(page_size, PAGE_SIZES["a4"])
    short_side, long_side = sorted((width, height))
    if orientation == "landscape":
        return long_side, short_side
    return short_side, long_side


def expand_badges(badge_ids: list[str], copies: int) -> list[str]:
    """Repeat badge ids by copy count while keeping a stable order."""

    copies = max(1, min(copies, 24))
    return [badge_id for badge_id in badge_ids for _ in range(copies)]


def compute_panels(
    page_width: float,
    page_height: float,
    sides: list[str],
    page_margin: float = PANEL_MARGIN,
    panel_gap: float = 24.0,
    separate_side_pages: bool = False,
) -> dict[str, tuple[float, float, float, float]]:
    """Return front/back panel rectangles for the selected sides."""

    selected = [side for side in ("front", "back") if side in sides]
    if not selected:
        selected = ["front"]

    safe_margin = _clamp(page_margin, 0.0, min(page_width, page_height) / 2 - 1.0)
    content_x = safe_margin
    content_y = safe_margin
    content_width = page_width - 2 * safe_margin
    content_height = page_height - 2 * safe_margin

    if len(selected) == 1 or separate_side_pages:
        return {side: (content_x, content_y, content_width, content_height) for side in selected}

    gap = min(max(0.0, panel_gap), max(0.0, content_width - 2.0))
    panel_width = (content_width - gap) / 2
    return {
        "front": (content_x, content_y, panel_width, content_height),
        "back": (content_x + panel_width + gap, content_y, panel_width, content_height),
    }


def _grid_dimensions(
    count: int,
    panel: tuple[float, float, float, float],
    badge_size: float,
    spacing: float,
) -> tuple[int, int, int, float, float]:
    """Return grid columns, rows, visible columns, and occupied size for a spacing value."""

    _, _, width, _ = panel
    cols = max(1, int((width + spacing) // (badge_size + spacing)))
    rows = max(1, ceil(count / cols))
    actual_cols = min(cols, count)
    total_width = actual_cols * badge_size + max(0, actual_cols - 1) * spacing
    total_height = rows * badge_size + max(0, rows - 1) * spacing
    return cols, rows, actual_cols, total_width, total_height


def _grid_fits(count: int, panel: tuple[float, float, float, float], badge_size: float, spacing: float) -> bool:
    """Return whether grid placement with this spacing fits inside the panel."""

    if count <= 0:
        return True
    _, _, width, height = panel
    _, _, _, total_width, total_height = _grid_dimensions(count, panel, badge_size, spacing)
    return total_width <= width + 0.01 and total_height <= height + 0.01


def _rows_fits(count: int, panel: tuple[float, float, float, float], badge_size: float, spacing: float) -> bool:
    """Return whether staggered row placement with this spacing fits inside the panel."""

    if count <= 0:
        return True
    _, _, width, height = panel
    cols, rows, _, _, total_height = _grid_dimensions(count, panel, badge_size, spacing)
    for row in range(rows):
        row_count = min(cols, count - row * cols)
        offset = spacing * 0.5 if row % 2 else 0.0
        total_width = row_count * badge_size + max(0, row_count - 1) * spacing + offset
        if total_width > width + 0.01:
            return False
    return total_height <= height + 0.01


def _density_aware_spacing(
    ids: list[str],
    panel: tuple[float, float, float, float],
    badge_size: float,
    spacing: float,
    fits: Callable[[int, tuple[float, float, float, float], float, float], bool],
) -> float:
    """Shrink spacing just enough for dense grid-like layouts to fit a panel."""

    if not ids or spacing <= 0 or fits(len(ids), panel, badge_size, spacing):
        return spacing
    if not fits(len(ids), panel, badge_size, 0.0):
        return 0.0

    low = 0.0
    high = spacing
    for _ in range(32):
        candidate = (low + high) / 2
        if fits(len(ids), panel, badge_size, candidate):
            low = candidate
        else:
            high = candidate
    return low


def _comfortable_page_capacity(
    panel: tuple[float, float, float, float], badge_size: float, spacing: float, mode: str
) -> int:
    """Return how many requested-size badges fit without reducing spacing."""

    _, _, width, height = panel
    columns = max(1, int((width + spacing) // (badge_size + spacing)))
    rows = max(1, int((height + spacing) // (badge_size + spacing)))
    capacity = max(1, columns * rows)
    if mode == "rows":
        while capacity > 1 and not _rows_fits(capacity, panel, badge_size, spacing):
            capacity -= 1
    return capacity


def _grid_positions(
    ids: list[str],
    panel: tuple[float, float, float, float],
    badge_size: float,
    spacing: float,
) -> list[Placement]:
    x, y, width, height = panel
    count = len(ids)
    cols, rows, actual_cols, total_width, total_height = _grid_dimensions(
        count, panel, badge_size, spacing
    )
    start_x = x + max(0, (width - total_width) / 2)
    start_y = y + height - max(0, (height - total_height) / 2) - badge_size

    placements: list[Placement] = []
    for index, badge_id in enumerate(ids):
        row, col = divmod(index, cols)
        placements.append(
            Placement(
                badge_id=badge_id,
                x=start_x + col * (badge_size + spacing),
                y=start_y - row * (badge_size + spacing),
                width=badge_size,
                height=badge_size,
            )
        )
    return placements


def _rows_positions(
    ids: list[str],
    panel: tuple[float, float, float, float],
    badge_size: float,
    spacing: float,
) -> list[Placement]:
    x, y, width, height = panel
    cols = max(1, int((width + spacing) // (badge_size + spacing)))
    rows = max(1, ceil(len(ids) / cols))
    row_gap = min(badge_size + spacing * 1.5, height / rows)
    placements: list[Placement] = []
    for index, badge_id in enumerate(ids):
        row, col = divmod(index, cols)
        row_count = min(cols, len(ids) - row * cols)
        offset = spacing * 0.5 if row % 2 else 0
        total_width = row_count * badge_size + max(0, row_count - 1) * spacing + offset
        start_x = x + max(0, (width - total_width) / 2) + offset
        placement_y = y + height - (row + 1) * row_gap + (row_gap - badge_size) / 2
        placement_x = start_x + col * (badge_size + spacing)
        placements.append(
            Placement(
                badge_id,
                _clamp(placement_x, x, x + width - badge_size),
                _clamp(placement_y, y, y + height - badge_size),
                badge_size,
                badge_size,
            )
        )
    return placements


def _diagonal_positions(ids: list[str], panel: tuple[float, float, float, float], badge_size: float, spacing: float) -> list[Placement]:
    x, y, width, height = panel
    angle = -28.0
    diagonal = sqrt(width * width + height * height)
    step = max(badge_size + spacing, diagonal / max(1, len(ids)))
    center_x = x + width / 2
    center_y = y + height / 2
    start = -step * (len(ids) - 1) / 2
    placements: list[Placement] = []
    for index, badge_id in enumerate(ids):
        distance = start + index * step
        px = center_x + cos(radians(angle)) * distance - badge_size / 2
        py = center_y + sin(radians(angle)) * distance - badge_size / 2
        placements.append(
            Placement(
                badge_id,
                min(max(px, x), x + width - badge_size),
                min(max(py, y), y + height - badge_size),
                badge_size,
                badge_size,
                angle,
            )
        )
    return placements


def _clamp(value: float, minimum: float, maximum: float) -> float:
    """Keep a placement coordinate inside a panel range."""

    if maximum < minimum:
        return minimum
    return min(max(value, minimum), maximum)


def _scatter_positions(ids: list[str], panel: tuple[float, float, float, float], badge_size: float, spacing: float) -> list[Placement]:
    x, y, width, height = panel
    rng = Random("tshirt-template-scatter")
    placements: list[Placement] = []
    for badge_id in ids:
        px = x + rng.random() * max(1, width - badge_size)
        py = y + rng.random() * max(1, height - badge_size)
        rotation = rng.choice([-18, -10, -6, 0, 6, 10, 18])
        placements.append(Placement(badge_id, px, py, badge_size, badge_size, rotation))
    return placements


def _circle_positions(ids: list[str], panel: tuple[float, float, float, float], badge_size: float, spacing: float) -> list[Placement]:
    x, y, width, height = panel
    if not ids:
        return []

    center_x = x + width / 2
    center_y = y + height / 2
    radius_x = max(0.0, width / 2 - badge_size / 2 - spacing)
    radius_y = max(0.0, height / 2 - badge_size / 2 - spacing)
    if len(ids) == 1:
        return [Placement(ids[0], center_x - badge_size / 2, center_y - badge_size / 2, badge_size, badge_size)]

    placements: list[Placement] = []
    for index, badge_id in enumerate(ids):
        angle = 2 * pi * index / len(ids) - pi / 2
        px = center_x + cos(angle) * radius_x - badge_size / 2
        py = center_y + sin(angle) * radius_y - badge_size / 2
        placements.append(
            Placement(
                badge_id,
                _clamp(px, x, x + width - badge_size),
                _clamp(py, y, y + height - badge_size),
                badge_size,
                badge_size,
                angle * 180 / pi + 90,
            )
        )
    return placements


def _spiral_positions(ids: list[str], panel: tuple[float, float, float, float], badge_size: float, spacing: float) -> list[Placement]:
    x, y, width, height = panel
    if not ids:
        return []

    center_x = x + width / 2
    center_y = y + height / 2
    if len(ids) == 1:
        return [Placement(ids[0], center_x - badge_size / 2, center_y - badge_size / 2, badge_size, badge_size)]

    max_radius = max(0.0, min(width, height) / 2 - badge_size / 2 - spacing)
    turns = 1.75
    placements: list[Placement] = []
    for index, badge_id in enumerate(ids):
        progress = index / (len(ids) - 1)
        angle = turns * 2 * pi * progress - pi / 2
        radius = max_radius * progress**0.7
        px = center_x + cos(angle) * radius - badge_size / 2
        py = center_y + sin(angle) * radius - badge_size / 2
        placements.append(
            Placement(
                badge_id,
                _clamp(px, x, x + width - badge_size),
                _clamp(py, y, y + height - badge_size),
                badge_size,
                badge_size,
                angle * 180 / pi,
            )
        )
    return placements


def _wave_positions(ids: list[str], panel: tuple[float, float, float, float], badge_size: float, spacing: float) -> list[Placement]:
    x, y, width, height = panel
    if not ids:
        return []

    center_y = y + (height - badge_size) / 2
    amplitude = max(0.0, (height - badge_size) / 3 - spacing)
    if len(ids) == 1:
        return [Placement(ids[0], x + (width - badge_size) / 2, center_y, badge_size, badge_size)]

    span = max(0.0, width - badge_size)
    placements: list[Placement] = []
    for index, badge_id in enumerate(ids):
        progress = index / (len(ids) - 1)
        angle = 2 * pi * progress
        px = x + span * progress
        py = center_y + sin(angle) * amplitude
        placements.append(
            Placement(
                badge_id,
                _clamp(px, x, x + width - badge_size),
                _clamp(py, y, y + height - badge_size),
                badge_size,
                badge_size,
                cos(angle) * 14,
            )
        )
    return placements


def _border_positions(ids: list[str], panel: tuple[float, float, float, float], badge_size: float, spacing: float) -> list[Placement]:
    x, y, width, height = panel
    if not ids:
        return []

    step = badge_size + spacing
    positions: list[tuple[float, float, float]] = []

    top_y = y + height - badge_size
    bottom_y = y
    left_x = x
    right_x = x + width - badge_size

    horizontal_slots = max(1, int((width + spacing) // step))
    vertical_slots = max(0, int((height - 2 * step + spacing) // step))

    for slot in range(horizontal_slots):
        px = x + slot * step
        if px <= right_x:
            positions.append((px, top_y, 0.0))
    for slot in range(vertical_slots):
        py = top_y - (slot + 1) * step
        if py >= bottom_y + step:
            positions.append((right_x, py, 90.0))
    for slot in range(horizontal_slots):
        px = right_x - slot * step
        if px >= left_x:
            positions.append((px, bottom_y, 180.0))
    for slot in range(vertical_slots):
        py = bottom_y + (slot + 1) * step
        if py <= top_y - step:
            positions.append((left_x, py, -90.0))

    if not positions:
        positions = [(x + (width - badge_size) / 2, y + (height - badge_size) / 2, 0.0)]

    placements = []
    for index, badge_id in enumerate(ids):
        px, py, rotation = positions[index % len(positions)]
        inset = (index // len(positions)) * min(spacing, badge_size * 0.2)
        placements.append(
            Placement(
                badge_id,
                min(max(px + inset, x), x + width - badge_size),
                min(max(py + inset, y), y + height - badge_size),
                badge_size,
                badge_size,
                rotation,
            )
        )
    return placements


MIN_M_PIXEL_GRID_SIZE = 5
DENSE_M_PIXEL_BADGE_THRESHOLD = 12
DENSE_M_PIXEL_GRID_SIZE = 7


def _m_pixel_slots(cols: int, rows: int) -> list[tuple[int, int]]:
    """Return row/column slots that draw a blocky capital M."""

    midpoint = max(1, (rows - 1) // 2)
    slots: list[tuple[int, int]] = []
    for row in range(rows):
        diagonal_cols: set[int] = set()
        if row <= midpoint:
            diagonal_cols = {
                round(row * (cols - 1) / (2 * midpoint)),
                round((cols - 1) - row * (cols - 1) / (2 * midpoint)),
            }
        for col in range(cols):
            if col in {0, cols - 1} or col in diagonal_cols:
                slots.append((row, col))
    return slots


def _m_pixel_dimensions(minimum_slots: int) -> tuple[int, int, list[tuple[int, int]]]:
    """Return compact odd grid dimensions with enough M pixels."""

    rows = cols = MIN_M_PIXEL_GRID_SIZE
    slots = _m_pixel_slots(cols, rows)
    while len(slots) < minimum_slots:
        rows += 2
        cols += 2
        slots = _m_pixel_slots(cols, rows)
    return cols, rows, slots


def _m_pixel_badge_ids(ids: list[str], slots: int) -> list[str]:
    """Repeat selected badges so every M pixel receives artwork."""

    if not ids:
        return []
    return [ids[index % len(ids)] for index in range(slots)]


def _m_no_shrink_fallback_slots(count: int) -> list[tuple[int, int]]:
    """Return fixed-size M slots plus overflow slots that do not shrink badges."""

    base_cols = base_rows = MIN_M_PIXEL_GRID_SIZE
    slots = _m_pixel_slots(base_cols, base_rows)
    if count <= len(slots):
        return slots

    # Keep an empty grid lane between the fixed-size M and every overflow
    # treatment so the lines/frames read as separate accents instead of
    # touching the pixel-art letter.
    buffer_cells = 1
    top_line = -(buffer_cells + 1)
    bottom_line = base_rows + buffer_cells

    fallback_slots: list[tuple[int, int]] = []
    fallback_slots.extend((top_line, col) for col in range(base_cols))
    if count <= len(slots) + len(fallback_slots):
        return slots + fallback_slots

    fallback_slots.extend((bottom_line, col) for col in range(base_cols))
    if count <= len(slots) + len(fallback_slots):
        return slots + fallback_slots

    inner_min = -(buffer_cells + 1)
    inner_max = base_rows + buffer_cells
    inner_frame_slots = [
        (row, col)
        for row in range(inner_min, inner_max + 1)
        for col in range(inner_min, inner_max + 1)
        if row in {inner_min, inner_max} or col in {inner_min, inner_max}
    ]
    fallback_slots = inner_frame_slots
    if count <= len(slots) + len(fallback_slots):
        return slots + fallback_slots

    outer_min = inner_min - 1
    outer_max = inner_max + 1
    outer_frame_slots = [
        (row, col)
        for row in range(outer_min, outer_max + 1)
        for col in range(outer_min, outer_max + 1)
        if row in {outer_min, outer_max} or col in {outer_min, outer_max}
    ]
    fallback_slots += outer_frame_slots
    next_min = outer_min - 1
    next_max = outer_max + 1
    while len(slots) + len(fallback_slots) < count:
        fallback_slots.extend(
            (row, col)
            for row in range(next_min, next_max + 1)
            for col in range(next_min, next_max + 1)
            if row in {next_min, next_max} or col in {next_min, next_max}
        )
        next_min -= 1
        next_max += 1
    return slots + fallback_slots


def _m_pixel_no_shrink_badge_ids(ids: list[str], slots: int) -> list[str]:
    """Fill a fixed-size M, then place overflow badges once in fallback slots."""

    if not ids:
        return []
    if len(ids) <= slots:
        return _m_pixel_badge_ids(ids, slots)
    return ids[:slots]


def _scaled_spacing_for_slot_coordinates(
    slot_coordinates: list[tuple[int, int]],
    panel: tuple[float, float, float, float],
    badge_size: float,
    spacing: float,
) -> float:
    """Shrink only spacing, never badges, so fixed slot coordinates fit when possible."""

    if not slot_coordinates or spacing <= 0:
        return spacing
    _, _, width, height = panel
    rows = [row for row, _ in slot_coordinates]
    cols = [col for _, col in slot_coordinates]
    grid_cols = max(cols) - min(cols) + 1
    grid_rows = max(rows) - min(rows) + 1
    max_horizontal_spacing = (width - grid_cols * badge_size) / max(1, grid_cols - 1)
    max_vertical_spacing = (height - grid_rows * badge_size) / max(1, grid_rows - 1)
    if max_horizontal_spacing < 0 or max_vertical_spacing < 0:
        return 0.0
    return min(spacing, max_horizontal_spacing, max_vertical_spacing)


def _slot_coordinate_positions(
    ids: list[str],
    slot_coordinates: list[tuple[int, int]],
    panel: tuple[float, float, float, float],
    badge_size: float,
    spacing: float,
) -> list[Placement]:
    """Place badge ids into arbitrary integer grid coordinates centered in a panel."""

    x, y, width, height = panel
    if not ids or not slot_coordinates:
        return []

    rows = [row for row, _ in slot_coordinates]
    cols = [col for _, col in slot_coordinates]
    min_row = min(rows)
    min_col = min(cols)
    grid_cols = max(cols) - min_col + 1
    grid_rows = max(rows) - min_row + 1
    step = badge_size + spacing
    total_width = grid_cols * badge_size + max(0, grid_cols - 1) * spacing
    total_height = grid_rows * badge_size + max(0, grid_rows - 1) * spacing
    start_x = x + (width - total_width) / 2
    top_y = y + height - (height - total_height) / 2 - badge_size

    placements: list[Placement] = []
    for badge_id, (row, col) in zip(ids, slot_coordinates):
        placements.append(
            Placement(
                badge_id=badge_id,
                x=start_x + (col - min_col) * step,
                y=top_y - (row - min_row) * step,
                width=badge_size,
                height=badge_size,
            )
        )
    return placements



def _m_pixel_minimum_slots(selected_badge_count: int) -> int:
    """Return the minimum number of M pixels to draw for a selection size."""

    if selected_badge_count >= DENSE_M_PIXEL_BADGE_THRESHOLD:
        return max(
            selected_badge_count,
            len(_m_pixel_slots(DENSE_M_PIXEL_GRID_SIZE, DENSE_M_PIXEL_GRID_SIZE)),
        )
    return max(selected_badge_count, MIN_M_PIXEL_GRID_SIZE)


def _m_pixel_scaled_size_and_spacing(
    cols: int,
    rows: int,
    panel: tuple[float, float, float, float],
    badge_size: float,
    spacing: float,
) -> tuple[float, float]:
    """Return pixel badge size and spacing that keep the whole M inside a panel."""

    _, _, width, height = panel
    requested_width = cols * badge_size + max(0, cols - 1) * spacing
    requested_height = rows * badge_size + max(0, rows - 1) * spacing
    scale = min(
        1.0,
        width / requested_width if requested_width else 1.0,
        height / requested_height if requested_height else 1.0,
    )
    return badge_size * scale, spacing * scale


def _m_pixel_positions(
    ids: list[str],
    panel: tuple[float, float, float, float],
    badge_size: float,
    spacing: float,
) -> list[Placement]:
    x, y, width, height = panel
    if not ids:
        return []

    cols, rows, slots = _m_pixel_dimensions(_m_pixel_minimum_slots(len(ids)))
    pixel_size, pixel_spacing = _m_pixel_scaled_size_and_spacing(
        cols, rows, panel, badge_size, spacing
    )

    total_width = cols * pixel_size + max(0, cols - 1) * pixel_spacing
    total_height = rows * pixel_size + max(0, rows - 1) * pixel_spacing
    step = pixel_size + pixel_spacing
    start_x = x + (width - total_width) / 2
    top_y = y + height - (height - total_height) / 2 - pixel_size

    placements: list[Placement] = []
    for badge_id, (row, col) in zip(_m_pixel_badge_ids(ids, len(slots)), slots):
        placements.append(
            Placement(
                badge_id=badge_id,
                x=start_x + col * step,
                y=top_y - row * step,
                width=pixel_size,
                height=pixel_size,
            )
        )
    return placements


def _m_pixel_no_shrink_positions(
    ids: list[str],
    panel: tuple[float, float, float, float],
    badge_size: float,
    spacing: float,
) -> list[Placement]:
    """Draw a fixed-size M and move overflow badges around it instead of shrinking."""

    if not ids:
        return []

    slots = _m_no_shrink_fallback_slots(len(ids))
    base_m_slots = len(_m_pixel_slots(MIN_M_PIXEL_GRID_SIZE, MIN_M_PIXEL_GRID_SIZE))
    placement_count = min(len(slots), max(len(ids), base_m_slots))
    selected_slots = slots[:placement_count]
    placement_ids = _m_pixel_no_shrink_badge_ids(ids, placement_count)
    pixel_spacing = _scaled_spacing_for_slot_coordinates(
        selected_slots, panel, badge_size, spacing
    )
    return _slot_coordinate_positions(placement_ids, selected_slots, panel, badge_size, pixel_spacing)


def place_badges(
    badge_ids: list[str] | Mapping[str, list[str]],
    sides: list[str],
    page_size: str = "a4",
    mode: str = "grid",
    orientation: str = "portrait",
    badge_size_inches: float = 1.35,
    spacing_inches: float = 0.18,
    page_margin_inches: float = 0.5,
    panel_gap_inches: float = 24.0 / POINTS_PER_INCH,
    copies: int = 1,
    separate_side_pages: bool = False,
) -> tuple[tuple[float, float], list[PanelLayout]]:
    """Compute printable panel layouts for selected badges."""

    page_width, page_height = page_size_points(page_size, orientation)
    badge_size = max(0.35, min(badge_size_inches, 4.0)) * POINTS_PER_INCH
    spacing = max(0.0, min(spacing_inches, 2.0)) * POINTS_PER_INCH
    page_margin = max(0.0, min(page_margin_inches, 2.0)) * POINTS_PER_INCH
    panel_gap = max(0.0, min(panel_gap_inches, 4.0)) * POINTS_PER_INCH
    badges_by_side = (
        {side: list(badge_ids.get(side, [])) for side in sides}
        if isinstance(badge_ids, Mapping)
        else {side: list(badge_ids) for side in sides}
    )
    panels = compute_panels(
        page_width,
        page_height,
        sides,
        page_margin,
        panel_gap,
        separate_side_pages=separate_side_pages,
    )
    placers = {
        "grid": _grid_positions,
        "rows": _rows_positions,
        "diagonal": _diagonal_positions,
        "scatter": _scatter_positions,
        "circle": _circle_positions,
        "spiral": _spiral_positions,
        "wave": _wave_positions,
        "border": _border_positions,
        "m-pixels": _m_pixel_positions,
        "m-pixels-no-shrink": _m_pixel_no_shrink_positions,
    }
    placer = placers.get(mode, _grid_positions)

    layouts = []
    density_fitters = {"grid": _grid_fits, "rows": _rows_fits}
    for side, panel in panels.items():
        expanded_ids = expand_badges(badges_by_side.get(side, []), copies)
        paginate = separate_side_pages and mode not in {"m-pixels", "m-pixels-no-shrink"}
        capacity = _comfortable_page_capacity(panel, badge_size, spacing, mode) if paginate else max(1, len(expanded_ids))
        page_badge_ids = [expanded_ids[index : index + capacity] for index in range(0, len(expanded_ids), capacity)] or [[]]
        for page_ids in page_badge_ids:
            panel_spacing = (
                _density_aware_spacing(
                    page_ids,
                    panel,
                    badge_size,
                    spacing,
                    density_fitters[mode],
                )
                if mode in density_fitters
                else spacing
            )
            layouts.append(
                PanelLayout(side, *panel, placer(page_ids, panel, badge_size, panel_spacing))
            )
    return (page_width, page_height), layouts
