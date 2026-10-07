"""Regression coverage for the design-to-print workflow in a real browser.

Run with ``pytest tests/test_browser_ux.py`` after installing Playwright. Tests
use a local Flask server and local artwork, so no upstream credentials or badge
repository access are needed. Set CHROMIUM_EXECUTABLE to select a system browser,
or install Playwright's Chromium with ``playwright install chromium``.
"""

# Optional browser dependencies must be checked before importing the app.
# ruff: noqa: E402

import os
import re
import shutil
from email import policy
from email.parser import BytesParser
from pathlib import Path
from threading import Thread
from urllib.parse import urljoin

import pytest

playwright = pytest.importorskip("playwright.sync_api")
pytest.importorskip("flask")

from flask import send_from_directory
from werkzeug.serving import WSGIRequestHandler, make_server

from tshirt_templates.app import create_app
from tshirt_templates.badges import Badge


BADGE_IDS = ["alpha.svg", "beta.svg", "gamma.svg"]


class QuietRequestHandler(WSGIRequestHandler):
    def log_request(self, code="-", size="-"):
        pass


@pytest.fixture(scope="module")
def chromium():
    executable = os.environ.get("CHROMIUM_EXECUTABLE") or shutil.which("chromium")
    with playwright.sync_playwright() as manager:
        try:
            browser = manager.chromium.launch(
                executable_path=executable,
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
        except playwright.Error as error:
            pytest.skip(f"Chromium is unavailable: {error}")
        yield browser
        browser.close()


@pytest.fixture
def browser_server(monkeypatch, tmp_path):
    artwork_dir = tmp_path / "artwork"
    artwork_dir.mkdir()
    badges = []
    for index, badge_id in enumerate(BADGE_IDS):
        path = artwork_dir / badge_id
        path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" '
            'viewBox="0 0 300 300"><circle cx="150" cy="150" r="140" '
            f'fill="{["#999999", "#ffff00", "#000000"][index]}"/>'
            '<path d="M70 140h160v20H70z" fill="white"/></svg>',
            encoding="utf-8",
        )
        badges.append(
            Badge(
                id=badge_id,
                name=["Archivist", "Assembly Regular", "Been There"][index],
                path=badge_id,
                raw_url=f"/test-artwork/{badge_id}",
                extension=".svg",
                local_path=str(path),
            )
        )
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: badges)
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: badges)
    app = create_app()
    app.config.update(
        TESTING=True,
        UPLOAD_FOLDER=str(tmp_path / "uploads"),
        TEMPLATE_FOLDER=str(tmp_path / "templates"),
    )
    Path(app.config["UPLOAD_FOLDER"]).mkdir()
    Path(app.config["TEMPLATE_FOLDER"]).mkdir()

    @app.get("/test-artwork/<path:filename>")
    def artwork(filename):
        return send_from_directory(artwork_dir, filename)

    server = make_server("127.0.0.1", 0, app, threaded=True, request_handler=QuietRequestHandler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    worker.join(timeout=5)


@pytest.fixture
def page(chromium, browser_server):
    context = chromium.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    page.set_default_timeout(10000)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    # The test assets are local; avoid waiting for decorative remote logos.
    page.route("https://**", lambda route: route.abort())
    page.goto(browser_server, wait_until="domcontentloaded")
    page.locator("[data-language-switch]").click()
    playwright.expect(page.locator("html")).to_have_attribute("lang", "en")
    yield page
    context.close()
    assert not errors, f"Browser JavaScript errors: {errors}"


def _preview(page):
    page.locator("#template-actions .actions-primary button").first.click()
    playwright.expect(page.locator("#manual-layout-form")).to_be_visible()
    playwright.expect(page.locator(".draggable-badge").first).to_be_visible()


def _open_coordinates(page):
    details = page.locator(".preview-coordinate-details")
    if details.get_attribute("open") is None:
        details.locator(":scope > summary").click()


def _open_library(page):
    details = page.locator(".template-library")
    if details.get_attribute("open") is None:
        details.locator(":scope > summary").click()


def _order(page):
    return page.locator("#badge-grid input[name=front_badges]").evaluate_all(
        "inputs => inputs.map(input => input.value)"
    )


def _reorder_badges(page):
    card = page.locator('.badge-card:has(input[value="gamma.svg"])')
    card.locator('[data-move-badge="up"]').click()
    card.locator('[data-move-badge="up"]').click()
    assert _order(page) == ["gamma.svg", "alpha.svg", "beta.svg"]


def _geometry(page):
    return page.locator(".draggable-badge").evaluate_all(
        """badges => badges.map(badge => ({
          id: badge.dataset.badgeId,
          side: badge.dataset.side,
          x: Number(badge.dataset.x), y: Number(badge.dataset.y),
          width: Number(badge.dataset.width), height: Number(badge.dataset.height),
          rotation: Number(badge.dataset.rotation),
          locked: document.querySelector(`.placement-lock[data-key="${badge.dataset.key}"]`).checked
        }))"""
    )


def _assert_geometry(actual, expected, tolerance=0.3):
    assert len(actual) == len(expected)
    for after, before in zip(actual, expected):
        for field in ("id", "side", "locked"):
            assert after[field] == before[field]
        for field in ("x", "y", "width", "height", "rotation"):
            assert after[field] == pytest.approx(before[field], abs=tolerance), field


def _text_position(page, side="front"):
    return page.locator(f'.draggable-panel-text[data-side="{side}"]').evaluate(
        "text => [Number(text.dataset.x), Number(text.dataset.y)]"
    )


def _fill_number(page, selector, value):
    page.locator(selector).fill(str(value))
    page.locator(selector).press("Tab")


def _submitted_fields(request):
    content_type = request.headers["content-type"]
    message = BytesParser(policy=policy.default).parsebytes(
        f"Content-Type: {content_type}\r\n\r\n".encode() + request.post_data_buffer
    )
    return [
        (part.get_param("name", header="content-disposition"), part.get_payload(decode=True))
        for part in message.iter_parts()
    ]


def _make_finished_edits(page):
    badge = page.locator('.draggable-badge[data-key="0_0"]')
    badge.click()
    page.locator('.quick-move[data-direction="right"]').click()
    page.locator("#quick-rotate").click()
    page.locator("#quick-lock").click()
    text = page.locator('.draggable-panel-text[data-side="front"]')
    text.focus()
    text.press("ArrowRight")
    text.press("ArrowDown")
    _open_coordinates(page)
    page.locator('.text-label-input[data-side="front"]').fill("Edited team")
    page.locator('.text-label-input[data-side="front"]').press("Tab")


def test_draft_keeps_order_assignments_finished_edits_and_export_settings(page):
    _reorder_badges(page)
    page.locator('input[name=back_badges][value="alpha.svg"]').uncheck()
    page.locator('input[name=front_badges][value="beta.svg"]').uncheck()
    page.locator("input[name=front_text]").fill("Our team")
    page.locator("input[name=back_text]").fill("Madrid")
    page.locator(".print-options-panel > summary").click()
    page.locator("select[name=export_dpi]").select_option("300")
    _preview(page)
    _make_finished_edits(page)
    expected = _geometry(page)
    expected_text = _text_position(page)
    page.reload(wait_until="domcontentloaded")
    _assert_geometry(_geometry(page), expected)
    assert _text_position(page) == pytest.approx(expected_text, abs=0.3)
    playwright.expect(page.locator('.text-label-input[data-side="front"]')).to_have_value("Edited team")
    page.locator("#adjust-settings").click()
    assert _order(page) == ["gamma.svg", "alpha.svg", "beta.svg"]
    playwright.expect(page.locator("input[name=front_text]")).to_have_value("Edited team")
    playwright.expect(page.locator("select[name=export_dpi]")).to_have_value("300")
    playwright.expect(page.locator('input[name=back_badges][value="alpha.svg"]')).not_to_be_checked()
    playwright.expect(page.locator('input[name=front_badges][value="beta.svg"]')).not_to_be_checked()
    page.reload(wait_until="domcontentloaded")
    playwright.expect(page.locator("input[name=front_text]")).to_have_value("Edited team")
    _preview(page)
    _assert_geometry(_geometry(page), expected)
    assert _text_position(page) == pytest.approx(expected_text, abs=0.3)
    # Reloading a submitted preview may resubmit the older POST body. The tab's
    # newer draft must still win over it.
    page.reload(wait_until="domcontentloaded")
    _assert_geometry(_geometry(page), expected)
    assert _text_position(page) == pytest.approx(expected_text, abs=0.3)


def test_units_preserve_physical_sizes_and_curve_preset_changes_only_diameter(page):
    page.locator("#badge-size-select").select_option("5.0")
    page.locator(".spacing-panel > summary").click()
    page.locator("#spacing-select").select_option("0.5")
    _fill_number(page, "#page-margin-input", 1.6)
    _fill_number(page, "#panel-gap-input", 0.7)
    page.locator(".curve-panel > summary").click()
    _fill_number(page, "#curve-diameter-input", 8.9)
    physical = {
        "#badge-size-select": 5.0,
        "#spacing-select": 0.5,
        "#page-margin-input": 1.6,
        "#panel-gap-input": 0.7,
        "#curve-diameter-input": 8.9,
    }
    page.locator("#unit-select").select_option("in")
    for selector, centimeters in physical.items():
        assert float(page.locator(selector).input_value()) * 2.54 == pytest.approx(centimeters, abs=0.02)
    # 5 cm is not exactly a preset inch size. Retaining the physical custom
    # amount avoids the previous reset to the default 2 in.
    assert float(page.locator("#badge-size-select").input_value()) != 2.0
    page.locator("#unit-select").select_option("cm")
    for selector, centimeters in physical.items():
        assert float(page.locator(selector).input_value()) == pytest.approx(centimeters, abs=0.03)
    untouched = {selector: page.locator(selector).input_value() for selector in physical if "curve" not in selector}
    page.locator("#curve-device-select").select_option("mug")
    assert float(page.locator("#curve-diameter-input").input_value()) == pytest.approx(8.2)
    for selector, value in untouched.items():
        assert page.locator(selector).input_value() == value


def test_finished_design_save_load_retains_layout_and_supports_delete_recovery(page):
    _reorder_badges(page)
    page.locator("input[name=front_text]").fill("Team")
    page.locator(".print-options-panel > summary").click()
    page.locator("select[name=export_dpi]").select_option("300")
    _preview(page)
    _make_finished_edits(page)
    expected = _geometry(page)
    expected_text = _text_position(page)
    page.locator(".preview-save-design > summary").click()
    page.locator("#finished-design-name").fill("finished-team")
    with page.expect_response(lambda response: response.url.endswith("/api/v1/templates") and response.request.method == "POST") as response_info:
        page.locator("#save-finished-design").click()
    response = response_info.value
    assert response.status == 201
    saved = response.json()["template"]
    assert int(saved["options"]["export_dpi"]) == 300
    assert saved["manual_placements"]
    assert any(placement.get("locked") for placement in saved["manual_placements"])
    page.locator("#adjust-settings").click()
    page.locator("#start-blank").click()
    if page.locator("#confirm-new-design").is_visible():
        page.locator("#confirm-new-design").click()
    _open_library(page)
    page.locator("#saved-template-select").select_option("finished-team")
    page.locator("#load-design-template").click()
    playwright.expect(page.locator("input[name=front_text]")).to_have_value("Edited team")
    assert _order(page) == ["gamma.svg", "alpha.svg", "beta.svg"]
    playwright.expect(page.locator("select[name=export_dpi]")).to_have_value("300")
    page.locator("#delete-design-template").click()
    playwright.expect(page.locator('#saved-template-select option[value="finished-team"]')).to_have_count(0)
    page.locator("#template-delete-undo").click()
    playwright.expect(page.locator('#saved-template-select option[value="finished-team"]')).to_have_count(1)
    _preview(page)
    _assert_geometry(_geometry(page), expected)
    assert _text_position(page) == pytest.approx(expected_text, abs=0.3)


def test_changing_units_after_manual_edits_keeps_physical_layout(page):
    page.locator("input[name=front_text]").fill("Team")
    _preview(page)
    _make_finished_edits(page)
    expected = _geometry(page)
    expected_text = _text_position(page)
    page.locator("#adjust-settings").click()
    page.locator("#unit-select").select_option("in")
    _preview(page)
    _assert_geometry(_geometry(page), expected)
    assert _text_position(page) == pytest.approx(expected_text, abs=0.3)
    page.locator("#adjust-settings").click()
    page.locator("#unit-select").select_option("cm")
    _preview(page)
    _assert_geometry(_geometry(page), expected)
    assert _text_position(page) == pytest.approx(expected_text, abs=0.3)


def test_named_design_replacement_requires_explicit_confirmation(page):
    _open_library(page)
    page.locator("#template-name").fill("our-team")
    with page.expect_response(lambda response: response.url.endswith("/api/v1/templates") and response.request.method == "POST"):
        page.locator("#save-design-template").click()
    page.locator("input[name=front_text]").fill("Replacement")
    page.locator("#save-design-template").click()
    playwright.expect(page.locator("#confirm-template-replace")).to_be_visible()
    original = page.request.get(urljoin(page.url, "/api/v1/templates/our-team")).json()
    assert original["template"]["options"].get("front_text", "") != "Replacement"
    with page.expect_response(lambda response: response.url.endswith("/api/v1/templates") and response.request.method == "POST") as response_info:
        page.locator("#confirm-template-replace").click()
    assert response_info.value.status == 201
    updated = page.request.get(urljoin(page.url, "/api/v1/templates/our-team")).json()
    assert updated["template"]["options"]["front_text"] == "Replacement"


def test_preview_color_controls_update_artwork_and_exports_without_moving_design(page):
    page.locator("input[name=front_text]").fill("Team")
    _preview(page)
    _make_finished_edits(page)
    expected = _geometry(page)
    image = page.locator('.draggable-badge[data-key="0_0"] image')
    original_url = image.get_attribute("href")
    page.locator("#preview-color-mode").select_option("black_only")
    page.locator("#preview-ink-contrast").select_option("0.5")
    playwright.expect(image).to_have_attribute("href", re.compile(r"color_mode=black_only.*ink_contrast=0\.5"))
    playwright.expect(page.locator("#fabric-preview-note")).to_be_visible()
    _assert_geometry(_geometry(page), expected, tolerance=0)
    page.locator("#compare-original").check()
    playwright.expect(image).to_have_attribute("href", original_url)
    # Comparing original art must not silently change the export mode.
    playwright.expect(page.locator('#manual-layout-form input[name="color_mode"]')).to_have_value("black_only")
    page.locator("#compare-original").uncheck()
    page.locator("#preview-color-mode").select_option("yellow_black")
    page.locator("#preview-ink-contrast").select_option("1.5")
    playwright.expect(image).to_have_attribute("href", re.compile(r"color_mode=yellow_black.*ink_contrast=1\.5"))
    playwright.expect(page.locator('#manual-layout-form input[name="ink_contrast"]')).to_have_value("1.5")
    _assert_geometry(_geometry(page), expected, tolerance=0)
    page.locator("#preview-color-mode").select_option("full_color")
    playwright.expect(page.locator("#preview-contrast-control")).to_be_hidden()
    playwright.expect(image).to_have_attribute("href", original_url)


def test_history_groups_a_drag_and_supports_rotation_alignment_reset_and_text(page):
    page.locator("input[name=front_text]").fill("Team")
    _preview(page)
    initial = _geometry(page)
    badge = page.locator('.draggable-badge[data-key="0_0"]')
    badge.scroll_into_view_if_needed()
    box = badge.bounding_box()
    start_x, start_y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(start_x, start_y)
    page.mouse.down()
    page.mouse.move(start_x + 22, start_y + 13, steps=8)
    page.mouse.up()
    dragged = _geometry(page)
    assert dragged[0]["x"] != initial[0]["x"]
    page.locator("#undo-layout").click()
    _assert_geometry(_geometry(page), initial, tolerance=0.01)
    playwright.expect(page.locator("#undo-layout")).to_be_disabled()
    page.locator("#redo-layout").click()
    _assert_geometry(_geometry(page), dragged, tolerance=0.01)
    page.locator("#quick-rotate").click()
    rotated = _geometry(page)
    assert abs(rotated[0]["rotation"] - dragged[0]["rotation"]) == 15
    page.locator("#undo-layout").click()
    _assert_geometry(_geometry(page), dragged, tolerance=0.01)
    _open_coordinates(page)
    page.locator('[data-alignment="right"]').click()
    aligned = _geometry(page)
    assert aligned[0]["x"] != dragged[0]["x"]
    page.locator("#undo-layout").click()
    _assert_geometry(_geometry(page), dragged, tolerance=0.01)
    page.locator("#reset-manual-layout").click()
    _assert_geometry(_geometry(page), initial, tolerance=0.3)
    page.locator("#undo-layout").click()
    _assert_geometry(_geometry(page), dragged, tolerance=0.01)
    original_text = _text_position(page)
    text = page.locator('.draggable-panel-text[data-side="front"]')
    text.focus()
    text.press("ArrowRight")
    assert _text_position(page) != original_text
    page.locator("#undo-layout").click()
    assert _text_position(page) == pytest.approx(original_text)


def test_locked_badges_ignore_visible_move_controls_and_keyboard(page):
    _preview(page)
    badge = page.locator('.draggable-badge[data-key="0_0"]')
    badge.click()
    page.locator("#quick-lock").click()
    locked = _geometry(page)
    assert locked[0]["locked"]
    playwright.expect(page.locator('.quick-move[data-direction="right"]')).to_be_disabled()
    playwright.expect(page.locator("#quick-rotate")).to_be_disabled()
    badge.focus()
    badge.press("ArrowRight")
    _assert_geometry(_geometry(page), locked, tolerance=0)
    page.locator("#quick-lock").click()
    page.locator('.quick-move[data-direction="right"]').click()
    assert _geometry(page)[0]["x"] > locked[0]["x"]


def test_mirror_off_pdf_label_filename_and_failed_export_preserve_design(page):
    page.locator('input[type=checkbox][name=mirror]').uncheck()
    _preview(page)
    pdf_button = page.locator("#manual-layout-form .actions-primary button").first
    playwright.expect(pdf_button).to_have_text("Download PDF")
    playwright.expect(page.locator("#summary-mirror")).to_contain_text("Off")
    badge = page.locator('.draggable-badge[data-key="0_0"]')
    badge.focus()
    badge.press("ArrowRight")
    expected = _geometry(page)
    submissions = []

    def fail_first_download(route):
        submissions.append(_submitted_fields(route.request))
        if len(submissions) == 1:
            route.fulfill(
                status=500,
                content_type="application/json",
                body='{"error":{"message":"Download could not be generated. Please try again."}}',
            )
        else:
            route.continue_()

    page.route("**/pdf", fail_first_download)
    pdf_button.click()
    feedback = page.locator("#manual-layout-form .download-feedback")
    playwright.expect(feedback).to_contain_text("Download could not be generated")
    _assert_geometry(_geometry(page), expected, tolerance=0)
    with page.expect_download() as download_info:
        feedback.locator("button").click()
    download = download_info.value
    assert download.suggested_filename == "tshirt-badge-design-unmirrored.pdf"
    assert download.failure() is None
    assert submissions[0] == submissions[1]
    _assert_geometry(_geometry(page), expected, tolerance=0)


def test_overlap_warning_survives_color_and_status_changes_until_resolved(page):
    _preview(page)
    _open_coordinates(page)
    target_x = page.locator('input[name="manual_0_1_x"]').input_value()
    target_y = page.locator('input[name="manual_0_1_y"]').input_value()
    _fill_number(page, 'input[name="manual_0_0_x"]', target_x)
    _fill_number(page, 'input[name="manual_0_0_y"]', target_y)
    warnings = page.locator("#collision-warnings")
    playwright.expect(warnings).to_contain_text(re.compile("overlap", re.IGNORECASE))
    page.locator("#preview-color-mode").select_option("black_only")
    badge = page.locator('.draggable-badge[data-key="0_0"]')
    badge.focus()
    badge.press("ArrowRight")
    playwright.expect(page.locator("#preview-status")).to_contain_text("nudged with keyboard")
    playwright.expect(warnings).to_contain_text(re.compile("overlap", re.IGNORECASE))
    page.locator("#reset-manual-layout").click()
    playwright.expect(warnings).not_to_contain_text(re.compile("overlap", re.IGNORECASE))


def test_missing_artwork_warns_blocks_incomplete_pdf_and_supports_retry(page, tmp_path):
    asset = tmp_path / "artwork" / "alpha.svg"
    original_artwork = asset.read_bytes()
    asset.unlink()
    _preview(page)
    warnings = page.locator("#preview-warnings")
    playwright.expect(warnings).to_contain_text("Archivist")
    badge = page.locator('.draggable-badge[data-key="0_0"]')
    badge.focus()
    badge.press("ArrowRight")
    expected = _geometry(page)
    playwright.expect(warnings).to_contain_text("Archivist")
    pdf_button = page.locator("#manual-layout-form .actions-primary button").first
    pdf_button.click()
    feedback = page.locator("#manual-layout-form .download-feedback")
    playwright.expect(feedback).to_contain_text("Archivist")
    playwright.expect(feedback.locator("button")).to_be_visible()
    _assert_geometry(_geometry(page), expected, tolerance=0)
    asset.write_bytes(original_artwork)
    with page.expect_download() as download_info:
        feedback.locator("button").click()
    assert download_info.value.failure() is None
    _assert_geometry(_geometry(page), expected, tolerance=0)
    playwright.expect(warnings).not_to_contain_text("Archivist")


def test_preview_can_add_text_undo_and_recover_after_reload(page):
    _preview(page)
    label = page.locator('.text-label-input[data-side="front"]')
    text = page.locator('.draggable-panel-text[data-side="front"]')
    playwright.expect(label).to_be_visible()
    playwright.expect(text).to_be_hidden()
    label.fill("New team label")
    label.press("Tab")
    playwright.expect(text).to_be_visible()
    playwright.expect(text.locator("text")).to_have_text("New team label")
    page.locator("#undo-layout").click()
    playwright.expect(label).to_have_value("")
    playwright.expect(text).to_be_hidden()
    page.locator("#redo-layout").click()
    playwright.expect(text).to_be_visible()
    page.reload(wait_until="domcontentloaded")
    playwright.expect(label).to_have_value("New team label")
    playwright.expect(text.locator("text")).to_have_text("New team label")
    page.locator("#adjust-settings").click()
    playwright.expect(page.locator("input[name=front_text]")).to_have_value("New team label")


def test_reordering_and_changing_units_preserves_finished_badge_edits(page):
    page.locator("input[name=front_text]").fill("Team")
    _preview(page)
    _make_finished_edits(page)
    expected = {(item["side"], item["id"]): item for item in _geometry(page)}
    expected_text = _text_position(page)
    page.locator("#adjust-settings").click()
    _reorder_badges(page)
    page.locator("#unit-select").select_option("in")
    _preview(page)
    actual = {(item["side"], item["id"]): item for item in _geometry(page)}
    for identity, before in expected.items():
        _assert_geometry([actual[identity]], [before])
    assert _text_position(page) == pytest.approx(expected_text, abs=0.3)
    playwright.expect(page.locator('.text-label-input[data-side="front"]')).to_have_value("Edited team")


def test_presets_and_contextual_controls_preserve_inactive_values(page):
    playwright.expect(page.locator("#ink-contrast-control")).to_be_hidden()
    playwright.expect(page.locator("#front-logo-size-control")).to_be_hidden()
    page.locator('input[type=checkbox][name=mirror]').uncheck()
    page.locator('[data-design-preset="black_only"]').click()
    playwright.expect(page.locator("select[name=color_mode]")).to_have_value("black_only")
    playwright.expect(page.locator("#ink-contrast-control")).to_be_visible()
    playwright.expect(page.locator('input[type=checkbox][name=mirror]')).not_to_be_checked()
    page.locator("select[name=ink_contrast]").select_option("0.5")
    page.locator("select[name=color_mode]").select_option("full_color")
    playwright.expect(page.locator("#ink-contrast-control")).to_be_hidden()
    page.locator("select[name=color_mode]").select_option("yellow_black")
    playwright.expect(page.locator("select[name=ink_contrast]")).to_have_value("0.5")
    page.locator('input[name=logo_sides][value="front"]').check()
    playwright.expect(page.locator("#front-logo-size-control")).to_be_visible()
    page.locator("#front-logo-size-select").select_option("2.5")
    page.locator('input[name=logo_sides][value="front"]').uncheck()
    playwright.expect(page.locator("#front-logo-size-control")).to_be_hidden()
    page.locator('input[name=logo_sides][value="front"]').check()
    playwright.expect(page.locator("#front-logo-size-select")).to_have_value("2.5")


@pytest.mark.parametrize("language", ["es", "en"])
def test_dynamic_language_and_mobile_controls_without_horizontal_overflow(page, language):
    page.set_viewport_size({"width": 375, "height": 812})
    if language == "es":
        page.locator("[data-language-switch]").click()
    playwright.expect(page.locator("html")).to_have_attribute("lang", language)
    page.locator("#front-visible-badges").click()
    notice = page.locator("#side-selection-notice").inner_text().lower()
    assert "trasero" in notice if language == "es" else "back" in notice
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
    _preview(page)
    playwright.expect(page.locator("html")).to_have_attribute("lang", language)
    badge = page.locator('.draggable-badge[data-key="0_0"]')
    badge.focus()
    badge.press("Enter")
    playwright.expect(badge).to_have_attribute("aria-pressed", "true")
    badge.press("ArrowRight")
    status = page.locator("#preview-status").inner_text().lower()
    assert "insignia" in status if language == "es" else "badge" in status
    playwright.expect(page.locator("#undo-layout")).to_be_enabled()
    page.locator("#undo-layout").click()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
    page.locator("#manual-layout-form .export-menu > summary").click()
    playwright.expect(page.locator('button[formaction="/export.png"]')).to_be_visible()
    page.locator("#manual-layout-form .export-menu").press("Escape")
    playwright.expect(page.locator('button[formaction="/export.png"]')).to_be_hidden()
