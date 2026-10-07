import sys

import pytest
from types import SimpleNamespace

from tshirt_templates.badges import Badge
from tshirt_templates.exports import render_png, render_svg
from tshirt_templates.layout import PanelLayout, Placement


def test_svg_retains_edited_text_position_and_escapes_user_text():
    from xml.etree import ElementTree

    layout = PanelLayout("front", 0, 0, 100, 100, [])
    label = 'Ada <& "Badge"'
    content = render_svg([], (100, 100), [layout], panel_text={
        "front": label, "size": "20", "font": "courier",
        "positions": {"front": {"x": 30, "y": 20}},
    })
    text = ElementTree.fromstring(content).find(".//{http://www.w3.org/2000/svg}text")
    assert text.text == label
    assert float(text.get("x")) == 30
    assert float(text.get("y")) == 80
    assert float(text.get("font-size")) == 20


@pytest.mark.parametrize("rasterizer_available", [True, False])
def test_png_retains_labels_at_their_edited_position(monkeypatch, rasterizer_available):
    from io import BytesIO
    from PIL import Image, ImageChops

    if not rasterizer_available:
        monkeypatch.setattr("tshirt_templates.exports.importlib.util.find_spec", lambda _name: None)
    layout = PanelLayout("front", 0, 0, 72, 72, [])
    content = render_png([], (72, 72), [layout], dpi=72, panel_text={
        "front": "M", "size": 12, "positions": {"front": {"x": 36, "y": 45}},
    })
    image = Image.open(BytesIO(content)).convert("RGB")
    bounds = ImageChops.difference(image, Image.new("RGB", image.size, "white")).getbbox()
    assert bounds is not None
    left, top, right, bottom = bounds
    assert 25 <= left < right <= 47
    assert 12 <= top < bottom <= 29


def test_render_png_uses_svg_rasterizer_at_requested_dpi(monkeypatch):
    from io import BytesIO
    from PIL import Image

    calls = []
    encoded = BytesIO()
    Image.new("RGBA", (417, 417)).save(encoded, format="PNG")
    rasterizer = SimpleNamespace(svg2png=lambda **kwargs: calls.append(kwargs) or encoded.getvalue())
    monkeypatch.setattr("tshirt_templates.exports.importlib.util.find_spec", lambda name: object())
    monkeypatch.setitem(sys.modules, "cairosvg", rasterizer)
    badge = Badge("badge.svg", "Badge", "badge.svg", "/static/demo-badge.svg", ".svg")
    layout = PanelLayout("front", 0, 0, 100, 100, [Placement(badge.id, 10, 10, 20, 20)])

    content = render_png([badge], (100, 100), [layout], dpi=300)

    with Image.open(BytesIO(content)) as image:
        assert image.size == (417, 417)
        assert abs(image.info["dpi"][0] - 300) < .1
    assert calls[0]["dpi"] == 300
    assert calls[0]["output_width"] == 417
    assert calls[0]["output_height"] == 417
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


def test_render_svg_fetches_repeated_badge_once(monkeypatch):
    from io import BytesIO
    from PIL import Image

    encoded = BytesIO()
    Image.new("RGBA", (10, 10), "black").save(encoded, format="PNG")
    calls = []
    monkeypatch.setattr("tshirt_templates.exports._fetch_asset", lambda badge: calls.append(badge.id) or encoded.getvalue())
    badge = Badge("badge.png", "Badge", "badge.png", "unused", ".png")
    layout = PanelLayout("front", 0, 0, 100, 100, [Placement(badge.id, 10, 10, 20, 20), Placement(badge.id, 40, 40, 20, 20)])
    result = render_svg([badge], (100, 100), [layout], color_mode="black_only")
    assert calls == [badge.id]
    assert result.count(b"data:image/png;base64,") == 2


@pytest.mark.parametrize("rasterizer_available", [True, False])
def test_png_print_resolution_and_page_gap(monkeypatch, rasterizer_available):
    from io import BytesIO
    from PIL import Image

    if not rasterizer_available:
        monkeypatch.setattr("tshirt_templates.exports.importlib.util.find_spec", lambda _name: None)
    layouts = [PanelLayout("front", 0, 0, 100, 100, []), PanelLayout("back", 0, 0, 100, 100, [])]
    result = Image.open(BytesIO(render_png([], (72, 144), layouts, dpi=300)))
    assert result.size == (300, 1300)
    assert abs(result.info["dpi"][0] - 300) < .1
