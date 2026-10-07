"""Regression coverage for complete, portable browser designs."""

import json
import sys
from math import isfinite
from types import SimpleNamespace

import pytest

from tshirt_templates.app import create_app
from tshirt_templates.badges import Badge
from tshirt_templates.cli import generate_pdf_from_file
from tshirt_templates.options import parse_layout_options


FIRST = Badge("first.svg", "First", "first.svg", "/static/demo-badge.svg", ".svg")
SECOND = Badge("second.svg", "Second", "second.svg", "/static/demo-badge.svg", ".svg")


@pytest.fixture
def browser(monkeypatch, tmp_path):
    contexts = []
    pdf_calls = []
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: [FIRST, SECOND])
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [FIRST, SECOND])
    monkeypatch.setattr(
        "tshirt_templates.app.render_template",
        lambda template, **context: contexts.append(context) or "preview",
    )
    monkeypatch.setitem(sys.modules, "tshirt_templates.pdf", SimpleNamespace(
        preflight_assets=lambda *args: [],
        verify_pdf_assets=lambda *args: [],
        render_pdf=lambda *args, **kwargs: pdf_calls.append((args, kwargs)) or b"%PDF-test",
    ))
    app = create_app()
    app.config.update(TESTING=True, TEMPLATE_FOLDER=str(tmp_path / "templates"), UPLOAD_FOLDER=str(tmp_path / "uploads"))
    return app.test_client(), contexts, pdf_calls


@pytest.mark.parametrize("field,value", [
    ("badge_size", "3.5"),
    ("badge_size", "0.5"),
    ("spacing", "0.8"),
    ("logo_size", "25.0"),
    ("front_logo_size", "20.0"),
    ("back_logo_size", "7.5"),
])
def test_converted_custom_sizes_preserve_physical_dimensions(field, value):
    initial = parse_layout_options({"unit": "cm", field: value}, lambda key: [])
    converted = parse_layout_options({"unit": "in", field: str(float(value) / 2.54)}, lambda key: [])
    restored = parse_layout_options({"unit": "cm", field: str(float(getattr(converted, field)) * 2.54)}, lambda key: [])

    assert getattr(converted, f"{field}_inches") == pytest.approx(getattr(initial, f"{field}_inches"), rel=1e-12)
    assert getattr(restored, f"{field}_inches") == pytest.approx(getattr(initial, f"{field}_inches"), rel=1e-12)


@pytest.mark.parametrize("field,value", [
    ("page_margin", "1.333333333333"),
    ("page_margin", "5"),
    ("panel_gap", "0.85"),
    ("curve_diameter", "2.5"),
    ("curve_diameter", "50"),
])
def test_continuous_dimensions_keep_precision_and_physical_limits(field, value):
    first = parse_layout_options({"unit": "cm", field: value}, lambda key: [])
    converted = parse_layout_options({"unit": "in", field: str(float(value) / 2.54)}, lambda key: [])

    assert getattr(first, f"{field}_inches") == pytest.approx(getattr(converted, f"{field}_inches"), rel=1e-12)


@pytest.mark.parametrize("invalid", ["nan", "inf", "-inf", "1000", "-1", "unreadable"])
def test_custom_sizes_reject_unsafe_values(invalid):
    options = parse_layout_options({"badge_size": invalid, "spacing": invalid, "logo_size": invalid}, lambda key: [])
    assert options.badge_size == "3.5"
    assert options.spacing == "0.5"
    assert options.logo_size == "5.0"


def test_options_reject_nonfinite_text_and_continuous_values():
    options = parse_layout_options({"front_text_x": "nan", "front_text_y": "inf", "page_margin": "nan", "curve_diameter": "inf", "export_dpi": "bad"}, lambda key: [])
    assert options.front_text_x is None
    assert options.front_text_y is None
    assert options.page_margin == "1.25"
    assert options.curve_diameter == "8"
    assert options.export_dpi == 150


def test_preview_design_contains_resolved_final_state_and_order(browser):
    client, contexts, _calls = browser
    response = client.post("/preview", data={
        "front_badges": [FIRST.id], "back_badges": [SECOND.id],
        "badge_order": [SECOND.id, FIRST.id],
        "sides": ["front", "back"], "unit": "in", "page_size": "letter",
        "badge_size": "1.37795275590551", "export_dpi": "300", "mirror": "off",
        "front_text": " Ada ", "front_text_x": "2.25", "front_text_y": "1.5",
        "manual_0_0_badge_id": FIRST.id, "manual_0_0_side": "front",
        "manual_0_0_x": "2.123456789", "manual_0_0_y": "3.987654321",
        "manual_0_0_rotation": "25", "locked_0_0": "on",
    })

    assert response.status_code == 200
    context = contexts[-1]
    design = context["design_data"]
    assert design["badge_ids"] == [SECOND.id, FIRST.id]
    assert design["side_badge_ids"] == {"front": [FIRST.id], "back": [SECOND.id]}
    assert design["options"]["mirror"] is False
    assert design["options"]["front_text"] == "Ada"
    assert design["options"]["front_text_x"] == 2.25
    assert design["options"]["front_text_y"] == 1.5
    assert design["options"]["export_dpi"] == 300
    assert not any(key.endswith("_inches") for key in design["options"])
    assert design["manual_placements"][0] == {
        "layout_index": 0, "placement_index": 0, "badge_id": FIRST.id, "side": "front",
        "x": pytest.approx(2.123456789), "y": pytest.approx(3.987654321),
        "rotation": 25, "locked": True,
    }
    assert context["mirror"] is False
    assert context["print_summary"]["page_count"] == 2
    assert context["print_summary"]["export_dpi"] == 300
    assert context["rerun_layout"] is False


@pytest.mark.parametrize("guard", [{"manual_0_0_badge_id": SECOND.id}, {"manual_0_0_side": "back"}])
def test_stale_manual_placement_and_lock_are_ignored(browser, guard):
    client, contexts, _calls = browser
    base = {"front_badges": [FIRST.id], "sides": ["front"]}
    client.post("/preview", data=base)
    original = contexts[-1]["design_data"]["manual_placements"][0]
    client.post("/preview", data={**base, **guard, "manual_0_0_x": "1", "manual_0_0_y": "2", "locked_0_0": "on"})
    restored = contexts[-1]["design_data"]["manual_placements"][0]

    assert restored == original
    assert restored["locked"] is False


def test_rerun_preserves_locked_position_and_replaces_unlocked_position(browser):
    client, contexts, _calls = browser
    response = client.post("/preview", data={
        "front_badges": [FIRST.id, SECOND.id], "sides": ["front"], "unit": "in",
        "rerun_layout": "on", "locked_0_0": "on",
        "manual_0_0_badge_id": FIRST.id, "manual_0_0_x": "1", "manual_0_0_y": "1",
        "manual_0_1_badge_id": SECOND.id, "manual_0_1_x": "1", "manual_0_1_y": "1",
    })

    assert response.status_code == 200
    first, second = contexts[-1]["design_data"]["manual_placements"]
    assert (first["x"], first["y"]) == pytest.approx((1, 1))
    assert (second["x"], second["y"]) != pytest.approx((1, 1))
    assert contexts[-1]["rerun_layout"] is True


def test_json_layout_respects_side_assignments_identity_guard_and_text_positions(browser):
    client, _contexts, _calls = browser
    payload = {
        "badge_ids": [FIRST.id, SECOND.id],
        "side_badge_ids": {"front": [FIRST.id], "back": [SECOND.id]},
        "options": {"unit": "in", "page_size": "letter", "front_text": "Ada", "front_text_x": 2.5, "front_text_y": 3, "export_dpi": 450},
        "manual_placements": [{"layout_index": 0, "placement_index": 0, "badge_id": SECOND.id, "x": 0, "y": 0}],
    }
    result = client.post("/api/v1/layouts/preview", json=payload).json

    assert [placement["badge_id"] for placement in result["layouts"][0]["placements"]] == [FIRST.id]
    assert [placement["badge_id"] for placement in result["layouts"][1]["placements"]] == [SECOND.id]
    assert result["layouts"][0]["placements"][0]["x"] != 0
    assert result["options"]["front_text_x"] == 2.5
    assert result["options"]["export_dpi"] == 450


def test_saved_full_design_is_renderable_via_cli_with_text_positions(browser, tmp_path):
    client, contexts, calls = browser
    client.post("/preview", data={
        "front_badges": [FIRST.id], "back_badges": [SECOND.id], "sides": ["front", "back"],
        "unit": "in", "page_size": "letter", "front_text": "Ada", "front_text_x": "2.5", "front_text_y": "3",
        "manual_0_0_badge_id": FIRST.id, "manual_0_0_x": "1.25", "manual_0_0_y": "1.5", "locked_0_0": "on",
        "export_dpi": "300",
    })
    design = contexts[-1]["design_data"]
    saved = client.post("/api/v1/templates", json={"name": "final-design", "template": design}).json
    assert saved["template"] == design

    template_path = tmp_path / "final-design.json"
    template_path.write_text(json.dumps(saved["template"]))
    output_path = tmp_path / "design.pdf"
    content = generate_pdf_from_file(template_path, output_path)
    assert content == output_path.read_bytes() == b"%PDF-test"
    args, kwargs = calls[-1]
    assert kwargs["panel_text"]["positions"]["front"] == {"x": 180, "y": 576}
    assert [layout.side for layout in args[2]] == ["front", "back"]
    assert args[2][0].placements[0].x == pytest.approx(1.25 * 72)


def test_explicit_replacement_protects_saved_design_and_legacy_clients(browser):
    client, _contexts, _calls = browser
    original = {"badge_ids": [FIRST.id], "options": {"front_text": "original"}}
    replacement = {"badge_ids": [FIRST.id], "options": {"front_text": "replacement"}}
    assert client.post("/api/v1/templates", json={"name": "design", "template": original, "overwrite": False}).status_code == 201
    conflict = client.post("/api/v1/templates", json={"name": "design", "template": replacement, "overwrite": False})
    assert conflict.status_code == 409
    assert conflict.json["error"]["code"] == "template_exists"
    assert client.get("/api/v1/templates/design").json["template"]["options"]["front_text"] == "original"
    assert client.post("/api/v1/templates", json={"name": "design", "template": replacement, "overwrite": True}).status_code == 201
    assert client.post("/api/v1/templates", json={"name": "design", "template": original}).status_code == 201


@pytest.mark.parametrize("mirror,filename", [
    ("on", "tshirt-badge-transfer-mirrored.pdf"),
    ("off", "tshirt-badge-design-unmirrored.pdf"),
])
def test_browser_pdf_filename_matches_actual_mirror_state(browser, mirror, filename):
    client, _contexts, calls = browser
    response = client.post("/pdf", data={"front_badges": [FIRST.id], "sides": ["front"], "mirror": mirror})
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == f"attachment; filename={filename}"
    assert calls[-1][1]["mirror"] is (mirror == "on")


def test_nonfinite_manual_coordinates_do_not_corrupt_preview(browser):
    client, contexts, _calls = browser
    client.post("/preview", data={"front_badges": [FIRST.id], "sides": ["front"], "manual_0_0_x": "nan", "manual_0_0_y": "inf", "manual_0_0_rotation": "nan"})
    placement = contexts[-1]["design_data"]["manual_placements"][0]
    assert all(isfinite(placement[key]) for key in ("x", "y", "rotation"))


def test_text_coordinate_conversion_does_not_pass_infinity_to_pdf(browser):
    client, _contexts, calls = browser
    response = client.post("/api/v1/pdfs", json={
        "badge_ids": [FIRST.id],
        "options": {"sides": ["front"], "unit": "in", "front_text": "Ada", "front_text_x": 1e308, "front_text_y": 1},
    })
    assert response.status_code == 200
    assert "positions" not in calls[-1][1]["panel_text"]


def test_unavailable_artwork_references_survive_preview_and_saved_design(browser):
    client, contexts, _calls = browser
    missing_id = "upload:removed.png"
    client.post("/preview", data={
        "front_badges": [missing_id, FIRST.id], "back_badges": [SECOND.id],
        "badge_order": [missing_id, SECOND.id, FIRST.id], "sides": ["front", "back"],
    })
    context = contexts[-1]
    design = context["design_data"]
    assert design["badge_ids"] == [missing_id, SECOND.id, FIRST.id]
    assert design["side_badge_ids"]["front"] == [missing_id, FIRST.id]
    assert [placement["badge_id"] for placement in design["manual_placements"]] == [FIRST.id, SECOND.id]
    assert context["missing_artwork"][0]["badge_id"] == missing_id
    assert context["missing_artwork"][0] in context["preflight_warnings"]
    saved = client.post("/api/v1/templates", json={"name": "missing-reference", "template": design})
    assert saved.json["template"] == design


@pytest.mark.parametrize("route", ["/pdf", "/proof.pdf", "/export.svg", "/export.png"])
def test_browser_export_blocks_unavailable_selected_artwork(browser, route):
    client, _contexts, calls = browser
    response = client.post(route, data={"front_badges": [FIRST.id, "upload:removed.png"], "sides": ["front"]})
    assert response.status_code == 422
    assert response.json["error"]["code"] == "missing_artwork"
    assert response.json["error"]["failures"][0]["badge_id"] == "upload:removed.png"
    assert not calls


def test_missing_artwork_on_inactive_side_does_not_block_pdf(browser):
    client, contexts, _calls = browser
    data = {"front_badges": [FIRST.id], "back_badges": ["upload:removed.png"], "sides": ["front"]}
    client.post("/preview", data=data)
    assert contexts[-1]["design_data"]["side_badge_ids"]["back"] == ["upload:removed.png"]
    assert contexts[-1]["missing_artwork"] == []
    assert client.post("/pdf", data=data).status_code == 200


def test_reordered_badge_copies_keep_individual_positions_and_locks(browser):
    client, contexts, _calls = browser
    data = {"front_badges": [SECOND.id, FIRST.id], "sides": ["front"], "copies": "2", "order": "selected"}
    for index, badge_id in enumerate([FIRST.id, FIRST.id, SECOND.id, SECOND.id]):
        data.update({
            f"manual_0_{index}_badge_id": badge_id, f"manual_0_{index}_side": "front",
            f"manual_0_{index}_x": str(index + 2), f"manual_0_{index}_y": str(index + 3),
            f"manual_0_{index}_rotation": str(index * 15),
        })
    data["locked_0_1"] = "on"
    assert client.post("/preview", data=data).status_code == 200
    placements = contexts[-1]["design_data"]["manual_placements"]
    assert [item["badge_id"] for item in placements] == [SECOND.id, SECOND.id, FIRST.id, FIRST.id]
    assert [item["x"] for item in placements] == pytest.approx([4, 5, 2, 3])
    assert [item["y"] for item in placements] == pytest.approx([5, 6, 3, 4])
    assert [item["rotation"] for item in placements] == [30, 45, 0, 15]
    assert [item["locked"] for item in placements] == [False, False, False, True]


def test_print_summary_and_resolution_warnings_use_actual_placed_sizes(browser, monkeypatch):
    client, contexts, _calls = browser
    checked_sizes = []
    monkeypatch.setattr(sys.modules["tshirt_templates.pdf"], "preflight_assets", lambda badges, size: checked_sizes.append(size) or [])
    client.post("/preview", data={
        "front_badges": [FIRST.id, SECOND.id], "sides": ["front"],
        "badge_size": "30", "unit": "cm", "mode": "m-pixels",
    })
    context = contexts[-1]
    sizes = context["print_summary"]["placed_badge_sizes"]
    assert sizes
    assert max(sizes) < 30
    assert len(checked_sizes) == 2
    assert max(checked_sizes) < 30 / 2.54
    for layout in context["layouts"]:
        for placement in layout.placements:
            assert round(placement.width / context["points_per_unit"], 2) in sizes
