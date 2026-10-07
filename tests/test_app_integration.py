import pytest

pytest.importorskip("flask")

import base64
import json
import logging
import sys
from io import BytesIO
from types import SimpleNamespace

from tshirt_templates.app import avoid_locked_placement_collisions, create_app
from tshirt_templates.badges import Badge
from tshirt_templates.layout import PanelLayout, Placement


DEMO_BADGE = Badge(
    id="demo-badge.svg",
    name="Demo Badge",
    path="demo-badge.svg",
    raw_url="/static/demo-badge.svg",
    extension=".svg",
)


def _logged_events(caplog):
    return [json.loads(record.message) for record in caplog.records if record.message.startswith("{")]


def test_create_app_reads_secret_key_from_environment(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "container-secret")

    app = create_app()

    assert app.secret_key == "container-secret"


def test_index_renders_badge_picker(monkeypatch):
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: [DEMO_BADGE])
    app = create_app()

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"AutoPlot badges (&amp; other images) into t-shirts &amp; mugs" in response.data
    assert b'<html lang="es">' in response.data
    assert b'data-language-switch' in response.data
    assert b'Switch language to English' in response.data
    assert b'>English</button>' in response.data
    assert b'src="/static/i18n.js"' in response.data
    assert b"Generate front & back t-shirt badge PDF templates" not in response.data
    assert b'class="brand-mark"' in response.data
    assert b'href="https://makespacemadrid.org/assets/images/favicon.png"' in response.data
    assert b"Template workflow" in response.data
    assert b"Saved design templates" in response.data
    assert b"Save current design" in response.data
    assert b"Load selected design" in response.data
    assert b"Delete selected design" in response.data
    assert b"currentDesignTemplate" in response.data
    assert b"saveCurrentDesignTemplate" in response.data
    assert b"loadSelectedDesignTemplate" in response.data
    assert b"deleteSelectedDesignTemplate" in response.data
    assert b"side_badge_ids" in response.data
    assert b"/api/v1/templates" in response.data
    assert b"1. Page and layout" in response.data
    assert b"2. Badge size and labels" in response.data
    assert b"3. PDF output" in response.data
    assert b"Download calibration page" in response.data
    assert b"Quick print guide" not in response.data
    assert b"Mirror transfers" not in response.data
    assert b"Leave cut spacing" not in response.data
    assert b"Measure curves" not in response.data
    assert b'href="/calibration.pdf"' in response.data
    assert b"M pixel shape" in response.data
    assert b"M pixel shape (no shrink)" in response.data
    assert b"Circle wreath" in response.data
    assert b"Spiral trail" in response.data
    assert b"Wave ribbon" in response.data
    assert b"Portrait" in response.data
    assert b"Landscape" in response.data
    assert b'<option value="a4" selected>A4</option>' in response.data
    assert b"Units" in response.data
    assert b"Centimeters" in response.data
    assert b"Page margin" in response.data
    assert b"Panel gap" in response.data
    assert b"page-margin-input" in response.data
    assert b'name="page_margin" id="page-margin-input" min="0" max="5" step="0.01"' in response.data
    assert b'name="panel_gap" id="panel-gap-input" min="0" max="10" step="0.01"' in response.data
    assert b"Badge size choices start at 2.5 cm / 1 in" in response.data
    assert b"Include MakeSpace logo" not in response.data
    assert b"Logo on front" in response.data
    assert b"Logo on back" in response.data
    assert b"Badge order" in response.data
    assert b'id="badge-view-toggle"' in response.data
    assert b'aria-controls="badge-grid"' in response.data
    assert b"Show text rows" in response.data
    assert b"badgeware-badge-view" in response.data
    assert b"Badges are selected by default for both sides, except badge-template.png" in response.data
    assert b"selected-badge-count" in response.data
    assert b"both-badge-count" in response.data
    assert b"side-selection-notice" in response.data
    assert b"visible-badge-count" in response.data
    assert b"Circumference: about" in response.data
    assert b"Search badges" in response.data
    assert b"Show assignment" in response.data
    assert b"All assignments" in response.data
    assert b"Reset filters" in response.data
    assert b"Skip badge list and continue to actions" in response.data
    assert b'id="badge-picker-help"' in response.data
    assert b'aria-describedby="badge-picker-help"' in response.data
    assert b'id="template-actions"' in response.data
    assert b"Select visible" in response.data
    assert b"Front only" in response.data
    assert b"Back only" in response.data
    assert b"Clear visible" in response.data
    assert b'draggable="true"' in response.data
    assert b'data-category="uncategorized"' in response.data
    assert b"Front text" in response.data
    assert b"Back text" in response.data
    assert b"Text size" in response.data
    assert b'id="text-size-input" min="8" max="72" step="1" value="28"' in response.data
    assert b"Font for front/back panel labels." in response.data
    assert b'class="info-hint"' in response.data
    assert b'<summary aria-label="More information">i</summary>' in response.data
    assert "ⓘ".encode() not in response.data
    assert response.data.find(b"Upload badge artwork") < response.data.find(b"Template options")
    assert response.data.find(b"Optional: mug/canteen curved adapter effect") < response.data.find(b"3. PDF output")
    assert b"Ubuntu" in response.data
    assert b"Alphabetical" in response.data
    assert b"By category" in response.data
    assert b'name="mirror" value="off"' in response.data
    assert b"Add crop and registration marks" in response.data
    assert b'name="include_print_marks" value="off"' in response.data
    assert b"Add badge cut-line outlines" in response.data
    assert b'name="include_cut_lines" value="off"' in response.data
    assert b"Replace colours with yellow &amp; black" in response.data
    assert b"Black only (for yellow shirts)" in response.data
    assert b'name="color_mode"' in response.data
    assert b"Optional: mug/canteen curved adapter effect" in response.data
    assert b"Adapter math" in response.data
    assert b"Curve diameter" in response.data
    assert b'name="curve_diameter" id="curve-diameter-input" min="2.5" max="50" step="0.01"' in response.data
    assert b"normalizeNumberInput" in response.data
    assert b"curveDiameterInput.min = unit === 'cm' ? '2.5' : '1'" in response.data
    assert b"Demo Badge" in response.data



def test_index_leaves_badge_template_manual_only(monkeypatch):
    template_badge = Badge(
        id="badge-template.png",
        name="Badge Template",
        path="badge-template.png",
        raw_url="/static/badge-template.png",
        extension=".png",
    )
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: [DEMO_BADGE, template_badge])
    app = create_app()

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b'id="front-badge-count">1</span>' in response.data
    assert b'id="back-badge-count">1</span>' in response.data
    assert b'data-path="badge-template.png" data-category="uncategorized" data-manual-only="true"' in response.data
    template_card = response.data.split(b'data-path="badge-template.png"', 1)[1].split(b'</article>', 1)[0]
    assert b'value="badge-template.png"' in template_card
    assert b'checked' not in template_card
    assert b'Not printed' in template_card
    assert b"card.dataset.manualOnly === 'true'" in response.data

def test_index_renders_delete_button_for_uploaded_badges(monkeypatch, tmp_path):
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: [])
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    uploaded = tmp_path / "abc-team.svg"
    uploaded.write_bytes(b"<svg></svg>")

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"Replace upload" in response.data
    assert b"Delete upload" in response.data
    assert b'name="replace_upload" value="abc-team.svg"' in response.data
    assert b'name="delete_upload" value="abc-team.svg"' in response.data


def test_browser_replace_upload_route_updates_file(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    uploaded = tmp_path / "abc-team.svg"
    uploaded.write_bytes(b"<svg>old</svg>")

    response = app.test_client().post(
        "/uploads/replace",
        data={
            "replace_upload": uploaded.name,
            "replacement_upload": (BytesIO(b"<svg>new</svg>"), "new.svg"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    assert uploaded.read_bytes() == b"<svg>new</svg>"


def test_browser_delete_upload_route_removes_file(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    uploaded = tmp_path / "abc-team.svg"
    uploaded.write_bytes(b"<svg></svg>")

    response = app.test_client().post("/uploads/delete", data={"delete_upload": uploaded.name})

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    assert not uploaded.exists()


def test_preview_shows_upload_dimension_warnings(monkeypatch, tmp_path):
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    response = app.test_client().post(
        "/preview",
        data={
            "badges": [DEMO_BADGE.id],
            "uploads": (BytesIO(b'<svg viewBox="0 0 32 32"></svg>'), "tiny.svg"),
            "sides": ["front"],
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Upload notices" in response.data
    assert b"32" in response.data


def test_preview_renders_selected_layout(monkeypatch):
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()

    response = app.test_client().post(
        "/preview",
        data={
            "badges": [DEMO_BADGE.id],
            "sides": ["front", "back"],
            "mode": "grid",
            "page_size": "letter",
            "orientation": "landscape",
            "unit": "in",
            "badge_size": "1.2",
            "spacing": "0.2",
            "page_margin": "0.4",
            "panel_gap": "0.3",
            "copies": "2",
            "front_text": "Ada",
            "back_text": "MakeSpace",
            "text_font": "dejavu",
            "text_size": "36",
            "include_cut_lines": "on",
        },
    )

    assert response.status_code == 200
    assert b'<html lang="es">' in response.data
    assert b'Switch language to English' in response.data
    assert b'>English</button>' in response.data
    assert b"PDF template preview" in response.data
    assert b"Layout summary" in response.data
    assert b"Demo Badge on Front" in response.data
    assert b"Detailed placement coordinates" in response.data
    assert b"High-contrast outlines" in response.data
    assert b"badge-contrast-outline" in response.data
    assert b"cut-line-outline" in response.data
    assert b"highContrastPreview" in response.data
    assert b'class="brand-mark"' in response.data
    assert b'viewBox="0 0 792.0 612.0"' in response.data
    assert b'href="https://makespacemadrid.org/assets/images/favicon.png"' in response.data
    assert b'name="orientation" value="landscape"' in response.data
    assert b'name="page_margin" value="0.4"' in response.data
    assert b'name="panel_gap" value="0.3"' in response.data
    assert b"Manual placement" in response.data
    assert b'data-field="x"' in response.data
    assert b'step="0.01" value="' in response.data
    assert b"normalizeNumberInput" in response.data
    assert b"Ctrl/Shift-click badges to multi-select" in response.data
    assert b'data-selected="false"' in response.data
    assert b'aria-pressed="false"' in response.data
    assert b"selection-outline" in response.data
    assert b"selectedBadges" in response.data
    assert b"movableBadgesFor" in response.data
    assert b"Reset automatic placement" in response.data
    assert b"Snap to grid" in response.data
    assert b"Snap to panel edges" in response.data
    assert b'id="edge-snap-tolerance"' in response.data
    assert b"data-panel-x" in response.data
    assert b"snapBadgeToPanelEdges" in response.data
    assert b"Rotate 45" in response.data
    assert b"Align left" in response.data
    assert b"Center horizontally" in response.data
    assert b"Distribute vertically" in response.data
    assert b"applyPanelAlignment" in response.data
    assert b"preview-status" in response.data
    assert b'class="draggable-badge"' in response.data
    assert b'class="collision-outline"' in response.data
    assert b"FRONT" in response.data
    assert b"BACK" in response.data
    assert b"Ada" in response.data
    assert b"MakeSpace" in response.data
    assert b'class="draggable-panel-text"' in response.data
    assert b'class="panel-text-hit-area"' in response.data
    assert b'sizePanelTextTarget' in response.data
    assert response.data.index(b'class="draggable-badge"') < response.data.index(b'class="draggable-panel-text"')
    assert b'name="front_text_x"' in response.data
    assert b'name="back_text_y"' in response.data
    assert b'updatePanelTextFromInputs' in response.data
    assert b'name="front_text" value="Ada"' in response.data
    assert b'name="back_text" value="MakeSpace"' in response.data
    assert b'name="text_font" value="dejavu"' in response.data
    assert b'name="text_size" value="36"' in response.data
    assert b'font-size="36.0"' in response.data
    assert b'height="50.0"' in response.data


def test_calibration_pdf_route_returns_printable_pdf():
    app = create_app()

    response = app.test_client().get("/calibration.pdf?page_size=letter&orientation=landscape&unit=in")

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.headers["Content-Disposition"] == "attachment; filename=tshirt-calibration-page.pdf"
    assert response.data.startswith(b"%PDF")
    assert b"Print calibration page" in response.data
    assert b"unit=in" in response.data


def test_pdf_route_returns_mirrored_pdf_download_by_default(monkeypatch):
    calls = []
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(render_pdf=lambda *args, **kwargs: calls.append(kwargs) or b"%PDF-1.4\n%%EOF"),
    )
    app = create_app()

    response = app.test_client().post(
        "/pdf",
        data={
            "badges": [DEMO_BADGE.id],
            "sides": ["front"],
            "mode": "grid",
            "page_size": "letter",
            "unit": "in",
            "badge_size": "1.2",
            "spacing": "0.2",
            "copies": "1",
        },
    )

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.headers["Content-Disposition"] == "attachment; filename=tshirt-badge-template.pdf"
    assert response.data.startswith(b"%PDF")
    assert calls[0]["mirror"] is True
    assert calls[0]["panel_text"] == {"front": "", "back": "", "font": "ubuntu", "size": "28"}
    assert calls[0]["print_marks"] is False
    assert calls[0]["cut_lines"] is False
    assert calls[0]["metadata"]["include_print_marks"] == "false"
    assert calls[0]["metadata"]["include_cut_lines"] == "false"
    assert calls[0]["metadata"]["include_yellow_unifier"] == "false"
    assert calls[0]["yellow_unifier"] is False


def test_proof_pdf_route_forces_non_mirrored_output(monkeypatch):
    calls = []
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(render_pdf=lambda *args, **kwargs: calls.append(kwargs) or b"%PDF-1.4\n%%EOF"),
    )
    app = create_app()

    response = app.test_client().post("/proof.pdf", data={"front_badges": [DEMO_BADGE.id], "sides": ["front"]})

    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == "attachment; filename=tshirt-badge-proof.pdf"
    assert calls[0]["mirror"] is False
    assert calls[0]["metadata"]["mirror"] == "false"


def test_svg_and_png_export_routes(monkeypatch):
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()
    data = {"front_badges": [DEMO_BADGE.id], "sides": ["front"]}

    svg = app.test_client().post("/export.svg", data=data)
    png = app.test_client().post("/export.png", data=data)

    assert svg.status_code == 200 and svg.mimetype == "image/svg+xml"
    assert b'<svg xmlns="http://www.w3.org/2000/svg"' in svg.data
    assert png.status_code == 200 and png.mimetype == "image/png"
    assert png.data.startswith(b"\x89PNG")


def test_locked_layout_moves_unlocked_badges_out_of_the_way():
    locked = Placement("locked", 10, 10, 40, 40)
    colliding = Placement("moving", 20, 20, 40, 40)
    layout = PanelLayout("front", 0, 0, 200, 200, [locked, colliding])

    adjusted = avoid_locked_placement_collisions(layout, {0})

    assert adjusted.placements[0] == locked
    assert adjusted.placements[1] != colliding
    moved = adjusted.placements[1]
    assert not (
        moved.x < locked.x + locked.width + 4
        and moved.x + moved.width + 4 > locked.x
        and moved.y < locked.y + locked.height + 4
        and moved.y + moved.height + 4 > locked.y
    )


def test_pdf_route_passes_panel_text_options(monkeypatch):
    calls = []
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(render_pdf=lambda *args, **kwargs: calls.append(kwargs) or b"%PDF-1.4\n%%EOF"),
    )
    app = create_app()

    response = app.test_client().post(
        "/pdf",
        data={
            "badges": [DEMO_BADGE.id],
            "sides": ["front", "back"],
            "front_text": "Ada",
            "back_text": "MakeSpace",
            "text_font": "courier",
            "text_size": "34",
        },
    )

    assert response.status_code == 200
    assert calls[0]["panel_text"] == {"front": "Ada", "back": "MakeSpace", "font": "courier", "size": "34"}



def test_pdf_route_renders_with_placeholder_when_asset_verification_fails(monkeypatch):
    calls = []
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(
            verify_pdf_assets=lambda badges: [
                {"badge_id": badges[0].id, "name": badges[0].name, "message": "broken asset"}
            ],
            render_pdf=lambda *args, **kwargs: calls.append((args, kwargs)) or b"%PDF-1.4\n%%EOF",
        ),
    )
    app = create_app()

    response = app.test_client().post(
        "/pdf",
        data={"badges": [DEMO_BADGE.id], "sides": ["front"], "mode": "grid"},
    )

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")
    assert json.loads(response.headers["X-Badgeware-Warnings"]) == {
        "asset_failures": [{"badge_id": DEMO_BADGE.id, "name": DEMO_BADGE.name, "message": "broken asset"}]
    }
    args, kwargs = calls[0]
    assert [badge.id for badge in args[0]] == [DEMO_BADGE.id]
    assert kwargs["metadata"]["asset_failures"] == "1"
    assert kwargs["metadata"]["allow_partial"] == "true"

def test_refresh_route_clears_cache_and_redirects(monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    called = []
    monkeypatch.setattr("tshirt_templates.app.refresh_badges", lambda: called.append(True))
    app = create_app()

    response = app.test_client().post("/refresh")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    assert called == [True]
    assert {"event": "badge_refresh", "source": "browser"} in _logged_events(caplog)


def test_preview_saves_uploaded_badges(monkeypatch, tmp_path):
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    response = app.test_client().post(
        "/preview",
        data={
            "uploads": (BytesIO(b"<svg></svg>"), "custom.svg"),
            "sides": ["front"],
            "mode": "grid",
            "page_size": "letter",
            "unit": "in",
            "badge_size": "1.2",
            "spacing": "0.2",
            "copies": "1",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Custom" in response.data
    assert b"upload:" in response.data


def test_preview_orders_badges_alphabetically(monkeypatch):
    alpha = Badge("alpha.svg", "Alpha", "alpha.svg", "/static/demo-badge.svg", ".svg")
    zulu = Badge("zulu.svg", "Zulu", "zulu.svg", "/static/demo-badge.svg", ".svg")
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [zulu, alpha])
    app = create_app()

    response = app.test_client().post(
        "/preview",
        data={
            "badges": [zulu.id, alpha.id],
            "sides": ["front"],
            "mode": "grid",
            "order": "alphabetical",
        },
    )

    assert response.status_code == 200
    assert response.data.index(b"Alpha") < response.data.index(b"Zulu")


def test_pdf_route_applies_manual_coordinates(monkeypatch):
    captured = {}
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])

    def fake_render_pdf(badges, page_size, layouts, **kwargs):
        captured["placement"] = layouts[0].placements[0]
        return b"%PDF-1.4\n%%EOF"

    monkeypatch.setitem(sys.modules, "tshirt_templates.pdf", SimpleNamespace(render_pdf=fake_render_pdf))
    app = create_app()

    response = app.test_client().post(
        "/pdf",
        data={
            "badges": [DEMO_BADGE.id],
            "sides": ["front"],
            "mode": "grid",
            "page_size": "letter",
            "unit": "in",
            "badge_size": "1.0",
            "manual_0_0_x": "1.5",
            "manual_0_0_y": "2.5",
            "manual_0_0_rotation": "15",
        },
    )

    assert response.status_code == 200
    assert captured["placement"].x == 108.0
    assert captured["placement"].y == 792.0 - 180.0 - 72.0
    assert captured["placement"].rotation == 15


def test_preview_can_include_makespace_logo(monkeypatch):
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()

    response = app.test_client().post(
        "/preview",
        data={
            "badges": [DEMO_BADGE.id],
            "sides": ["front"],
            "mode": "grid",
            "logo_sides": ["front"],
            "logo_size": "5.0",
        },
    )

    assert response.status_code == 200
    assert b"MakeSpace Madrid Logo" in response.data
    assert b"makespace-bk.svg" in response.data


def test_pdf_route_includes_makespace_logo_placement(monkeypatch):
    captured = {}
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])

    def fake_render_pdf(badges, page_size, layouts, **kwargs):
        captured["badges"] = badges
        captured["layout"] = layouts[0]
        return b"%PDF-1.4\n%%EOF"

    monkeypatch.setitem(sys.modules, "tshirt_templates.pdf", SimpleNamespace(render_pdf=fake_render_pdf))
    app = create_app()

    response = app.test_client().post(
        "/pdf",
        data={
            "badges": [DEMO_BADGE.id],
            "sides": ["front"],
            "mode": "grid",
            "unit": "in",
            "badge_size": "1.0",
            "logo_sides": ["front"],
            "logo_size": "3.0",
        },
    )

    assert response.status_code == 200
    assert [badge.id for badge in captured["badges"]] == [DEMO_BADGE.id, "makespace-logo"]
    logo_placement = captured["layout"].placements[-1]
    assert logo_placement.badge_id == "makespace-logo"
    assert logo_placement.width == 216.0
    assert logo_placement.height == 216.0


def test_api_health_options_and_badges(monkeypatch):
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: [DEMO_BADGE])
    app = create_app()
    client = app.test_client()

    health = client.get("/api/v1/health")
    ready = client.get("/api/v1/ready")
    options = client.get("/api/v1/options")
    badges = client.get("/api/v1/badges?logo_sides=front")

    assert health.status_code == 200
    assert health.json == {"status": "ok", "service": "tshirt_templates"}
    assert ready.status_code == 200
    assert ready.json == {
        "status": "ready",
        "service": "tshirt_templates",
        "checks": {"upload_folder": "ok"},
    }
    assert options.status_code == 200
    assert options.json["defaults"]["page_size"] == "a4"
    assert options.json["defaults"]["text_font"] == "ubuntu"
    assert options.json["defaults"]["text_size"] == "28"
    assert options.json["defaults"]["curve_device"] == "custom"
    assert options.json["defaults"]["curve_diameter"] == "8.0"
    assert options.json["defaults"]["page_margin"] == "1.25"
    assert options.json["defaults"]["panel_gap"] == "0.85"
    assert options.json["defaults"]["logo_sides"] == []
    assert options.json["defaults"]["include_yellow_unifier"] is False
    assert options.json["layout_modes"]["m-pixels-no-shrink"] == "M pixel shape (no shrink)"
    assert options.json["layout_mode_details"]["m-pixels-no-shrink"]["shrinks_badges"] is False
    assert options.json["layout_mode_details"]["m-pixels-no-shrink"]["fallbacks"] == [
        "line-above",
        "lines-above-and-below",
        "square-frame",
        "double-square-frame",
    ]
    assert options.json["text_fonts"]["ubuntu"] == "Ubuntu"
    assert options.json["text_fonts"]["fredoka-one"] == "Fredoka One"
    assert options.json["curve_device_options"]["mug"] == "Standard mug"
    assert options.json["curve_device_diameters"]["mug"]["cm"] == "8.2"
    assert options.json["logo_size_options"]["cm"]
    assert options.json["badge_size_options"]["cm"][0] == "2.5"
    assert options.json["badge_size_options"]["in"][0] == "1.0"
    index_html = client.get("/").data
    badge_select_html = index_html.split(b'id="badge-size-select"', 1)[1].split(b"</select>", 1)[0]
    assert b'value="1.0"' not in badge_select_html
    assert b'value="2.5"' in badge_select_html
    assert badges.status_code == 200
    assert [badge["id"] for badge in badges.json["badges"]] == [DEMO_BADGE.id, "makespace-logo"]


def test_api_uploads_saves_badges(monkeypatch, tmp_path, caplog):
    caplog.set_level(logging.INFO)
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    response = app.test_client().post(
        "/api/v1/uploads",
        data={"uploads": (BytesIO(b"<svg></svg>"), "team badge.svg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    uploaded = response.json["badges"][0]
    assert uploaded["id"].startswith("upload:")
    assert uploaded["name"] == "Team Badge"
    assert uploaded["source"] == "upload"
    assert response.json["warnings"][0]["code"] == "missing_dimensions"
    assert (tmp_path / uploaded["id"].removeprefix("upload:")).exists()
    assert {
        "badge_count": 1,
        "event": "upload_saved",
        "route": "/api/v1/uploads",
        "warning_count": 1,
    } in _logged_events(caplog)


def test_api_uploads_rejects_empty_payload(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    response = app.test_client().post("/api/v1/uploads", data={})

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_upload"
    assert response.json["error"]["field"] == "uploads"


def test_api_replace_upload_updates_saved_badge(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    uploaded = tmp_path / "abc-team.svg"
    uploaded.write_bytes(b"<svg>old</svg>")

    response = app.test_client().put(
        f"/api/v1/uploads/{uploaded.name}",
        data={"upload": (BytesIO(b"<svg>new</svg>"), "replacement.svg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert response.json["badge"]["id"] == f"upload:{uploaded.name}"
    assert uploaded.read_bytes() == b"<svg>new</svg>"
    assert response.json["warnings"][0]["code"] == "missing_dimensions"


def test_api_uploads_reject_invalid_image_content(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    response = app.test_client().post(
        "/api/v1/uploads",
        data={"uploads": (BytesIO(b"not an image"), "fake.png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_upload"


def test_api_replace_upload_rejects_missing_file_field(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    uploaded = tmp_path / "abc-team.svg"
    uploaded.write_bytes(b"<svg>old</svg>")

    response = app.test_client().put(f"/api/v1/uploads/{uploaded.name}")

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_upload"


def test_api_delete_upload_removes_saved_badge(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    uploaded = tmp_path / "abc-team.svg"
    uploaded.write_bytes(b"<svg></svg>")

    response = app.test_client().delete(f"/api/v1/uploads/{uploaded.name}")

    assert response.status_code == 200
    assert response.json == {"deleted": uploaded.name}
    assert not uploaded.exists()


def test_api_delete_upload_returns_not_found_for_unknown_file(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    response = app.test_client().delete("/api/v1/uploads/missing.svg")

    assert response.status_code == 404
    assert response.json["error"]["code"] == "upload_not_found"


def test_api_layout_preview_computes_json_layout_with_logo(monkeypatch):
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()

    response = app.test_client().post(
        "/api/v1/layouts/preview",
        json={
            "badge_ids": [DEMO_BADGE.id],
            "options": {
                "sides": ["front", "back"],
                "unit": "in",
                "badge_size": "1.0",
                "spacing": "0.2",
                "logo_sides": ["front", "back"],
                "logo_size": "2.0",
                "front_logo_size": "1.0",
                "back_logo_size": "3.0",
                "front_text": "Ada",
                "back_text": "MakeSpace",
                "text_font": "times",
                "text_size": "32",
                "include_yellow_unifier": True,
                "include_curve_effect": True,
                "curve_device": "mug",
                "curve_diameter": "3.25",
            },
            "manual_placements": [
                {"layout_index": 0, "placement_index": 0, "x": 1.0, "y": 2.0, "rotation": 12}
            ],
        },
    )

    assert response.status_code == 200
    assert response.json["page"]["unit"] == "in"
    assert response.json["options"]["include_logo"] is True
    assert response.json["options"]["front_logo_size"] == "1.0"
    assert response.json["options"]["back_logo_size"] == "3.0"
    assert response.json["options"]["front_text"] == "Ada"
    assert response.json["options"]["back_text"] == "MakeSpace"
    assert response.json["options"]["text_font"] == "times"
    assert response.json["options"]["text_size"] == "32"
    assert response.json["options"]["include_yellow_unifier"] is True
    assert response.json["options"]["include_curve_effect"] is True
    assert response.json["options"]["curve_device"] == "mug"
    assert response.json["options"]["curve_diameter"] == "3.25"
    assert [badge["id"] for badge in response.json["badges"]] == [DEMO_BADGE.id, "makespace-logo"]
    front_placements = response.json["layouts"][0]["placements"]
    back_placements = response.json["layouts"][1]["placements"]
    assert [placement["badge_id"] for placement in front_placements] == [DEMO_BADGE.id, "makespace-logo"]
    assert [placement["badge_id"] for placement in back_placements] == [DEMO_BADGE.id, "makespace-logo"]
    assert front_placements[0]["x"] == 1.0
    assert front_placements[0]["rotation"] == 12.0
    assert front_placements[-1]["width"] == 1.0
    assert back_placements[-1]["width"] == 3.0


def test_api_layout_preview_accepts_m_pixel_no_shrink_mode(monkeypatch):
    badges = [
        Badge(
            id=f"badge-{index}.svg",
            name=f"Badge {index}",
            path=f"badge-{index}.svg",
            raw_url=f"/static/badge-{index}.svg",
            extension=".svg",
        )
        for index in range(14)
    ]
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: badges)
    app = create_app()

    response = app.test_client().post(
        "/api/v1/layouts/preview",
        json={
            "badge_ids": [badge.id for badge in badges],
            "options": {
                "sides": ["front"],
                "mode": "m-pixels-no-shrink",
                "unit": "in",
                "badge_size": "1.0",
                "spacing": "0.1",
            },
        },
    )

    assert response.status_code == 200
    assert response.json["options"]["mode"] == "m-pixels-no-shrink"
    placements = response.json["layouts"][0]["placements"]
    assert len(placements) == 14
    assert {placement["width"] for placement in placements} == {1.0}
    assert len({round(placement["y"], 3) for placement in placements}) == 6


def test_api_layout_preview_can_limit_logo_to_one_side(monkeypatch):
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()

    response = app.test_client().post(
        "/api/v1/layouts/preview",
        json={
            "badge_ids": [DEMO_BADGE.id],
            "options": {
                "sides": ["front", "back"],
                "unit": "in",
                "badge_size": "1.0",
                "logo_sides": ["front"],
                "front_logo_size": "1.0",
                "back_logo_size": "3.0",
            },
        },
    )

    assert response.status_code == 200
    assert response.json["options"]["logo_sides"] == ["front"]
    front_placements = response.json["layouts"][0]["placements"]
    back_placements = response.json["layouts"][1]["placements"]
    assert [placement["badge_id"] for placement in front_placements] == [DEMO_BADGE.id, "makespace-logo"]
    assert [placement["badge_id"] for placement in back_placements] == [DEMO_BADGE.id]


def test_api_pdf_generates_pdf_from_json(monkeypatch):
    calls = []
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(render_pdf=lambda *args, **kwargs: calls.append((args, kwargs)) or b"%PDF-1.4\n%%EOF"),
    )
    app = create_app()

    response = app.test_client().post(
        "/api/v1/pdfs",
        json={
            "badge_ids": [DEMO_BADGE.id],
            "options": {
                "sides": ["front"],
                "unit": "in",
                "badge_size": "1.0",
                "front_text": "Ada",
                "text_font": "courier",
                "text_size": "31",
                "mirror": False,
                "include_print_marks": True,
                "include_cut_lines": True,
                "include_yellow_unifier": True,
                "include_curve_effect": True,
                "curve_device": "mug",
                "curve_diameter": "3.25",
            },
            "manual_placements": [
                {"layout_index": 0, "placement_index": 0, "x": 1.0, "y": 2.0, "rotation": 12}
            ],
        },
    )

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.headers["Content-Disposition"] == "attachment; filename=tshirt-badge-template.pdf"
    assert response.data.startswith(b"%PDF")
    args, kwargs = calls[0]
    assert [badge.id for badge in args[0]] == [DEMO_BADGE.id]
    assert args[2][0].placements[0].x == 72.0
    assert args[2][0].placements[0].rotation == 12.0
    assert kwargs["mirror"] is False
    assert kwargs["panel_text"] == {"front": "Ada", "back": "", "font": "courier", "size": "31"}
    assert kwargs["print_marks"] is True
    assert kwargs["cut_lines"] is True
    assert kwargs["metadata"]["include_print_marks"] == "true"
    assert kwargs["metadata"]["include_cut_lines"] == "true"
    assert kwargs["metadata"]["include_yellow_unifier"] == "true"
    assert kwargs["yellow_unifier"] is True
    assert kwargs["metadata"]["include_curve_effect"] == "true"
    assert kwargs["metadata"]["curve_device"] == "mug"
    assert kwargs["metadata"]["curve_diameter"] == "3.25"
    assert kwargs["curve_settings"] == {"device": "mug", "diameter_inches": 3.25}


def test_pdf_route_passes_dragged_panel_text_positions(monkeypatch):
    calls = []
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(render_pdf=lambda *args, **kwargs: calls.append((args, kwargs)) or b"%PDF-1.4\n%%EOF"),
    )
    app = create_app()

    response = app.test_client().post(
        "/pdf",
        data={
            "badges": [DEMO_BADGE.id],
            "sides": ["front"],
            "unit": "in",
            "page_size": "letter",
            "front_text": "Ada",
            "front_text_x": "2.5",
            "front_text_y": "3.0",
            "text_size": "30",
        },
    )

    assert response.status_code == 200
    panel_text = calls[0][1]["panel_text"]
    assert panel_text["front"] == "Ada"
    assert panel_text["size"] == "30"
    assert panel_text["positions"]["front"] == {"x": 180.0, "y": 576.0}

def test_api_pdf_verifies_assets_before_rendering(monkeypatch, caplog):
    caplog.set_level(logging.WARNING)
    render_calls = []
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(
            verify_pdf_assets=lambda badges: [
                {"badge_id": badges[0].id, "name": badges[0].name, "message": "broken asset"}
            ],
            render_pdf=lambda *args, **kwargs: render_calls.append((args, kwargs)) or b"%PDF",
        ),
    )
    app = create_app()

    response = app.test_client().post(
        "/api/v1/pdfs",
        json={"badge_ids": [DEMO_BADGE.id], "options": {"sides": ["front"]}},
    )

    assert response.status_code == 422
    assert response.json["error"]["code"] == "asset_verification_failed"
    assert response.json["error"]["failures"][0]["badge_id"] == DEMO_BADGE.id
    assert render_calls == []
    assert {
        "event": "pdf_generation_failed",
        "failure_count": 1,
        "reason": "asset_verification_failed",
        "route": "/api/v1/pdfs",
    } in _logged_events(caplog)


def test_api_pdf_can_allow_partial_asset_failures(monkeypatch):
    calls = []
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(
            verify_pdf_assets=lambda badges: [
                {"badge_id": badges[0].id, "name": badges[0].name, "message": "broken asset"}
            ],
            render_pdf=lambda *args, **kwargs: calls.append((args, kwargs)) or b"%PDF-1.4\n%%EOF",
        ),
    )
    app = create_app()

    response = app.test_client().post(
        "/api/v1/pdfs",
        json={"badge_ids": [DEMO_BADGE.id], "options": {"sides": ["front"]}, "allow_partial": True},
    )

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")
    assert json.loads(response.headers["X-Badgeware-Warnings"]) == {
        "asset_failures": [{"badge_id": DEMO_BADGE.id, "name": DEMO_BADGE.name, "message": "broken asset"}]
    }
    args, kwargs = calls[0]
    assert [badge.id for badge in args[0]] == [DEMO_BADGE.id]
    assert kwargs["metadata"]["asset_failures"] == "1"
    assert kwargs["metadata"]["allow_partial"] == "true"

def test_api_pdf_rejects_non_json_payload():
    app = create_app()

    response = app.test_client().post("/api/v1/pdfs", data="not-json")

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_json"


def test_mcp_metadata_resources_prompts_and_tools(monkeypatch):
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()
    client = app.test_client()

    metadata = client.get("/mcp")
    initialize = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    ping = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "ping"})
    initialized = client.post("/mcp", json={"jsonrpc": "2.0", "id": 3, "method": "notifications/initialized"})
    tools = client.post("/mcp", json={"jsonrpc": "2.0", "id": 4, "method": "tools/list"})
    resources = client.post("/mcp", json={"jsonrpc": "2.0", "id": 5, "method": "resources/list"})
    read_options = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 6,
            "method": "resources/read",
            "params": {"uri": "tshirt://options"},
        },
    )
    read_badges = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 11,
            "method": "resources/read",
            "params": {"uri": "tshirt://badges"},
        },
    )
    resource_templates = client.post("/mcp", json={"jsonrpc": "2.0", "id": 8, "method": "resources/templates/list"})
    prompts = client.post("/mcp", json={"jsonrpc": "2.0", "id": 9, "method": "prompts/list"})
    prompt = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 10,
            "method": "prompts/get",
            "params": {"name": "explain_layout"},
        },
    )
    layout = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "compute_layout",
                "arguments": {
                    "badge_ids": [DEMO_BADGE.id],
                    "options": {"sides": ["front"], "unit": "cm", "badge_size": "3.5"},
                },
            },
        },
    )

    assert metadata.status_code == 200
    assert metadata.json["endpoint"] == "/mcp"
    assert metadata.json["transport"] == "streamable-http-json-rpc"
    assert "required MCP port" in metadata.json["port_note"]
    assert "render_pdf" in metadata.json["tools"]
    assert initialize.status_code == 200
    assert initialize.json["result"]["serverInfo"]["name"] == "tshirt_templates"
    assert initialize.json["result"]["capabilities"]["prompts"]["listChanged"] is False
    assert ping.status_code == 200
    assert ping.json["result"] == {}
    assert initialized.status_code == 200
    assert initialized.json["result"] == {}
    assert tools.status_code == 200
    tool_payloads = {tool["name"]: tool for tool in tools.json["result"]["tools"]}
    expected_modes = {
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
    compute_mode_schema = tool_payloads["compute_layout"]["inputSchema"]["properties"]["options"]["properties"]["mode"]
    render_mode_schema = tool_payloads["render_pdf"]["inputSchema"]["properties"]["options"]["properties"]["mode"]
    validate_mode_schema = tool_payloads["validate_template"]["inputSchema"]["properties"]["options"]["properties"]["mode"]
    assert set(compute_mode_schema["enum"]) == expected_modes
    assert set(render_mode_schema["enum"]) == expected_modes
    assert set(validate_mode_schema["enum"]) == expected_modes
    assert "preserve badge size" in compute_mode_schema["description"]
    assert {tool["name"] for tool in tools.json["result"]["tools"]} >= {
        "get_options",
        "list_badges",
        "compute_layout",
        "render_pdf",
        "upload_badge_artwork",
        "validate_template",
        "list_saved_templates",
        "save_template",
        "get_saved_template",
        "delete_saved_template",
    }
    assert resources.status_code == 200
    assert {resource["uri"] for resource in resources.json["result"]["resources"]} >= {
        "tshirt://options",
        "tshirt://badges",
        "tshirt://templates",
    }
    assert read_options.status_code == 200
    options_resource = read_options.json["result"]["contents"][0]
    assert options_resource["mimeType"] == "application/json"
    assert json.loads(options_resource["text"])["defaults"]["text_font"] == "ubuntu"
    assert json.loads(options_resource["text"])["defaults"]["text_size"] == "28"
    assert json.loads(options_resource["text"])["defaults"]["page_margin"] == "1.25"
    options_payload = json.loads(options_resource["text"])
    assert options_payload["defaults"]["logo_sides"] == []
    assert options_payload["defaults"]["include_yellow_unifier"] is False
    assert options_payload["layout_modes"]["m-pixels-no-shrink"] == "M pixel shape (no shrink)"
    assert options_payload["layout_mode_details"]["m-pixels-no-shrink"]["fallbacks"] == [
        "line-above",
        "lines-above-and-below",
        "square-frame",
        "double-square-frame",
    ]
    assert read_badges.status_code == 200
    badges_resource = read_badges.json["result"]["contents"][0]
    assert json.loads(badges_resource["text"])["badges"][0]["id"] == DEMO_BADGE.id
    assert resource_templates.status_code == 200
    templates_payload = resource_templates.json["result"]["resourceTemplates"]
    assert {template["uriTemplate"] for template in templates_payload} >= {
        "tshirt://badges{?order,logo_sides,include_logo,refresh}",
        "tshirt://templates/{name}",
    }
    assert prompts.status_code == 200
    assert {prompt["name"] for prompt in prompts.json["result"]["prompts"]} >= {
        "design_tshirt_template",
        "optimize_cut_sheet",
        "explain_layout",
    }
    assert prompt.status_code == 200
    assert prompt.json["result"]["messages"][0]["content"]["type"] == "text"
    assert layout.status_code == 200
    content = layout.json["result"]["structuredContent"]
    assert content["layouts"][0]["placements"][0]["badge_id"] == DEMO_BADGE.id


def test_mcp_rejects_unknown_resources_and_invalid_uploads(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    client = app.test_client()

    unknown_resource = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": "tshirt://missing"},
        },
    )
    invalid_upload = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "upload_badge_artwork",
                "arguments": {"filename": "badge.svg", "content_base64": "not-base64"},
            },
        },
    )

    assert unknown_resource.status_code == 200
    assert unknown_resource.json["error"]["message"] == "Unknown resource: tshirt://missing"
    assert invalid_upload.status_code == 200
    assert invalid_upload.json["error"]["message"] == "content_base64 is not valid base64."



def test_mcp_render_pdf_reports_asset_verification_failures(monkeypatch):
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(
            verify_pdf_assets=lambda badges: [
                {"badge_id": badges[0].id, "name": badges[0].name, "message": "broken asset"}
            ],
            render_pdf=lambda *args, **kwargs: b"%PDF",
        ),
    )
    app = create_app()

    response = app.test_client().post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "render_pdf",
                "arguments": {"badge_ids": [DEMO_BADGE.id], "options": {"sides": ["front"]}},
            },
        },
    )

    assert response.status_code == 200
    assert response.json["error"]["code"] == -32602
    assert response.json["error"]["data"]["code"] == "asset_verification_failed"
    assert response.json["error"]["data"]["failures"][0]["badge_id"] == DEMO_BADGE.id


def test_mcp_render_pdf_can_allow_partial_asset_failures(monkeypatch):
    calls = []
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(
            verify_pdf_assets=lambda badges: [
                {"badge_id": badges[0].id, "name": badges[0].name, "message": "broken asset"}
            ],
            render_pdf=lambda *args, **kwargs: calls.append((args, kwargs)) or b"%PDF-1.4\n%%EOF",
        ),
    )
    app = create_app()

    response = app.test_client().post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "render_pdf",
                "arguments": {
                    "badge_ids": [DEMO_BADGE.id],
                    "options": {"sides": ["front"]},
                    "allow_partial": True,
                },
            },
        },
    )

    assert response.status_code == 200
    payload = response.json["result"]["structuredContent"]
    assert base64.b64decode(payload["pdf_base64"]).startswith(b"%PDF")
    assert payload["warnings"] == [
        {
            "code": "asset_verification_failed",
            "message": "One or more badge assets could not be fetched or rendered; placeholders will be drawn for failed assets.",
            "failures": [{"badge_id": DEMO_BADGE.id, "name": DEMO_BADGE.name, "message": "broken asset"}],
        }
    ]
    args, kwargs = calls[0]
    assert [badge.id for badge in args[0]] == [DEMO_BADGE.id]
    assert kwargs["metadata"]["asset_failures"] == "1"
    assert kwargs["metadata"]["allow_partial"] == "true"


def test_mcp_render_pdf_upload_and_validate_template(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(render_pdf=lambda *args, **kwargs: calls.append((args, kwargs)) or b"%PDF-1.4\n%%EOF"),
    )
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    client = app.test_client()

    upload = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "upload_badge_artwork",
                "arguments": {
                    "filename": "team.svg",
                    "content_base64": base64.b64encode(b"<svg></svg>").decode("ascii"),
                },
            },
        },
    )
    pdf = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "render_pdf",
                "arguments": {
                    "badge_ids": [DEMO_BADGE.id],
                    "options": {"sides": ["front"], "mirror": False, "front_text": "Ada"},
                },
            },
        },
    )
    validation = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "validate_template",
                "arguments": {"badge_ids": [DEMO_BADGE.id, "missing.svg"], "options": {"sides": ["front"]}},
            },
        },
    )

    assert upload.status_code == 200
    uploaded_badge = upload.json["result"]["structuredContent"]["badge"]
    assert uploaded_badge["id"].startswith("upload:")
    assert (tmp_path / uploaded_badge["id"].removeprefix("upload:")).exists()
    assert pdf.status_code == 200
    pdf_payload = pdf.json["result"]["structuredContent"]
    assert pdf_payload["mime_type"] == "application/pdf"
    assert pdf_payload["warnings"] == []
    assert pdf_payload["diagnostics"]["requested_badge_ids"] == [DEMO_BADGE.id]
    assert pdf_payload["diagnostics"]["missing_badge_ids"] == []
    assert pdf_payload["diagnostics"]["placement_count"] > 0
    assert pdf_payload["resource"]["mimeType"] == "application/pdf"
    assert base64.b64decode(pdf_payload["pdf_base64"]).startswith(b"%PDF")
    pdf_content = pdf.json["result"]["content"]
    assert pdf_content[0]["type"] == "text"
    assert pdf_content[1]["type"] == "resource"
    assert pdf_content[1]["resource"]["blob"] == pdf_payload["pdf_base64"]
    assert calls[0][1]["panel_text"]["front"] == "Ada"
    assert validation.status_code == 200
    validation_payload = validation.json["result"]["structuredContent"]
    assert validation_payload["normalized"]["options"]["sides"] == ["front"]
    assert validation_payload["warnings"][0]["code"] == "unknown_badges"



def test_mcp_render_pdf_rejects_missing_badges_before_delivering_partial_pdf(monkeypatch):
    calls = []
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(render_pdf=lambda *args, **kwargs: calls.append((args, kwargs)) or b"%PDF"),
    )
    app = create_app()

    response = app.test_client().post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "render_pdf",
                "arguments": {
                    "badge_ids": [DEMO_BADGE.id, "missing.svg"],
                    "options": {"sides": ["front"]},
                },
            },
        },
    )

    assert response.status_code == 200
    assert response.json["error"]["code"] == -32602
    assert response.json["error"]["data"]["code"] == "render_preflight_failed"
    assert response.json["error"]["data"]["failures"][0]["code"] == "unknown_badges"
    assert response.json["error"]["data"]["failures"][0]["badge_ids"] == ["missing.svg"]
    assert calls == []


def test_mcp_render_pdf_can_deliver_partial_pdf_with_diagnostics(monkeypatch):
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(render_pdf=lambda *args, **kwargs: b"%PDF-1.4\n%%EOF"),
    )
    app = create_app()

    response = app.test_client().post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "render_pdf",
                "arguments": {
                    "badge_ids": [DEMO_BADGE.id, "missing.svg"],
                    "options": {"sides": ["front"]},
                    "allow_partial": True,
                },
            },
        },
    )

    assert response.status_code == 200
    payload = response.json["result"]["structuredContent"]
    assert base64.b64decode(payload["pdf_base64"]).startswith(b"%PDF")
    assert payload["warnings"][0]["code"] == "unknown_badges"
    assert payload["diagnostics"]["missing_badge_ids"] == ["missing.svg"]
    assert payload["diagnostics"]["allow_partial"] is True

def test_api_ready_reports_not_ready_when_upload_folder_is_file(tmp_path):
    app = create_app()
    upload_path = tmp_path / "uploads"
    upload_path.write_text("not a directory", encoding="utf-8")
    app.config["UPLOAD_FOLDER"] = str(upload_path)

    response = app.test_client().get("/api/v1/ready")

    assert response.status_code == 503
    assert response.json == {
        "status": "not_ready",
        "service": "tshirt_templates",
        "checks": {"upload_folder": "error"},
    }


def test_api_index_and_mcp_batch_and_resource_template_queries(monkeypatch):
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()
    client = app.test_client()

    api_index = client.get("/api/v1")
    batch = client.post(
        "/mcp",
        json=[
            {"jsonrpc": "2.0", "id": 1, "method": "ping"},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "list_badges", "input": {"logo_sides": ["front"]}},
            },
        ],
    )
    templated_resource = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/read",
            "params": {"uri": "tshirt://badges?logo_sides=front"},
        },
    )
    mixed_batch = client.post(
        "/mcp",
        json=[
            {"jsonrpc": "2.0", "id": 4, "method": "ping"},
            "bad",
            {"jsonrpc": "2.0", "id": 5, "method": "tools/list", "params": []},
        ],
    )
    invalid = client.post("/mcp", json="bad")

    assert api_index.status_code == 200
    assert api_index.json["documentation"]["repository_path"] == "docs/APIDOCS.md"
    assert api_index.json["mcp"]["endpoint"] == "/mcp"
    assert api_index.json["mcp"]["resource_templates"] == ["tshirt://badges{?order,logo_sides,include_logo,refresh}"]
    assert "no required MCP port" in api_index.json["mcp"]["port_note"]
    assert batch.status_code == 200
    assert batch.json[0]["result"] == {}
    assert batch.json[1]["result"]["structuredContent"]["badges"][-1]["id"] == "makespace-logo"
    assert templated_resource.status_code == 200
    resource_payload = json.loads(templated_resource.json["result"]["contents"][0]["text"])
    assert resource_payload["badges"][-1]["id"] == "makespace-logo"
    assert mixed_batch.status_code == 200
    assert mixed_batch.json[0]["result"] == {}
    assert mixed_batch.json[1]["error"]["code"] == -32600
    assert mixed_batch.json[2]["error"]["code"] == -32602
    assert invalid.status_code == 200
    assert invalid.json["error"]["code"] == -32600


def test_api_saved_templates_round_trip(tmp_path):
    app = create_app()
    app.config["TEMPLATE_FOLDER"] = str(tmp_path)
    client = app.test_client()
    template = {
        "badge_ids": [DEMO_BADGE.id],
        "side_badge_ids": {"front": [DEMO_BADGE.id], "back": []},
        "options": {"sides": ["front"], "mode": "grid", "front_text": "Ada"},
        "manual_placements": [{"layout_index": 0, "placement_index": 0, "x": 1.5}],
    }

    saved = client.post("/api/v1/templates", json={"name": "team-shirt", "template": template})
    listed = client.get("/api/v1/templates")
    fetched = client.get("/api/v1/templates/team-shirt")
    rejected_name = client.post("/api/v1/templates", json={"name": "../bad", "template": template})
    template_path = tmp_path / "team-shirt.json"

    assert saved.status_code == 201
    assert saved.json["name"] == "team-shirt"
    assert saved.json["template"] == template
    assert template_path.exists()
    assert listed.status_code == 200
    assert listed.json["templates"][0]["name"] == "team-shirt"
    assert listed.json["templates"][0]["badge_count"] == 1
    assert fetched.status_code == 200
    assert fetched.json["template"]["options"]["front_text"] == "Ada"
    assert fetched.json["template"]["side_badge_ids"] == {"front": [DEMO_BADGE.id], "back": []}
    assert rejected_name.status_code == 400
    assert rejected_name.json["error"]["code"] == "invalid_template_name"

    deleted = client.delete("/api/v1/templates/team-shirt")
    missing = client.get("/api/v1/templates/team-shirt")

    assert deleted.status_code == 200
    assert deleted.json == {"deleted": "team-shirt"}
    assert missing.status_code == 404


def test_mcp_saved_template_tools_and_resources(tmp_path):
    app = create_app()
    app.config["TEMPLATE_FOLDER"] = str(tmp_path)
    client = app.test_client()
    template = {
        "badge_ids": [DEMO_BADGE.id],
        "side_badge_ids": {"front": [DEMO_BADGE.id], "back": []},
        "options": {"sides": ["front"], "mode": "grid"},
        "manual_placements": [],
    }

    save = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "save_template", "arguments": {"name": "mcp-shirt", "template": template}},
        },
    )
    list_tool = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "list_saved_templates"}},
    )
    resource_list = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 3, "method": "resources/read", "params": {"uri": "tshirt://templates"}},
    )
    resource_item = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/read",
            "params": {"uri": "tshirt://templates/mcp-shirt"},
        },
    )
    delete = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "delete_saved_template", "arguments": {"name": "mcp-shirt"}},
        },
    )

    assert save.status_code == 200
    assert save.json["result"]["structuredContent"]["name"] == "mcp-shirt"
    assert list_tool.status_code == 200
    assert list_tool.json["result"]["structuredContent"]["templates"][0]["name"] == "mcp-shirt"
    assert resource_list.status_code == 200
    list_payload = json.loads(resource_list.json["result"]["contents"][0]["text"])
    assert list_payload["templates"][0]["name"] == "mcp-shirt"
    assert resource_item.status_code == 200
    item_payload = json.loads(resource_item.json["result"]["contents"][0]["text"])
    assert item_payload["template"] == template
    assert delete.status_code == 200
    assert delete.json["result"]["structuredContent"] == {"deleted": "mcp-shirt"}


def test_preview_uses_front_and_back_badge_assignments(monkeypatch):
    front_badge = Badge(
        id="front.svg",
        name="Front Badge",
        path="front.svg",
        raw_url="/static/demo-badge.svg",
        extension=".svg",
    )
    back_badge = Badge(
        id="back.svg",
        name="Back Badge",
        path="back.svg",
        raw_url="/static/demo-badge.svg",
        extension=".svg",
    )
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [front_badge, back_badge])
    app = create_app()

    response = app.test_client().post(
        "/preview",
        data={
            "front_badges": [front_badge.id],
            "back_badges": [back_badge.id],
            "sides": ["front", "back"],
        },
    )

    assert response.status_code == 200
    assert b"Front Badge on Front" in response.data
    assert b"Back Badge on Back" in response.data
    assert b"Front Badge on Back" not in response.data
    assert b"Back Badge on Front" not in response.data
    assert b'name="front_badges" value="front.svg"' in response.data
    assert b'name="back_badges" value="back.svg"' in response.data


def test_black_only_preview_uses_yellow_fabric_and_retains_contrast(monkeypatch):
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    response = create_app().test_client().post("/preview", data={
        "badges": [DEMO_BADGE.id], "sides": ["front"],
        "color_mode": "black_only", "ink_contrast": "2",
    })
    assert response.status_code == 200
    assert b'fill="#ffd800"' in response.data
    assert b'name="ink_contrast" value="2"' in response.data
    assert b'background represents the fabric' in response.data


@pytest.mark.parametrize("mode", ["black_only", "yellow_black"])
def test_preview_artwork_matches_export_conversion_and_revalidates_uploads(monkeypatch, tmp_path, mode):
    from PIL import Image
    from tshirt_templates.pdf import _recolour_artwork

    source = Image.new("RGBA", (3, 1))
    source.putdata([(0, 0, 0, 255), (255, 216, 0, 255), (255, 255, 255, 0)])
    encoded = BytesIO()
    source.save(encoded, format="PNG")
    path = tmp_path / "badge.png"
    path.write_bytes(encoded.getvalue())
    badge = Badge("badge.png", "Badge", "badge.png", "/uploads/badge.png", ".png", str(path))
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: [badge])
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [badge])
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path / "uploads")
    client = app.test_client()
    preview = client.post("/preview", data={"badges":badge.id, "sides":"front", "color_mode":mode, "ink_contrast":"0.5"})
    assert preview.status_code == 200
    assert b"/artwork/badge.png?" in preview.data
    assert b"<feColorMatrix" not in preview.data
    url = f"/artwork/badge.png?color_mode={mode}&ink_contrast=0.5"
    response = client.get(url)
    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert response.data == _recolour_artwork(encoded.getvalue(), False, mode, 0.5)
    assert client.get(url, headers={"If-None-Match":response.headers["ETag"]}).status_code == 304
    Image.new("RGBA", (3, 1), "black").save(path)
    updated = client.get(url, headers={"If-None-Match":response.headers["ETag"]})
    assert updated.status_code == 200
    assert updated.data != response.data


def test_converted_artwork_rejects_missing_badges_and_invalid_modes(monkeypatch):
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: [DEMO_BADGE])
    client = create_app().test_client()
    assert client.get("/artwork/missing.png?color_mode=black_only").status_code == 404
    assert client.get("/artwork/demo-badge.svg?color_mode=invalid").status_code == 400
