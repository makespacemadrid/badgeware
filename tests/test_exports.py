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


def test_render_svg_applies_selected_limited_ink_filter(monkeypatch):
    monkeypatch.setattr("tshirt_templates.exports._fetch_asset", lambda _badge: b"<svg></svg>")
    badge = Badge("badge.svg", "Badge", "badge.svg", "/static/demo-badge.svg", ".svg")
    layout = PanelLayout("front", 0, 0, 100, 100, [Placement(badge.id, 10, 10, 20, 20)])

    yellow_black = render_svg([badge], (100, 100), [layout], color_mode="yellow_black")
    black_only = render_svg([badge], (100, 100), [layout], color_mode="black_only")

    assert b'filter="url(#limited-ink)"' in yellow_black
    assert b'tableValues="0 1"' in yellow_black
    assert b"<feComposite" in black_only
