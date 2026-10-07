import sys
from types import SimpleNamespace

from tshirt_templates.badges import Badge
from tshirt_templates.exports import render_png, render_svg
from tshirt_templates.layout import PanelLayout, Placement


def test_render_png_uses_svg_rasterizer_at_requested_dpi(monkeypatch):
    calls = []
    rasterizer = SimpleNamespace(svg2png=lambda **kwargs: calls.append(kwargs) or b"png")
    monkeypatch.setattr("tshirt_templates.exports.importlib.util.find_spec", lambda name: object())
    monkeypatch.setitem(sys.modules, "cairosvg", rasterizer)
    badge = Badge("badge.svg", "Badge", "badge.svg", "/static/demo-badge.svg", ".svg")
    layout = PanelLayout("front", 0, 0, 100, 100, [Placement(badge.id, 10, 10, 20, 20)])

    content = render_png([badge], (100, 100), [layout], dpi=300)

    assert content == b"png"
    assert calls[0]["dpi"] == 300
    assert b"data:image/svg+xml;base64," in calls[0]["bytestring"]


def test_render_svg_embeds_converted_limited_ink_artwork(monkeypatch):
    monkeypatch.setattr("tshirt_templates.exports._fetch_asset", lambda _badge: b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10" fill="gray"/></svg>')
    badge = Badge("badge.svg", "Badge", "badge.svg", "/static/demo-badge.svg", ".svg")
    layout = PanelLayout("front", 0, 0, 100, 100, [Placement(badge.id, 10, 10, 20, 20)])

    yellow_black = render_svg([badge], (100, 100), [layout], color_mode="yellow_black")
    black_only = render_svg([badge], (100, 100), [layout], color_mode="black_only")

    assert b"data:image/png;base64," in yellow_black
    assert b"<filter" not in yellow_black
    assert b"data:image/png;base64," in black_only
    assert b'filter="url(#limited-ink)"' not in black_only


def test_black_only_png_converts_artwork_without_svg_filter_support(monkeypatch):
    from io import BytesIO
    from PIL import Image

    source = Image.new("RGBA", (10, 10), (80, 80, 80, 255))
    encoded = BytesIO()
    source.save(encoded, format="PNG")
    monkeypatch.setattr("tshirt_templates.exports._fetch_asset", lambda _badge: encoded.getvalue())
    badge = Badge("gray.png", "Gray", "gray.png", "unused", ".png")
    layout = PanelLayout("front", 0, 0, 100, 100, [Placement(badge.id, 10, 10, 20, 20)])
    for rasterizer_available in (True, False):
        if not rasterizer_available:
            monkeypatch.setattr("tshirt_templates.exports.importlib.util.find_spec", lambda _name: None)
        result = Image.open(BytesIO(render_png([badge], (100, 100), [layout], color_mode="black_only")))
        # Converted black coverage on white differs from the original gray.
        red, green, blue = result.convert("RGB").getpixel((round(result.width * .2), round(result.height * .8)))
        assert red == green == blue
        assert 60 <= red <= 68


def test_yellow_black_png_converts_artwork_with_and_without_cairosvg(monkeypatch):
    from io import BytesIO
    from PIL import Image

    source = Image.new("RGBA", (10, 10), (128, 128, 128, 255))
    encoded = BytesIO()
    source.save(encoded, format="PNG")
    monkeypatch.setattr("tshirt_templates.exports._fetch_asset", lambda _badge: encoded.getvalue())
    badge = Badge("gray.png", "Gray", "gray.png", "unused", ".png")
    layout = PanelLayout("front", 0, 0, 100, 100, [Placement(badge.id, 10, 10, 20, 20)])
    for rasterizer_available in (True, False):
        if not rasterizer_available:
            monkeypatch.setattr("tshirt_templates.exports.importlib.util.find_spec", lambda _name: None)
        result = Image.open(BytesIO(render_png([badge], (100, 100), [layout], color_mode="yellow_black")))
        pixel = result.convert("RGB").getpixel((round(result.width * .2), round(result.height * .8)))
        assert pixel == (128, 108, 0)
