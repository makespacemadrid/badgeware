"""Editable SVG and raster PNG exports for computed badge layouts."""

from __future__ import annotations

import base64
import importlib
import importlib.util
from io import BytesIO
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

from .badges import Badge
from .layout import PanelLayout
from .pdf import _fetch_asset, _recolour_artwork


def _data_uri(badge: Badge, content: bytes) -> str:
    mime = "image/svg+xml" if badge.extension == ".svg" or content.lstrip().startswith(b"<svg") else (
        "image/png" if badge.extension == ".png" else "image/jpeg"
    )
    return f"data:{mime};base64,{base64.b64encode(content).decode('ascii')}"


def render_svg(
    badges: list[Badge], page_size: tuple[float, float], layouts: list[PanelLayout], color_mode: str = "full_color", ink_contrast: float = 1.0,
    panel_text: dict | None = None,
) -> bytes:
    """Render all layout pages in one vertically stacked, editable SVG document."""

    page_width, page_height = page_size
    lookup = {badge.id: badge for badge in badges}
    artwork_uris: dict[str, str | None] = {}
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
            if badge.id not in artwork_uris:
                try:
                    content = _fetch_asset(badge)
                    if color_mode != "full_color":
                        # CairoSVG does not implement color-matrix filters. Embed
                        # the same converted artwork used by PDF so PNG also works.
                        is_svg = badge.extension == ".svg" or content.lstrip().startswith(b"<svg")
                        content = _recolour_artwork(content, is_svg, color_mode, ink_contrast)
                        artwork_uris[badge.id] = "data:image/png;base64," + base64.b64encode(content).decode("ascii")
                    else:
                        artwork_uris[badge.id] = _data_uri(badge, content)
                except Exception:
                    artwork_uris[badge.id] = None
            href = artwork_uris[badge.id]
            if href is None:
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
        if panel_text and panel_text.get(layout.side):
            position = panel_text.get("positions", {}).get(layout.side, {})
            x = position.get("x", layout.x + layout.width / 2)
            y = page_height - position.get("y", layout.y + 18)
            font = {"ubuntu": "Ubuntu, sans-serif", "fredoka-one": "Fredoka One, sans-serif", "helvetica": "Helvetica, sans-serif", "times": "Times, serif", "courier": "Courier, monospace", "dejavu-sans": "DejaVu Sans, sans-serif"}.get(panel_text.get("font"), "Ubuntu, sans-serif")
            parts.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-family="{font}" font-size="{float(panel_text.get("size", 28))}" font-weight="800" fill="#111">{escape(str(panel_text[layout.side]))}</text>')
        parts.append("</g>")
    parts.append("</svg>")
    return "".join(parts).encode("utf-8")


def render_png(
    badges: list[Badge], page_size: tuple[float, float], layouts: list[PanelLayout], dpi: int = 150,
    color_mode: str = "full_color", ink_contrast: float = 1.0,
    panel_text: dict | None = None,
) -> bytes:
    """Render a contact sheet PNG, including rasterized embedded SVG artwork."""

    svg = render_svg(badges, page_size, layouts, color_mode=color_mode, ink_contrast=ink_contrast, panel_text=panel_text)
    if importlib.util.find_spec("cairosvg") is not None:
        cairosvg = importlib.import_module("cairosvg")
        # SVG user units are pixels; dpi alone does not scale its unitless size.
        scale = dpi / 72.0
        total_height = len(layouts) * page_size[1] + max(0, len(layouts) - 1) * 24
        content = cairosvg.svg2png(
            bytestring=svg, dpi=dpi,
            output_width=max(1, round(page_size[0] * scale)),
            output_height=max(1, round(total_height * scale)),
        )
        # Record the physical print resolution as well as the pixel dimensions.
        with Image.open(BytesIO(content)) as rendered:
            output = BytesIO()
            rendered.save(output, format="PNG", dpi=(dpi, dpi))
            return output.getvalue()

    # Keep raster-only exports usable in minimal environments that have not yet
    # installed the optional SVG rasterizer from requirements.txt.
    scale = dpi / 72.0
    width = max(1, round(page_size[0] * scale))
    page_height = max(1, round(page_size[1] * scale))
    gap = max(1, round(24 * scale))
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
        if panel_text and panel_text.get(layout.side):
            position = panel_text.get("positions", {}).get(layout.side, {})
            x = position.get("x", layout.x + layout.width / 2) * scale
            y = offset_y + (page_size[1] - position.get("y", layout.y + 18)) * scale
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", max(1, round(float(panel_text.get("size", 28)) * scale)))
            except OSError:
                font = ImageFont.load_default()
            draw.text((x, y), str(panel_text[layout.side]), fill="#111", font=font, anchor="ms")
    output = BytesIO()
    image.convert("RGB").save(output, format="PNG", dpi=(dpi, dpi), optimize=True)
    return output.getvalue()
