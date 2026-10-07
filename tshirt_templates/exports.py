"""Editable SVG and raster PNG exports for computed badge layouts."""

from __future__ import annotations

import base64
import importlib
import importlib.util
from io import BytesIO
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw

from .badges import Badge
from .layout import PanelLayout
from .pdf import _fetch_asset, _recolour_artwork


def _data_uri(badge: Badge, content: bytes) -> str:
    mime = "image/svg+xml" if badge.extension == ".svg" or content.lstrip().startswith(b"<svg") else (
        "image/png" if badge.extension == ".png" else "image/jpeg"
    )
    return f"data:{mime};base64,{base64.b64encode(content).decode('ascii')}"


def render_svg(
    badges: list[Badge], page_size: tuple[float, float], layouts: list[PanelLayout], color_mode: str = "full_color", ink_contrast: float = 1.0
) -> bytes:
    """Render all layout pages in one vertically stacked, editable SVG document."""

    page_width, page_height = page_size
    lookup = {badge.id: badge for badge in badges}
    gap = 24
    total_height = len(layouts) * page_height + max(0, len(layouts) - 1) * gap
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{page_width}" height="{total_height}" viewBox="0 0 {page_width} {total_height}">'
    ]
    for index, layout in enumerate(layouts):
        offset = index * (page_height + gap)
        parts.append(f'<g id="page-{index + 1}" data-side="{escape(layout.side)}" transform="translate(0 {offset})">')
        parts.append(f'<rect width="{page_width}" height="{page_height}" fill="white"/>')
        for placement_index, placement in enumerate(layout.placements):
            badge = lookup.get(placement.badge_id)
            if not badge:
                continue
            try:
                content = _fetch_asset(badge)
                if color_mode != "full_color":
                    # CairoSVG does not implement color-matrix filters. Embed
                    # the same converted artwork used by PDF so PNG also works.
                    is_svg = badge.extension == ".svg" or content.lstrip().startswith(b"<svg")
                    content = _recolour_artwork(content, is_svg, color_mode, ink_contrast)
                    href = "data:image/png;base64," + base64.b64encode(content).decode("ascii")
                else:
                    href = _data_uri(badge, content)
            except Exception:
                continue
            cx = placement.x + placement.width / 2
            cy = placement.y + placement.height / 2
            parts.append(
                f'<image id="badge-{index}-{placement_index}" data-badge-id="{escape(badge.id)}" '
                f'x="{placement.x}" y="{page_height - placement.y - placement.height}" '
                f'width="{placement.width}" height="{placement.height}" preserveAspectRatio="xMidYMid meet" '
                f'transform="rotate({-placement.rotation} {cx} {page_height - cy})" '
                f'href="{href}"/>'
            )
        parts.append("</g>")
    parts.append("</svg>")
    return "".join(parts).encode("utf-8")


def render_png(
    badges: list[Badge], page_size: tuple[float, float], layouts: list[PanelLayout], dpi: int = 150,
    color_mode: str = "full_color", ink_contrast: float = 1.0,
) -> bytes:
    """Render a contact sheet PNG, including rasterized embedded SVG artwork."""

    svg = render_svg(badges, page_size, layouts, color_mode=color_mode, ink_contrast=ink_contrast)
    if importlib.util.find_spec("cairosvg") is not None:
        cairosvg = importlib.import_module("cairosvg")
        return cairosvg.svg2png(bytestring=svg, dpi=dpi)

    # Keep raster-only exports usable in minimal environments that have not yet
    # installed the optional SVG rasterizer from requirements.txt.
    scale = dpi / 72.0
    width = max(1, round(page_size[0] * scale))
    page_height = max(1, round(page_size[1] * scale))
    gap = max(1, round(12 * scale))
    image = Image.new("RGBA", (width, len(layouts) * page_height + max(0, len(layouts) - 1) * gap), "white")
    draw = ImageDraw.Draw(image)
    lookup = {badge.id: badge for badge in badges}
    for page_index, layout in enumerate(layouts):
        offset_y = page_index * (page_height + gap)
        for placement in layout.placements:
            badge = lookup.get(placement.badge_id)
            if not badge:
                continue
            x = round(placement.x * scale)
            y = offset_y + round((page_size[1] - placement.y - placement.height) * scale)
            target = (max(1, round(placement.width * scale)), max(1, round(placement.height * scale)))
            try:
                content = _fetch_asset(badge)
                if badge.extension == ".svg" or content.lstrip().startswith(b"<svg"):
                    raise ValueError("SVG rasterizer unavailable")
                content = _recolour_artwork(content, False, color_mode, ink_contrast)
                artwork = Image.open(BytesIO(content)).convert("RGBA")
                artwork.thumbnail(target, Image.Resampling.LANCZOS)
                if placement.rotation:
                    artwork = artwork.rotate(-placement.rotation, expand=True, resample=Image.Resampling.BICUBIC)
                image.alpha_composite(artwork, (x + (target[0] - artwork.width) // 2, y + (target[1] - artwork.height) // 2))
            except Exception:
                draw.rounded_rectangle((x, y, x + target[0], y + target[1]), radius=8, outline="#cc3a3a", width=2)
                draw.text((x + 4, y + 4), badge.name[:24], fill="#7a1f1f")
    output = BytesIO()
    image.convert("RGB").save(output, format="PNG", dpi=(dpi, dpi), optimize=True)
    return output.getvalue()
