"""PDF rendering for sublimation badge templates."""

from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from math import asin, degrees, pi, sqrt
from pathlib import Path
from tempfile import NamedTemporaryFile
from types import SimpleNamespace
from xml.sax.saxutils import escape

from PIL import Image, ImageChops

from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

from .badges import Badge
from .layout import PanelLayout

PROJECT_ROOT = Path(__file__).resolve().parent.parent


FONT_FILES = {
    "ubuntu": [
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
    ],
    "dejavu": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "fredoka-one": [
        str(PROJECT_ROOT / "static" / "fonts" / "FredokaOne-Regular.ttf"),
        "/usr/share/fonts/truetype/fredoka-one/FredokaOne-Regular.ttf",
        "/usr/share/fonts/truetype/fredoka/FredokaOne-Regular.ttf",
    ],
}
BUILT_IN_FONTS = {
    "helvetica": "Helvetica-Bold",
    "times": "Times-Bold",
    "courier": "Courier-Bold",
}
REGISTERED_FONTS: dict[str, str] = {}


DEMO_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
<circle cx="100" cy="100" r="94" fill="#ffe066" stroke="#222" stroke-width="8"/>
<path d="M55 110 L88 142 L148 62" fill="none" stroke="#2f9e44" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
<text x="100" y="178" text-anchor="middle" font-family="Arial" font-size="22" font-weight="700">DEMO</text>
</svg>"""


def _fetch_asset(badge: Badge) -> bytes:
    if badge.local_path:
        return Path(badge.local_path).read_bytes()
    if badge.raw_url.startswith("/static/demo-badge.svg"):
        return DEMO_SVG
    import requests

    response = requests.get(badge.raw_url, timeout=20)
    response.raise_for_status()
    return response.content



def verify_pdf_assets(badges: list[Badge]) -> list[dict[str, str]]:
    """Return failures for badge artwork that cannot be fetched or rendered."""

    failures: list[dict[str, str]] = []
    checked_ids: set[str] = set()
    for badge in badges:
        if badge.id in checked_ids:
            continue
        checked_ids.add(badge.id)
        try:
            content = _fetch_asset(badge)
            if badge.extension == ".svg" or content.lstrip().startswith(b"<svg"):
                with NamedTemporaryFile(suffix=".svg") as svg_file:
                    svg_file.write(content)
                    svg_file.flush()
                    drawing = svg2rlg(svg_file.name)
                if not drawing:
                    raise ValueError("SVG could not be parsed for PDF rendering.")
            else:
                ImageReader(BytesIO(content)).getSize()
        except Exception as error:
            failures.append(
                {
                    "badge_id": badge.id,
                    "name": badge.name,
                    "message": str(error) or error.__class__.__name__,
                }
            )
    return failures


def preflight_assets(badges: list[Badge], print_size_inches: float = 1.35) -> list[dict[str, str]]:
    """Return actionable artwork warnings before an export is generated."""

    warnings: list[dict[str, str]] = []
    checked_ids: set[str] = set()
    for badge in badges:
        if badge.id in checked_ids:
            continue
        checked_ids.add(badge.id)
        try:
            content = _fetch_asset(badge)
            if badge.extension == ".svg" or content.lstrip().startswith(b"<svg"):
                continue
            with Image.open(BytesIO(content)) as image:
                width, height = image.size
                effective_dpi = min(width, height) / max(print_size_inches, 0.01)
                if effective_dpi < 150:
                    warnings.append({"badge_id": badge.id, "name": badge.name, "code": "low_resolution", "message": f"Effective resolution is about {effective_dpi:.0f} DPI; 150 DPI or more is recommended."})
                if "A" in image.getbands():
                    alpha = image.getchannel("A")
                    transparent = sum(1 for value in alpha.getdata() if value < 32)
                    if transparent / max(1, width * height) > 0.5:
                        warnings.append({"badge_id": badge.id, "name": badge.name, "code": "high_transparency", "message": "More than half of the artwork is transparent; verify its visible print area."})
        except Exception as error:
            warnings.append({"badge_id": badge.id, "name": badge.name, "code": "missing_asset", "message": str(error) or "Artwork could not be loaded."})
    return warnings

def _draw_svg(pdf: canvas.Canvas, content: bytes, x: float, y: float, width: float, height: float) -> None:
    with NamedTemporaryFile(suffix=".svg") as svg_file:
        svg_file.write(content)
        svg_file.flush()
        drawing = svg2rlg(svg_file.name)
    if not drawing:
        return
    scale = min(width / drawing.width, height / drawing.height)
    pdf.saveState()
    pdf.translate(x + (width - drawing.width * scale) / 2, y + (height - drawing.height * scale) / 2)
    pdf.scale(scale, scale)
    renderPDF.draw(drawing, pdf, 0, 0)
    pdf.restoreState()


def _draw_raster(pdf: canvas.Canvas, content: bytes, x: float, y: float, width: float, height: float) -> None:
    pdf.drawImage(ImageReader(BytesIO(content)), x, y, width=width, height=height, preserveAspectRatio=True, mask="auto")


def _ink_lightness(image: Image.Image) -> Image.Image:
    """Keep bright yellow ink bright, while retaining its shaded details."""

    hue, saturation, value = image.convert("HSV").split()
    yellow_hues = hue.point([255 if 25 <= level <= 53 else 0 for level in range(256)])
    saturated = saturation.point([255 if level >= 96 else 0 for level in range(256)])
    yellow = ImageChops.multiply(yellow_hues, saturated)
    return Image.composite(value, image.convert("L"), yellow)


def _artwork_white_point(lightness: Image.Image, alpha: Image.Image) -> int:
    """Lift the artwork's highlights without letting transparent pixels set its range."""

    histogram = [0] * 256
    for level, opacity in zip(lightness.getdata(), alpha.getdata()):
        histogram[level] += opacity
    total = sum(histogram)
    if not total:
        return 224
    cumulative = 0
    low = high = None
    for level, weight in enumerate(histogram):
        cumulative += weight
        if low is None and cumulative >= total * 0.05:
            low = level
        if cumulative >= total * 0.95:
            high = level
            break
    # A flat gray asset must stay gray. Stretch only an established tonal range.
    if high - low < 96:
        return 224
    return max(128, min(224, high))


@lru_cache(maxsize=16)
def _recolour_artwork(content: bytes, is_svg: bool, color_mode: str, ink_contrast: float = 1.0) -> bytes:
    """Convert artwork to the limited inks used by the selected shirt mode."""

    if color_mode == "full_color":
        return content
    if is_svg:
        import cairosvg
        from cairosvg.helpers import node_format
        from cairosvg.parser import Tree

        # Use CairoSVG's intrinsic dimensions (including physical units) and
        # constrain only the longest side, so non-square artwork keeps its shape.
        sizing = SimpleNamespace(dpi=96, font_size=16, context_width=None, context_height=None)
        width, height, _ = node_format(sizing, Tree(bytestring=content))
        dimensions = {"output_width": 1200} if width >= height else {"output_height": 1200}
        content = cairosvg.svg2png(bytestring=content, **dimensions)
    with Image.open(BytesIO(content)) as source:
        image = source.convert("RGBA")
    alpha = image.getchannel("A")
    lightness = _ink_lightness(image)
    white_point = _artwork_white_point(lightness, alpha)
    light_levels = []
    for level in range(256):
        light = max(0.0, min(1.0, (level - 32) / (white_point - 32)))
        # Symmetric contrast preserves pure black and unprinted highlights for
        # every setting, including Soft; a linear slope altered both endpoints.
        if 0 < light < 1:
            bright = light ** ink_contrast
            dark = (1 - light) ** ink_contrast
            light = bright / (bright + dark)
        light_levels.append(light)
    empty = Image.new("L", image.size, 0)
    if color_mode == "black_only":
        coverage = lightness.point([round(255 * (1 - light)) for light in light_levels])
        image = Image.merge("RGBA", (empty, empty, empty, ImageChops.multiply(alpha, coverage)))
    else:
        red = lightness.point([round(255 * light) for light in light_levels])
        green = lightness.point([round(216 * light) for light in light_levels])
        image = Image.merge("RGBA", (red, green, empty, alpha))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _draw_missing_badge(pdf: canvas.Canvas, badge: Badge, x: float, y: float, width: float, height: float) -> None:
    pdf.setStrokeColor(colors.HexColor("#cc3a3a"))
    pdf.setFillColor(colors.HexColor("#fff5f5"))
    pdf.roundRect(x, y, width, height, 8, stroke=1, fill=1)
    pdf.setFillColor(colors.HexColor("#7a1f1f"))
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawCentredString(x + width / 2, y + height / 2, escape(badge.name[:24]))


def _draw_badge(
    pdf: canvas.Canvas,
    badge: Badge,
    x: float,
    y: float,
    width: float,
    height: float,
    content: bytes | None = None,
    color_mode: str = "full_color",
    ink_contrast: float = 1.0,
) -> None:
    try:
        asset_content = _fetch_asset(badge) if content is None else content
        is_svg = badge.extension == ".svg" or asset_content.lstrip().startswith(b"<svg")
        asset_content = _recolour_artwork(asset_content, is_svg, color_mode, ink_contrast)
        if is_svg and color_mode == "full_color":
            _draw_svg(pdf, asset_content, x, y, width, height)
        else:
            _draw_raster(pdf, asset_content, x, y, width, height)
    except Exception:
        _draw_missing_badge(pdf, badge, x, y, width, height)


def _font_name(font_key: str) -> str:
    if font_key in BUILT_IN_FONTS:
        return BUILT_IN_FONTS[font_key]
    if font_key in REGISTERED_FONTS:
        return REGISTERED_FONTS[font_key]
    for font_file in FONT_FILES.get(font_key, []):
        if Path(font_file).exists():
            registered_name = f"PanelText-{font_key}"
            pdfmetrics.registerFont(TTFont(registered_name, font_file))
            REGISTERED_FONTS[font_key] = registered_name
            return registered_name
    return "Helvetica-Bold"


def _draw_cut_line(pdf: canvas.Canvas, x: float, y: float, width: float, height: float) -> None:
    """Draw a subtle dashed outline around a badge for hand cutting."""

    pdf.saveState()
    pdf.setStrokeColor(colors.HexColor("#111111"))
    pdf.setLineWidth(0.5)
    pdf.setDash(2, 2)
    pdf.roundRect(x, y, width, height, 6, stroke=1, fill=0)
    pdf.restoreState()



def _curved_placement(
    layout: PanelLayout,
    center_x: float,
    center_y: float,
    rotation: float,
    curve_settings: dict[str, float] | None,
) -> tuple[float, float, float]:
    if not curve_settings:
        return center_x, center_y, rotation
    diameter_inches = curve_settings.get("diameter_inches", 0.0)
    radius = max(36.0, diameter_inches * 72.0 / 2.0)
    panel_center_x = layout.x + layout.width / 2.0
    offset_x = max(-radius * 0.95, min(radius * 0.95, center_x - panel_center_x))
    sagitta = radius - sqrt(max(0.0, radius * radius - offset_x * offset_x))
    theta = degrees(asin(offset_x / radius))
    return center_x, center_y - sagitta, rotation + theta


def _draw_curve_guide(pdf: canvas.Canvas, layout: PanelLayout, curve_settings: dict[str, float] | None) -> None:
    if not curve_settings:
        return
    pdf.saveState()
    pdf.setStrokeColor(colors.HexColor("#2f80ed"))
    pdf.setFillColor(colors.HexColor("#2f80ed"))
    pdf.setDash(2, 4)
    pdf.setLineWidth(0.5)
    center_x = layout.x + layout.width / 2.0
    pdf.line(center_x, layout.y, center_x, layout.y + layout.height)
    pdf.setDash()
    pdf.setFont("Helvetica", 7)
    diameter = curve_settings.get("diameter_inches", 0.0)
    circumference = diameter * pi
    device = str(curve_settings.get("device", "custom")).replace("-", " ")
    pdf.drawCentredString(
        center_x,
        layout.y + 4,
        f"curve guide: {device}; diameter {diameter:.2f} in; circumference {circumference:.2f} in",
    )
    pdf.restoreState()

def _draw_panel_text(
    pdf: canvas.Canvas,
    layout: PanelLayout,
    panel_text: dict[str, str] | None,
) -> None:
    if not panel_text:
        return
    text = (panel_text.get(layout.side) or "").strip()
    if not text:
        return
    font_name = _font_name(panel_text.get("font", "ubuntu"))
    try:
        font_size = float(panel_text.get("size", 28.0))
    except (TypeError, ValueError):
        font_size = 28.0
    font_size = min(72.0, max(8.0, font_size))
    pdf.saveState()
    pdf.setFillColor(colors.HexColor("#111111"))
    pdf.setFont(font_name, font_size)
    position = (panel_text.get("positions") or {}).get(layout.side, {})
    x = float(position.get("x", layout.x + layout.width / 2))
    y = float(position.get("y", layout.y + 16))
    pdf.drawCentredString(x, y, text)
    pdf.restoreState()


def _draw_print_marks(pdf: canvas.Canvas, page_width: float, page_height: float) -> None:
    """Draw crop and registration marks around the page edges."""

    mark = 18.0
    inset = 18.0
    center_radius = 5.0
    pdf.saveState()
    pdf.setStrokeColor(colors.HexColor("#111111"))
    pdf.setLineWidth(0.6)
    pdf.setDash()
    for x, y, x_direction, y_direction in [
        (inset, inset, 1, 1),
        (page_width - inset, inset, -1, 1),
        (inset, page_height - inset, 1, -1),
        (page_width - inset, page_height - inset, -1, -1),
    ]:
        pdf.line(x, y, x + mark * x_direction, y)
        pdf.line(x, y, x, y + mark * y_direction)
    for x, y in [
        (page_width / 2, inset),
        (page_width / 2, page_height - inset),
        (inset, page_height / 2),
        (page_width - inset, page_height / 2),
    ]:
        pdf.circle(x, y, center_radius, stroke=1, fill=0)
        pdf.line(x - center_radius * 1.8, y, x + center_radius * 1.8, y)
        pdf.line(x, y - center_radius * 1.8, x, y + center_radius * 1.8)
    pdf.restoreState()



def render_calibration_pdf(
    page_size: tuple[float, float],
    unit: str = "cm",
    mirror: bool = False,
) -> bytes:
    """Render a print calibration page with ruler marks and mirror guidance."""

    buffer = BytesIO()
    page_width, page_height = page_size
    pdf = canvas.Canvas(buffer, pagesize=page_size, pageCompression=0)
    pdf.setTitle("T-shirt template print calibration page")
    pdf.setSubject(f"unit={unit}; mirror={str(mirror).lower()}; print_scale=100%")

    if mirror:
        pdf.translate(page_width, 0)
        pdf.scale(-1, 1)

    pdf.setStrokeColor(colors.HexColor("#111111"))
    pdf.setFillColor(colors.HexColor("#111111"))
    pdf.setLineWidth(0.8)
    margin = 36.0
    step = 72.0 / 2.54 if unit == "cm" else 72.0
    label = "cm" if unit == "cm" else "in"

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(margin, page_height - margin, "Print calibration page")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(margin, page_height - margin - 18, "Print at 100% / actual size. Measure the rulers below before pressing transfers.")
    pdf.drawString(margin, page_height - margin - 34, "Mirror warning: sublimation transfers usually need mirrored artwork; proof/calibration pages usually do not.")

    origin_x = margin
    origin_y = margin
    ruler_length_x = page_width - 2 * margin
    ruler_length_y = page_height - 2 * margin - 72
    pdf.line(origin_x, origin_y, origin_x + ruler_length_x, origin_y)
    pdf.line(origin_x, origin_y, origin_x, origin_y + ruler_length_y)

    horizontal_marks = int(ruler_length_x // step)
    vertical_marks = int(ruler_length_y // step)
    pdf.setFont("Helvetica", 7)
    for index in range(horizontal_marks + 1):
        x = origin_x + index * step
        tick = 12 if index % 5 == 0 else 8
        pdf.line(x, origin_y, x, origin_y + tick)
        pdf.drawCentredString(x, origin_y - 12, str(index))
    for index in range(vertical_marks + 1):
        y = origin_y + index * step
        tick = 12 if index % 5 == 0 else 8
        pdf.line(origin_x, y, origin_x + tick, y)
        pdf.drawRightString(origin_x - 5, y - 2, str(index))

    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(origin_x + ruler_length_x / 2, origin_y - 28, f"Horizontal ruler ({label})")
    pdf.saveState()
    pdf.translate(origin_x - 28, origin_y + ruler_length_y / 2)
    pdf.rotate(90)
    pdf.drawCentredString(0, 0, f"Vertical ruler ({label})")
    pdf.restoreState()

    pdf.setDash(4, 3)
    pdf.roundRect(margin, margin, page_width - 2 * margin, page_height - 2 * margin, 10, stroke=1, fill=0)
    pdf.setDash()
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()

def render_pdf(
    badges: list[Badge],
    page_size: tuple[float, float],
    layouts: list[PanelLayout],
    mirror: bool = True,
    panel_text: dict[str, str] | None = None,
    print_marks: bool = False,
    cut_lines: bool = False,
    yellow_unifier: bool = False,
    color_mode: str = "full_color",
    curve_settings: dict[str, float] | None = None,
    metadata: dict[str, str] | None = None,
    one_layout_per_page: bool = False,
    ink_contrast: float = 1.0,
) -> bytes:
    """Render selected badge layouts into a PDF byte string."""

    badge_lookup = {badge.id: badge for badge in badges}
    asset_cache: dict[str, bytes | Exception] = {}
    for badge in badge_lookup.values():
        try:
            asset_cache[badge.id] = _fetch_asset(badge)
        except Exception as error:
            asset_cache[badge.id] = error
    buffer = BytesIO()
    page_width, page_height = page_size
    pdf = canvas.Canvas(buffer, pagesize=page_size)
    pdf.setTitle("T-shirt sublimation badge template")
    if metadata:
        pdf.setSubject("; ".join(f"{key}={value}" for key, value in sorted(metadata.items())))
        pdf.setKeywords(", ".join(f"{key}:{value}" for key, value in sorted(metadata.items())))

    def setup_page() -> None:
        if mirror:
            pdf.translate(page_width, 0)
            pdf.scale(-1, 1)
        if print_marks:
            _draw_print_marks(pdf, page_width, page_height)

    def draw_layout(layout: PanelLayout) -> None:
        _draw_panel_text(pdf, layout, panel_text)
        _draw_curve_guide(pdf, layout, curve_settings)

        for placement in layout.placements:
            badge = badge_lookup.get(placement.badge_id)
            if not badge:
                continue
            pdf.saveState()
            curved_x, curved_y, curved_rotation = _curved_placement(
                layout,
                placement.x + placement.width / 2,
                placement.y + placement.height / 2,
                placement.rotation,
                curve_settings,
            )
            pdf.translate(curved_x, curved_y)
            pdf.rotate(curved_rotation)
            cached_asset = asset_cache.get(badge.id)
            if isinstance(cached_asset, Exception):
                _draw_missing_badge(
                    pdf,
                    badge,
                    -placement.width / 2,
                    -placement.height / 2,
                    placement.width,
                    placement.height,
                )
            else:
                _draw_badge(
                    pdf,
                    badge,
                    -placement.width / 2,
                    -placement.height / 2,
                    placement.width,
                    placement.height,
                    cached_asset,
                    "yellow_black" if yellow_unifier and color_mode == "full_color" else color_mode,
                    **({"ink_contrast": ink_contrast} if ink_contrast != 1.0 else {}),
                )
            if cut_lines:
                _draw_cut_line(pdf, -placement.width / 2, -placement.height / 2, placement.width, placement.height)
            pdf.restoreState()

    if one_layout_per_page:
        for layout in layouts:
            setup_page()
            draw_layout(layout)
            pdf.showPage()
    else:
        setup_page()
        for layout in layouts:
            draw_layout(layout)
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()
