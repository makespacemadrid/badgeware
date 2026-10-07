import re
from io import BytesIO
from PIL import Image
from tshirt_templates.badges import Badge
from tshirt_templates.layout import PanelLayout, Placement
import tshirt_templates.pdf as pdf_module
from tshirt_templates.pdf import _curved_placement, preflight_assets, render_calibration_pdf, render_pdf, verify_pdf_assets


def test_preflight_warns_for_low_resolution_transparent_raster(monkeypatch):
    image = Image.new("RGBA", (32, 32), (255, 0, 0, 0))
    content = BytesIO()
    image.save(content, format="PNG")
    badge = Badge("tiny.png", "Tiny", "tiny.png", "https://example.invalid/tiny.png", ".png")
    monkeypatch.setattr(pdf_module, "_fetch_asset", lambda _badge: content.getvalue())

    warnings = preflight_assets([badge], print_size_inches=2)

    assert {warning["code"] for warning in warnings} == {"low_resolution", "high_transparency"}


def test_render_pdf_can_include_print_marks_and_metadata():
    badge = Badge(
        id="demo-badge.svg",
        name="Demo Badge",
        path="demo-badge.svg",
        raw_url="/static/demo-badge.svg",
        extension=".svg",
    )
    layout = PanelLayout(
        "front",
        20.0,
        20.0,
        160.0,
        160.0,
        [Placement(badge.id, 50.0, 50.0, 40.0, 40.0)],
    )

    content = render_pdf(
        [badge],
        (200.0, 200.0),
        [layout],
        print_marks=True,
        cut_lines=True,
        yellow_unifier=True,
        metadata={"include_cut_lines": "true", "include_print_marks": "true", "include_yellow_unifier": "true", "mode": "grid"},
    )

    assert content.startswith(b"%PDF")
    assert b"include_print_marks=true" in content
    assert b"include_cut_lines=true" in content
    assert b"include_yellow_unifier=true" in content
    assert b"mode=grid" in content
    assert b"/Subject" in content


def test_render_calibration_pdf_includes_rulers_and_warning_metadata():
    content = render_calibration_pdf((300.0, 240.0), unit="in", mirror=False)

    assert content.startswith(b"%PDF")
    assert b"Print calibration page" in content
    assert b"Mirror warning" in content
    assert b"unit=in" in content


def test_verify_pdf_assets_reports_unrenderable_badges(tmp_path):
    broken_png = tmp_path / "broken.png"
    broken_png.write_bytes(b"not a png")
    badge = Badge(
        id="upload:broken.png",
        name="Broken",
        path="uploaded/broken.png",
        raw_url="/uploads/broken.png",
        extension=".png",
        local_path=broken_png,
    )

    failures = verify_pdf_assets([badge])

    assert failures[0]["badge_id"] == badge.id
    assert failures[0]["name"] == "Broken"


def test_render_pdf_smoke_checks_page_size_and_placement_count(monkeypatch):
    badge = Badge(
        id="demo-badge.svg",
        name="Demo Badge",
        path="demo-badge.svg",
        raw_url="/static/demo-badge.svg",
        extension=".svg",
    )
    layout = PanelLayout(
        "front",
        20.0,
        20.0,
        160.0,
        160.0,
        [
            Placement(badge.id, 40.0, 45.0, 30.0, 30.0),
            Placement(badge.id, 80.0, 90.0, 30.0, 30.0),
        ],
    )
    drawn = []
    monkeypatch.setattr(pdf_module, "_draw_badge", lambda *args: drawn.append(args))

    content = render_pdf([badge], (200.0, 300.0), [layout], mirror=False)

    assert content.startswith(b"%PDF")
    assert b"/MediaBox [ 0 0 200 300 ]" in content
    assert len(drawn) == 2


def test_render_pdf_does_not_draw_panel_headers_page_numbers_or_panel_perimeter(monkeypatch):
    drawn_text = []
    drawn_rectangles = []
    original_canvas = pdf_module.canvas.Canvas

    class TrackingCanvas(original_canvas):
        def drawString(self, x, y, text):
            drawn_text.append(str(text))
            return super().drawString(x, y, text)

        def drawCentredString(self, x, y, text):
            drawn_text.append(str(text))
            return super().drawCentredString(x, y, text)

        def drawRightString(self, x, y, text):
            drawn_text.append(str(text))
            return super().drawRightString(x, y, text)

        def roundRect(self, x, y, width, height, radius, stroke=1, fill=0):
            drawn_rectangles.append((x, y, width, height, radius, stroke, fill))
            return super().roundRect(x, y, width, height, radius, stroke=stroke, fill=fill)

    monkeypatch.setattr(pdf_module.canvas, "Canvas", TrackingCanvas)

    content = render_pdf(
        [],
        (200.0, 300.0),
        [PanelLayout("front", 20.0, 20.0, 160.0, 120.0, [])],
        mirror=False,
    )

    assert content.startswith(b"%PDF")
    assert drawn_text == []
    assert drawn_rectangles == []



def test_render_pdf_uses_configured_panel_text_size(monkeypatch):
    font_sizes = []
    original_canvas = pdf_module.canvas.Canvas

    class TrackingCanvas(original_canvas):
        def setFont(self, font_name, font_size, leading=None):
            font_sizes.append(font_size)
            if leading is None:
                return super().setFont(font_name, font_size)
            return super().setFont(font_name, font_size, leading)

    monkeypatch.setattr(pdf_module.canvas, "Canvas", TrackingCanvas)

    content = render_pdf(
        [],
        (200.0, 300.0),
        [PanelLayout("front", 20.0, 20.0, 160.0, 120.0, [])],
        mirror=False,
        panel_text={"front": "Ada", "font": "ubuntu", "size": "36"},
    )

    assert content.startswith(b"%PDF")
    assert 36.0 in font_sizes

def test_legacy_yellow_unifier_recolours_badge_instead_of_drawing_overlay(monkeypatch):
    badge = Badge(
        id="demo-badge.svg",
        name="Demo Badge",
        path="demo-badge.svg",
        raw_url="/static/demo-badge.svg",
        extension=".svg",
    )
    layout = PanelLayout(
        "front",
        20.0,
        20.0,
        160.0,
        160.0,
        [Placement(badge.id, 40.0, 45.0, 30.0, 30.0)],
    )
    calls = []
    monkeypatch.setattr(pdf_module, "_draw_badge", lambda *args: calls.append(args))

    content = render_pdf([badge], (200.0, 300.0), [layout], mirror=False, yellow_unifier=True)

    assert content.startswith(b"%PDF")
    assert calls[0][-1] == "yellow_black"


def test_recolour_artwork_supports_two_ink_and_black_only_modes():
    source = Image.new("RGBA", (2, 1))
    source.putdata([(10, 10, 10, 255), (240, 240, 240, 255)])
    encoded = BytesIO()
    source.save(encoded, format="PNG")

    two_ink = Image.open(BytesIO(pdf_module._recolour_artwork(encoded.getvalue(), False, "yellow_black")))
    black_only = Image.open(BytesIO(pdf_module._recolour_artwork(encoded.getvalue(), False, "black_only")))

    assert list(two_ink.getdata()) == [(0, 0, 0, 255), (255, 216, 0, 255)]
    assert list(black_only.getdata()) == [(0, 0, 0, 255), (0, 0, 0, 0)]


def test_render_pdf_fetches_each_badge_asset_once_for_repeated_placements(monkeypatch):
    badge = Badge(
        id="demo-badge.svg",
        name="Demo Badge",
        path="demo-badge.svg",
        raw_url="/static/demo-badge.svg",
        extension=".svg",
    )
    layout = PanelLayout(
        "front",
        20.0,
        20.0,
        160.0,
        160.0,
        [
            Placement(badge.id, 40.0, 45.0, 30.0, 30.0),
            Placement(badge.id, 80.0, 90.0, 30.0, 30.0),
        ],
    )
    fetches = []
    monkeypatch.setattr(pdf_module, "_fetch_asset", lambda fetched_badge: fetches.append(fetched_badge.id) or pdf_module.DEMO_SVG)

    content = render_pdf([badge], (200.0, 300.0), [layout], mirror=False)

    assert content.startswith(b"%PDF")
    assert fetches == [badge.id]


def test_curved_placement_rotates_and_sags_from_panel_center():
    layout = PanelLayout("front", 0.0, 0.0, 200.0, 120.0, [])

    center_x, center_y, rotation = _curved_placement(
        layout,
        center_x=150.0,
        center_y=60.0,
        rotation=0.0,
        curve_settings={"diameter_inches": 3.0},
    )

    assert center_x == 150.0
    assert center_y < 60.0
    assert rotation > 0.0


def test_render_pdf_can_put_front_and_back_on_separate_pages():
    front = Badge(
        id="front.svg",
        name="Front",
        path="front.svg",
        raw_url="/static/demo-badge.svg",
        extension=".svg",
    )
    back = Badge(
        id="back.svg",
        name="Back",
        path="back.svg",
        raw_url="/static/demo-badge.svg",
        extension=".svg",
    )
    layouts = [
        PanelLayout("front", 20.0, 20.0, 160.0, 160.0, [Placement(front.id, 50.0, 50.0, 40.0, 40.0)]),
        PanelLayout("back", 20.0, 20.0, 160.0, 160.0, [Placement(back.id, 50.0, 50.0, 40.0, 40.0)]),
    ]

    content = render_pdf([front, back], (200.0, 200.0), layouts, mirror=False, one_layout_per_page=True)

    assert len(re.findall(rb"/Type\s*/Page\b", content)) == 2


def test_black_only_preserves_gray_detail_and_source_transparency():
    source = Image.new("RGBA", (6, 1))
    source.putdata([(0, 0, 0, 255), (80, 80, 80, 255), (128, 128, 128, 255),
                    (192, 192, 192, 255), (255, 255, 255, 255), (128, 128, 128, 128)])
    encoded = BytesIO()
    source.save(encoded, format="PNG")
    result = Image.open(BytesIO(pdf_module._recolour_artwork(encoded.getvalue(), False, "black_only")))
    assert list(result.getdata()) == [(0, 0, 0, 255), (0, 0, 0, 191), (0, 0, 0, 128),
                                      (0, 0, 0, 42), (0, 0, 0, 0), (0, 0, 0, 64)]


def test_yellow_black_preserves_gray_detail_and_source_transparency():
    source = Image.new("RGBA", (5, 1))
    source.putdata([(0, 0, 0, 255), (80, 80, 80, 255), (128, 128, 128, 128),
                    (192, 192, 192, 255), (255, 255, 255, 0)])
    encoded = BytesIO()
    source.save(encoded, format="PNG")
    result = Image.open(BytesIO(pdf_module._recolour_artwork(encoded.getvalue(), False, "yellow_black")))
    assert list(result.getdata()) == [(0, 0, 0, 255), (64, 54, 0, 255), (128, 108, 0, 128),
                                      (212, 180, 0, 255), (255, 216, 0, 0)]


def test_ink_contrast_changes_detail_for_both_limited_ink_modes():
    source = Image.new("RGBA", (1, 1), (80, 80, 80, 128))
    encoded = BytesIO()
    source.save(encoded, format="PNG")
    for mode in ("black_only", "yellow_black"):
        soft = Image.open(BytesIO(pdf_module._recolour_artwork(encoded.getvalue(), False, mode, 0.5))).getpixel((0, 0))
        strong = Image.open(BytesIO(pdf_module._recolour_artwork(encoded.getvalue(), False, mode, 2))).getpixel((0, 0))
        if mode == "black_only":
            assert soft[3] == 80
            assert strong[3] == 128
        else:
            assert soft == (96, 81, 0, 128)
            assert strong == (0, 0, 0, 128)
