"""Flask web application for badge-based t-shirt sublimation templates."""

from __future__ import annotations

import base64
import binascii
import importlib
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from flask import Flask, Response, flash, get_flashed_messages, jsonify, redirect, render_template, request, send_from_directory, url_for

from .badges import Badge, badge_category, get_badges_by_id, list_badges, order_badges, refresh_badges
from .layout import PanelLayout, Placement, page_size_points, place_badges
from .options import (
    BADGE_AMOUNTS,
    CENTIMETERS_PER_INCH,
    DEFAULT_BADGE_AMOUNTS,
    CURVE_DEVICE_DIAMETERS,
    DEFAULT_CURVE_DEVICE,
    DEFAULT_CURVE_DIAMETER_AMOUNTS,
    DEFAULT_LOGO_AMOUNTS,
    DEFAULT_PAGE_MARGIN_AMOUNTS,
    DEFAULT_PANEL_GAP_AMOUNTS,
    DEFAULT_SPACING_AMOUNTS,
    DEFAULT_TEXT_SIZE,
    DEFAULT_UNIT,
    LOGO_AMOUNTS,
    SPACING_AMOUNTS,
    parse_layout_options,
)
from .uploads import (
    delete_uploaded_badge,
    list_uploaded_badges,
    replace_uploaded_badge_bytes_with_warnings,
    save_uploaded_badge_bytes_with_warnings,
    save_uploaded_badges_with_warnings,
    upload_warnings_to_dicts,
)

LAYOUT_MODES = {
    "grid": "Grid",
    "rows": "Staggered rows",
    "diagonal": "Diagonal sash",
    "scatter": "Organic scatter",
    "circle": "Circle wreath",
    "spiral": "Spiral trail",
    "wave": "Wave ribbon",
    "border": "Border frame",
    "m-pixels": "M pixel shape",
    "m-pixels-no-shrink": "M pixel shape (no shrink)",
}
LAYOUT_MODE_DETAILS = {
    "grid": {
        "label": LAYOUT_MODES["grid"],
        "description": "Centered rows and columns with automatic spacing reduction for dense selections.",
    },
    "rows": {
        "label": LAYOUT_MODES["rows"],
        "description": "Staggered rows with alternating offsets and automatic spacing reduction.",
    },
    "diagonal": {
        "label": LAYOUT_MODES["diagonal"],
        "description": "Badges placed along a diagonal sash.",
    },
    "scatter": {
        "label": LAYOUT_MODES["scatter"],
        "description": "Deterministic pseudo-random positions and rotations.",
    },
    "circle": {
        "label": LAYOUT_MODES["circle"],
        "description": "Badges arranged around an oval wreath.",
    },
    "spiral": {
        "label": LAYOUT_MODES["spiral"],
        "description": "Badges trail outward from the panel center.",
    },
    "wave": {
        "label": LAYOUT_MODES["wave"],
        "description": "Badges follow a horizontal sine-wave ribbon.",
    },
    "border": {
        "label": LAYOUT_MODES["border"],
        "description": "Badges wrap around the panel edges.",
    },
    "m-pixels": {
        "label": LAYOUT_MODES["m-pixels"],
        "description": (
            "Badges fill a pixel-art capital M, expanding to denser M grids and scaling down "
            "only as needed to stay inside the panel."
        ),
    },
    "m-pixels-no-shrink": {
        "label": LAYOUT_MODES["m-pixels-no-shrink"],
        "description": (
            "Badges fill a fixed-size pixel-art capital M without reducing badge size; overflow "
            "falls back to one buffered line above, buffered lines above and below, a "
            "buffered square frame, then a double-square frame."
        ),
        "fallbacks": [
            "line-above",
            "lines-above-and-below",
            "square-frame",
            "double-square-frame",
        ],
        "shrinks_badges": False,
    },
}
PAGE_SIZES = {
    "a4": "A4",
    "a3": "A3",
    "letter": "US Letter",
}
ORIENTATIONS = {
    "portrait": "Portrait",
    "landscape": "Landscape",
}
ORDER_MODES = {
    "selected": "Selection order",
    "alphabetical": "Alphabetical",
    "category": "By category",
}
UNITS = {
    "cm": "Centimeters",
    "in": "Inches",
}


def _log_event(app: Flask, level: int, event: str, **fields: object) -> None:
    """Emit a machine-parseable application event through Flask's logger."""

    payload = {"event": event, **fields}
    app.logger.log(level, json.dumps(payload, sort_keys=True, default=str))


TEXT_FONTS = {
    "ubuntu": "Ubuntu",
    "fredoka-one": "Fredoka One",
    "helvetica": "Helvetica",
    "times": "Times",
    "courier": "Courier",
    "dejavu": "DejaVu Sans",
}
MIN_UI_BADGE_AMOUNTS = {"cm": 2.5, "in": 1.0}
BADGE_SIZE_OPTIONS = {
    unit: [
        amount
        for amount in sorted(amounts, key=float)
        if float(amount) >= MIN_UI_BADGE_AMOUNTS[unit]
    ]
    for unit, amounts in BADGE_AMOUNTS.items()
}
SPACING_OPTIONS = {
    unit: sorted(amounts, key=float) for unit, amounts in SPACING_AMOUNTS.items()
}
LOGO_SIZE_OPTIONS = {unit: sorted(amounts, key=float) for unit, amounts in LOGO_AMOUNTS.items()}
COPY_OPTIONS = list(range(1, 25))
CURVE_DEVICE_OPTIONS = {
    "custom": "Custom diameter",
    "mug": "Standard mug",
    "skinny-tumbler": "Skinny tumbler / canteen",
    "canteen": "Wide canteen",
}
APP_VERSION = "0.1.0"
MCP_TRANSPORT = "streamable-http-json-rpc"
MCP_BADGES_URI_TEMPLATE = "tshirt://badges{?order,logo_sides,include_logo,refresh}"
MCP_METHODS = [
    "initialize",
    "ping",
    "notifications/initialized",
    "tools/list",
    "tools/call",
    "resources/list",
    "resources/read",
    "resources/templates/list",
    "prompts/list",
    "prompts/get",
]
MCP_PORT_NOTE = (
    "MCP compatibility depends on configuring clients with the reachable /mcp URL; "
    "there is no required MCP port. Use --port only to avoid conflicts or expose the server."
)


MANUAL_SELECTION_BADGE_FILENAMES = {"badge-template.png"}


def is_manual_selection_badge(badge: Badge) -> bool:
    """Return True for catalog badges that should not be auto-selected."""

    filename = badge.path.rsplit("/", 1)[-1].lower()
    return filename in MANUAL_SELECTION_BADGE_FILENAMES


def default_selected_badge_ids(badges: list[Badge]) -> list[str]:
    """Return badge ids selected on first page load."""

    return [badge.id for badge in badges if not is_manual_selection_badge(badge)]


LOGO_BADGE = Badge(
    id="makespace-logo",
    name="MakeSpace Madrid Logo",
    path="assets/images/logo/makespace-bk.svg",
    raw_url=(
        "https://raw.githubusercontent.com/makespacemadrid/"
        "makespacemadrid.github.io/main/assets/images/logo/makespace-bk.svg"
    ),
    extension=".svg",
)


def points_per_unit(unit: str) -> float:
    """Return the number of PDF points in one displayed unit."""

    if unit == "cm":
        return 72.0 / CENTIMETERS_PER_INCH
    return 72.0


def append_logo_placements(
    layouts: list[PanelLayout],
    logo_size_inches: float | dict[str, float],
    logo_sides: list[str] | None = None,
) -> list[PanelLayout]:
    """Append the optional MakeSpace logo placement to selected panel layouts."""

    selected_logo_sides = set(logo_sides or ["front", "back"])
    adjusted_layouts: list[PanelLayout] = []
    for layout in layouts:
        if layout.side not in selected_logo_sides:
            adjusted_layouts.append(layout)
            continue
        side_logo_size_inches = (
            logo_size_inches.get(layout.side, logo_size_inches.get("default", 0.0))
            if isinstance(logo_size_inches, dict)
            else logo_size_inches
        )
        logo_size = side_logo_size_inches * 72.0
        width = min(logo_size, layout.width)
        height = min(logo_size, layout.height)
        margin = min(18.0, max(0.0, (layout.height - height) / 2))
        placement = Placement(
            badge_id=LOGO_BADGE.id,
            x=layout.x + (layout.width - width) / 2,
            y=layout.y + margin,
            width=width,
            height=height,
        )
        adjusted_layouts.append(
            PanelLayout(
                layout.side,
                layout.x,
                layout.y,
                layout.width,
                layout.height,
                [*layout.placements, placement],
            )
        )
    return adjusted_layouts


def badge_to_dict(badge: Badge) -> dict[str, str | None]:
    """Serialize a badge for JSON APIs and MCP tools."""

    if badge.id == LOGO_BADGE.id:
        source = "logo"
    elif badge.local_path:
        source = "upload"
    elif badge.raw_url.startswith("/static/demo-badge.svg"):
        source = "fallback"
    else:
        source = "upstream"
    return {
        "id": badge.id,
        "name": badge.name,
        "path": badge.path,
        "raw_url": badge.raw_url,
        "extension": badge.extension,
        "source": source,
    }


def api_index_payload() -> dict:
    """Return machine-readable API discovery metadata."""

    return {
        "service": "tshirt_templates",
        "version": APP_VERSION,
        "api_version": "v1",
        "base_path": "/api/v1",
        "documentation": {
            "repository_path": "docs/APIDOCS.md",
            "note": "This Flask app does not serve repository documentation files directly.",
        },
        "endpoints": {
            "health": {"method": "GET", "path": "/api/v1/health"},
            "ready": {"method": "GET", "path": "/api/v1/ready"},
            "options": {"method": "GET", "path": "/api/v1/options"},
            "badges": {"method": "GET", "path": "/api/v1/badges"},
            "uploads": {"method": "POST", "path": "/api/v1/uploads"},
            "upload": {"methods": ["PUT", "DELETE"], "path": "/api/v1/uploads/{filename}"},
            "layout_preview": {"method": "POST", "path": "/api/v1/layouts/preview"},
            "pdf": {"method": "POST", "path": "/api/v1/pdfs"},
            "templates": {"methods": ["GET", "POST"], "path": "/api/v1/templates"},
            "template": {"methods": ["GET", "DELETE"], "path": "/api/v1/templates/{name}"},
        },
        "mcp": {
            "endpoint": "/mcp",
            "transport": MCP_TRANSPORT,
            "methods": MCP_METHODS,
            "resource_templates": [MCP_BADGES_URI_TEMPLATE],
            "port_note": MCP_PORT_NOTE,
        },
    }

def options_payload() -> dict:
    """Return supported option values and defaults for API consumers."""

    return {
        "page_sizes": PAGE_SIZES,
        "orientations": ORIENTATIONS,
        "layout_modes": LAYOUT_MODES,
        "layout_mode_details": LAYOUT_MODE_DETAILS,
        "order_modes": ORDER_MODES,
        "units": UNITS,
        "text_fonts": TEXT_FONTS,
        "badge_size_options": BADGE_SIZE_OPTIONS,
        "spacing_options": SPACING_OPTIONS,
        "logo_size_options": LOGO_SIZE_OPTIONS,
        "curve_device_options": CURVE_DEVICE_OPTIONS,
        "curve_device_diameters": CURVE_DEVICE_DIAMETERS,
        "copy_options": COPY_OPTIONS,
        "defaults": {
            "page_size": "a4",
            "orientation": "portrait",
            "mode": "grid",
            "unit": DEFAULT_UNIT,
            "badge_size": DEFAULT_BADGE_AMOUNTS[DEFAULT_UNIT],
            "spacing": DEFAULT_SPACING_AMOUNTS[DEFAULT_UNIT],
            "page_margin": DEFAULT_PAGE_MARGIN_AMOUNTS[DEFAULT_UNIT],
            "panel_gap": DEFAULT_PANEL_GAP_AMOUNTS[DEFAULT_UNIT],
            "include_logo": False,
            "logo_sides": [],
            "logo_size": DEFAULT_LOGO_AMOUNTS[DEFAULT_UNIT],
            "front_logo_size": DEFAULT_LOGO_AMOUNTS[DEFAULT_UNIT],
            "back_logo_size": DEFAULT_LOGO_AMOUNTS[DEFAULT_UNIT],
            "copies": 1,
            "order": "selected",
            "sides": ["front", "back"],
            "mirror": True,
            "include_print_marks": False,
            "include_cut_lines": False,
            "include_yellow_unifier": False,
            "include_curve_effect": False,
            "curve_device": DEFAULT_CURVE_DEVICE,
            "curve_diameter": DEFAULT_CURVE_DIAMETER_AMOUNTS[DEFAULT_UNIT],
            "front_text": "",
            "back_text": "",
            "text_font": "ubuntu",
            "text_size": DEFAULT_TEXT_SIZE,
        },
    }


def placement_to_dict(placement: Placement, unit: str) -> dict:
    """Serialize a placement in both display units and PDF points."""

    divisor = points_per_unit(unit)
    return {
        "badge_id": placement.badge_id,
        "x": placement.x / divisor,
        "y": placement.y / divisor,
        "width": placement.width / divisor,
        "height": placement.height / divisor,
        "rotation": placement.rotation,
        "unit": unit,
        "points": {
            "x": placement.x,
            "y": placement.y,
            "width": placement.width,
            "height": placement.height,
        },
    }


def layout_to_dict(layout: PanelLayout, unit: str) -> dict:
    """Serialize a panel layout in both display units and PDF points."""

    divisor = points_per_unit(unit)
    return {
        "side": layout.side,
        "x": layout.x / divisor,
        "y": layout.y / divisor,
        "width": layout.width / divisor,
        "height": layout.height / divisor,
        "unit": unit,
        "points": {
            "x": layout.x,
            "y": layout.y,
            "width": layout.width,
            "height": layout.height,
        },
        "placements": [placement_to_dict(placement, unit) for placement in layout.placements],
    }


def apply_json_manual_placements(
    layouts: list[PanelLayout],
    page_height: float,
    unit: str,
    manual_placements: list,
) -> list[PanelLayout]:
    """Apply API manual placement overrides addressed by layout/placement index."""

    if not manual_placements:
        return layouts
    overrides = {}
    for item in manual_placements:
        if not isinstance(item, dict):
            continue
        try:
            key = (int(item.get("layout_index", -1)), int(item.get("placement_index", -1)))
        except (TypeError, ValueError):
            continue
        overrides[key] = item
    divisor = points_per_unit(unit)
    adjusted_layouts: list[PanelLayout] = []
    for layout_index, layout in enumerate(layouts):
        placements = []
        for placement_index, placement in enumerate(layout.placements):
            override = overrides.get((layout_index, placement_index))
            if not override:
                placements.append(placement)
                continue
            x = _json_coordinate(override.get("x"), placement.x, divisor)
            preview_y = _json_coordinate(
                override.get("y"), page_height - placement.y - placement.height, divisor
            )
            rotation = _json_float(override.get("rotation"), placement.rotation)
            placements.append(
                Placement(
                    badge_id=placement.badge_id,
                    x=x,
                    y=page_height - preview_y - placement.height,
                    width=placement.width,
                    height=placement.height,
                    rotation=rotation,
                )
            )
        adjusted_layouts.append(
            PanelLayout(layout.side, layout.x, layout.y, layout.width, layout.height, placements)
        )
    return adjusted_layouts


def _json_coordinate(value, default: float, point_multiplier: float) -> float:
    try:
        return float(value) * point_multiplier if value not in {None, ""} else default
    except (TypeError, ValueError):
        return default


def _json_float(value, default: float) -> float:
    try:
        return float(value) if value not in {None, ""} else default
    except (TypeError, ValueError):
        return default


def json_form_values(options: dict) -> dict[str, str]:
    """Normalize JSON option values into form-like strings for existing parsing."""

    values = {}
    for key, value in options.items():
        if isinstance(value, bool):
            values[key] = "on" if value else "off"
        elif value is not None and not isinstance(value, list):
            values[key] = str(value)
    return values


def json_getlist(options: dict):
    """Return a getlist-compatible callback for JSON option arrays."""

    def getlist(key: str) -> list[str]:
        value = options.get(key, [])
        if isinstance(value, list):
            return [str(item) for item in value]
        if value in {None, ""}:
            return []
        return [str(value)]

    return getlist


def logo_requested_from_sides(value) -> bool:
    """Return whether a JSON/query logo_sides value selects any logo side."""

    if value is None or value == "":
        return False
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = [str(item) for item in value]
    else:
        values = [str(value)]
    raw_sides = [side for item in values for side in item.replace(",", " ").split()]
    return any(side in {"front", "back"} for side in raw_sides)


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.setdefault("UPLOAD_FOLDER", str(Path(app.instance_path) / "uploads"))
    app.config.setdefault("TEMPLATE_FOLDER", str(Path(app.instance_path) / "templates"))
    app.config.setdefault("MAX_CONTENT_LENGTH", 32 * 1024 * 1024)
    app.secret_key = (
        app.config.get("SECRET_KEY")
        or os.environ.get("SECRET_KEY")
        or "dev-upload-warnings"
    )

    @app.get("/")
    def index() -> str:
        badges = _available_badges()
        selected_ids = default_selected_badge_ids(badges)
        manual_selection_ids = [badge.id for badge in badges if is_manual_selection_badge(badge)]
        return render_template(
            "index.html",
            badges=badges,
            badge_categories=sorted({badge_category(badge) for badge in badges}),
            selected_ids=selected_ids,
            manual_selection_ids=manual_selection_ids,
            modes=LAYOUT_MODES,
            page_sizes=PAGE_SIZES,
            orientations=ORIENTATIONS,
            order_modes=ORDER_MODES,
            units=UNITS,
            default_unit=DEFAULT_UNIT,
            default_badge_amounts=DEFAULT_BADGE_AMOUNTS,
            default_spacing_amounts=DEFAULT_SPACING_AMOUNTS,
            default_page_margin_amounts=DEFAULT_PAGE_MARGIN_AMOUNTS,
            default_panel_gap_amounts=DEFAULT_PANEL_GAP_AMOUNTS,
            default_logo_amounts=DEFAULT_LOGO_AMOUNTS,
            default_curve_diameter_amounts=DEFAULT_CURVE_DIAMETER_AMOUNTS,
            curve_device_options=CURVE_DEVICE_OPTIONS,
            curve_device_diameters=CURVE_DEVICE_DIAMETERS,
            badge_size_options=BADGE_SIZE_OPTIONS,
            spacing_options=SPACING_OPTIONS,
            logo_size_options=LOGO_SIZE_OPTIONS,
            copy_options=COPY_OPTIONS,
            text_fonts=TEXT_FONTS,
            default_text_size=DEFAULT_TEXT_SIZE,
            upload_messages=get_flashed_messages(),
            saved_templates=_list_saved_templates(),
        )

    @app.post("/refresh")
    def refresh() -> Response:
        refresh_badges()
        _log_event(app, logging.INFO, "badge_refresh", source="browser")
        return redirect(url_for("index"))

    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename: str) -> Response:
        return send_from_directory(_upload_folder(), filename)

    @app.post("/uploads/delete")
    def delete_upload() -> Response:
        filename = request.form.get("delete_upload", "")
        deleted = delete_uploaded_badge(filename, _upload_folder())
        _log_event(
            app,
            logging.INFO if deleted else logging.WARNING,
            "upload_deleted" if deleted else "upload_delete_missing",
            route="/uploads/delete",
            filename=filename,
        )
        return redirect(url_for("index"))

    @app.post("/uploads/replace")
    def replace_upload() -> Response:
        filename = request.form.get("replace_upload", "")
        upload = _first_uploaded_file("replacement_upload")
        if not upload:
            _log_event(
                app,
                logging.WARNING,
                "upload_rejected",
                route="/uploads/replace",
                reason="missing_file",
            )
            flash("Choose a replacement image before using Replace upload.")
        else:
            badge, warnings = replace_uploaded_badge_bytes_with_warnings(
                filename, upload.read(), _upload_folder()
            )
            if not badge:
                _log_event(
                    app,
                    logging.WARNING,
                    "upload_rejected",
                    route="/uploads/replace",
                    reason="invalid_replacement",
                )
                flash("Replacement upload must be a valid SVG, PNG, JPG, or JPEG image within the size limit.")
            else:
                _log_event(
                    app,
                    logging.INFO,
                    "upload_replaced",
                    route="/uploads/replace",
                    filename=filename,
                    warning_count=len(warnings),
                )
            for warning in warnings:
                flash(warning.message)
        return redirect(url_for("index"))

    @app.get("/api/v1")
    def api_index() -> Response:
        return jsonify(api_index_payload())

    @app.get("/api/v1/health")
    def api_health() -> Response:
        return jsonify({"status": "ok", "service": "tshirt_templates"})

    @app.get("/api/v1/ready")
    def api_ready() -> Response:
        upload_folder = Path(_upload_folder())
        checks = {"upload_folder": "ok"}
        status_code = 200
        status = "ready"
        try:
            upload_folder.mkdir(parents=True, exist_ok=True)
            if not upload_folder.is_dir():
                raise OSError("Configured upload folder is not a directory.")
        except OSError as error:
            checks["upload_folder"] = "error"
            status_code = 503
            status = "not_ready"
            app.logger.warning("Readiness check failed for upload folder: %s", error)
        return jsonify({"status": status, "service": "tshirt_templates", "checks": checks}), status_code

    @app.get("/api/v1/options")
    def api_options() -> Response:
        return jsonify(options_payload())

    @app.get("/api/v1/badges")
    def api_badges() -> Response:
        if request.args.get("refresh") in {"1", "true", "yes"}:
            refresh_badges()
            _log_event(app, logging.INFO, "badge_refresh", source="api")
        order = request.args.get("order", "alphabetical")
        badges = order_badges(_available_badges(), order)
        include_logo = request.args.get("include_logo") in {"1", "true", "yes"} or logo_requested_from_sides(
            request.args.getlist("logo_sides")
        )
        if include_logo:
            badges = [*badges, LOGO_BADGE]
        return jsonify({"badges": [badge_to_dict(badge) for badge in badges]})

    @app.post("/api/v1/uploads")
    def api_uploads() -> Response:
        upload_result = save_uploaded_badges_with_warnings(request.files.getlist("uploads"), _upload_folder())
        if not upload_result.badges:
            _log_event(
                app,
                logging.WARNING,
                "upload_rejected",
                route="/api/v1/uploads",
                warning_count=len(upload_result.warnings),
            )
            return _api_error(
                "invalid_upload",
                "Upload at least one SVG, PNG, JPG, or JPEG image under the uploads field.",
                400,
                field="uploads",
            )
        _log_event(
            app,
            logging.INFO,
            "upload_saved",
            route="/api/v1/uploads",
            badge_count=len(upload_result.badges),
            warning_count=len(upload_result.warnings),
        )
        return (
            jsonify(
                {
                    "badges": [badge_to_dict(badge) for badge in upload_result.badges],
                    "warnings": upload_warnings_to_dicts(upload_result.warnings),
                }
            ),
            201,
        )

    @app.delete("/api/v1/uploads/<path:filename>")
    def api_delete_upload(filename: str) -> Response:
        if not delete_uploaded_badge(filename, _upload_folder()):
            _log_event(
                app,
                logging.WARNING,
                "upload_delete_missing",
                route="/api/v1/uploads/{filename}",
                filename=filename,
            )
            return _api_error(
                "upload_not_found",
                "No uploaded badge exists for that filename.",
                404,
                field="filename",
            )
        _log_event(
            app,
            logging.INFO,
            "upload_deleted",
            route="/api/v1/uploads/{filename}",
            filename=filename,
        )
        return jsonify({"deleted": filename})

    @app.put("/api/v1/uploads/<path:filename>")
    def api_replace_upload(filename: str) -> Response:
        upload = _first_uploaded_file("upload") or _first_uploaded_file("replacement_upload")
        if not upload:
            _log_event(
                app,
                logging.WARNING,
                "upload_rejected",
                route="/api/v1/uploads/{filename}",
                reason="missing_file",
            )
            return _api_error(
                "invalid_upload",
                "Upload one replacement SVG, PNG, JPG, or JPEG image under the upload field.",
                400,
                field="upload",
            )
        badge, warnings = replace_uploaded_badge_bytes_with_warnings(
            filename, upload.read(), _upload_folder()
        )
        if not badge:
            _log_event(
                app,
                logging.WARNING,
                "upload_rejected",
                route="/api/v1/uploads/{filename}",
                reason="invalid_replacement",
            )
            return _api_error(
                "upload_not_found",
                "No uploaded badge exists for that filename, or the replacement is invalid, empty, or too large.",
                404,
                field="filename",
            )
        _log_event(
            app,
            logging.INFO,
            "upload_replaced",
            route="/api/v1/uploads/{filename}",
            filename=filename,
            warning_count=len(warnings),
        )
        return jsonify({"badge": badge_to_dict(badge), "warnings": upload_warnings_to_dicts(warnings)})

    @app.post("/api/v1/layouts/preview")
    def api_layout_preview() -> Response:
        payload = request.get_json(silent=True) or {}
        result = _layout_from_json(payload)
        return jsonify(result)

    @app.post("/api/v1/pdfs")
    def api_pdf() -> Response:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return _api_error(
                "invalid_json",
                "Submit a JSON object with badge_ids, options, and optional manual_placements.",
                400,
            )
        options, render_badges, page_size, layouts = _json_layout_parts(
            payload, separate_side_pages=True
        )
        asset_failures = _pdf_asset_failures(render_badges)
        allow_partial = bool(payload.get("allow_partial"))
        if asset_failures and not allow_partial:
            _log_event(
                app,
                logging.WARNING,
                "pdf_generation_failed",
                route="/api/v1/pdfs",
                reason="asset_verification_failed",
                failure_count=len(asset_failures),
            )
            return _api_error(
                "asset_verification_failed",
                "One or more badge assets could not be fetched or rendered.",
                422,
                failures=asset_failures,
            )
        from .pdf import render_pdf

        metadata = _pdf_metadata(options)
        if asset_failures:
            _log_event(
                app,
                logging.WARNING,
                "pdf_generation_partial",
                route="/api/v1/pdfs",
                reason="asset_verification_failed",
                failure_count=len(asset_failures),
            )
            metadata["asset_failures"] = str(len(asset_failures))
            metadata["allow_partial"] = "true"

        content = render_pdf(
            render_badges,
            page_size,
            layouts,
            mirror=options.mirror,
            panel_text=_panel_text_options(options, page_size[1]),
            print_marks=options.include_print_marks,
            cut_lines=options.include_cut_lines,
            yellow_unifier=options.include_yellow_unifier,
            curve_settings=_curve_settings(options),
            metadata=metadata,
            one_layout_per_page=True,
        )
        headers = {"Content-Disposition": "attachment; filename=tshirt-badge-template.pdf"}
        if asset_failures:
            headers["X-Badgeware-Warnings"] = json.dumps({"asset_failures": asset_failures})
        return Response(
            content,
            mimetype="application/pdf",
            headers=headers,
        )


    @app.get("/api/v1/templates")
    def api_list_templates() -> Response:
        return jsonify({"templates": _list_saved_templates()})

    @app.post("/api/v1/templates")
    def api_save_template() -> tuple[Response, int] | Response:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return _api_error(
                "invalid_json",
                "Submit a JSON object with name and template fields.",
                400,
            )
        result, error = _save_template_payload(payload)
        if error:
            return _api_error(error["code"], error["message"], 400, field=error.get("field"))
        return jsonify(result), 201

    @app.get("/api/v1/templates/<path:name>")
    def api_get_template(name: str) -> Response | tuple[Response, int]:
        template = _read_saved_template(name)
        if template is None:
            return _api_error(
                "template_not_found",
                "No saved template exists for that name.",
                404,
                field="name",
            )
        return jsonify(template)

    @app.delete("/api/v1/templates/<path:name>")
    def api_delete_template(name: str) -> Response | tuple[Response, int]:
        deleted = _delete_saved_template(name)
        if deleted is None:
            return _api_error(
                "template_not_found",
                "No saved template exists for that name.",
                404,
                field="name",
            )
        return jsonify({"deleted": deleted})

    @app.get("/mcp")
    def mcp_metadata() -> Response:
        return jsonify(_mcp_metadata())

    @app.post("/mcp")
    def mcp_json_rpc() -> Response:
        message = request.get_json(silent=True)
        response = _handle_mcp_payload(message)
        return jsonify(response)

    @app.post("/preview")
    def preview() -> str:
        badge_ids, badges, upload_warnings = _selected_badges_with_uploads()
        page_size, layouts = _layout_from_form(badge_ids, separate_side_pages=True)
        layouts = _append_logo_placements(layouts)
        layouts = _apply_manual_placements(layouts, page_size)
        return render_template(
            "preview.html",
            badges=badges,
            badge_lookup={badge.id: badge for badge in badges},
            layouts=layouts,
            page_width=page_size[0],
            page_height=page_size[1],
            form=request.form,
            selected_ids=badge_ids,
            unit=_layout_options().unit,
            points_per_unit=_points_per_unit(_layout_options().unit),
            text_size=_layout_options().text_size,
            upload_warnings=upload_warnings_to_dicts(upload_warnings),
        )


    @app.get("/calibration.pdf")
    def calibration_pdf() -> Response:
        from .pdf import render_calibration_pdf

        raw_options = {
            "page_size": request.args.get("page_size", "a4"),
            "orientation": request.args.get("orientation", "portrait"),
            "unit": request.args.get("unit", DEFAULT_UNIT),
            "mirror": request.args.get("mirror", "off"),
        }
        options = parse_layout_options(raw_options, lambda key: [])
        content = render_calibration_pdf(
            page_size_points(options.page_size, options.orientation),
            unit=options.unit,
            mirror=options.mirror,
        )
        return Response(
            content,
            mimetype="application/pdf",
            headers={"Content-Disposition": "attachment; filename=tshirt-calibration-page.pdf"},
        )

    @app.post("/pdf")
    def pdf() -> Response:
        badge_ids, badges, _upload_warnings = _selected_badges_with_uploads()
        page_size, layouts = _layout_from_form(badge_ids, separate_side_pages=True)
        layouts = _append_logo_placements(layouts)
        layouts = _apply_manual_placements(layouts, page_size)
        asset_failures = _pdf_asset_failures(badges)
        from .pdf import render_pdf

        options = _layout_options()
        metadata = _pdf_metadata(options)
        if asset_failures:
            _log_event(
                app,
                logging.WARNING,
                "pdf_generation_partial",
                route="/pdf",
                reason="asset_verification_failed",
                failure_count=len(asset_failures),
            )
            metadata["asset_failures"] = str(len(asset_failures))
            metadata["allow_partial"] = "true"
        content = render_pdf(
            badges,
            page_size,
            layouts,
            mirror=options.mirror,
            panel_text=_panel_text_options(options, page_size[1]),
            print_marks=options.include_print_marks,
            cut_lines=options.include_cut_lines,
            yellow_unifier=options.include_yellow_unifier,
            curve_settings=_curve_settings(options),
            metadata=metadata,
            one_layout_per_page=True,
        )
        headers = {"Content-Disposition": "attachment; filename=tshirt-badge-template.pdf"}
        if asset_failures:
            headers["X-Badgeware-Warnings"] = json.dumps({"asset_failures": asset_failures})
        return Response(
            content,
            mimetype="application/pdf",
            headers=headers,
        )

    def _upload_folder() -> str:
        return app.config["UPLOAD_FOLDER"]

    def _available_badges():
        return [*list_badges(), *list_uploaded_badges(_upload_folder())]

    def _selected_badges_with_uploads() -> tuple[dict[str, list[str]], list, list]:
        upload_result = save_uploaded_badges_with_warnings(
            request.files.getlist("uploads"), _upload_folder()
        )
        if upload_result.badges or upload_result.warnings:
            _log_event(
                app,
                logging.INFO if upload_result.badges else logging.WARNING,
                "upload_saved" if upload_result.badges else "upload_rejected",
                route=request.path,
                badge_count=len(upload_result.badges),
                warning_count=len(upload_result.warnings),
            )
        uploaded_ids = [badge.id for badge in upload_result.badges]
        side_badge_ids = _side_badge_ids(uploaded_ids)
        all_badge_ids = _unique_badge_ids(
            badge_id for ids in side_badge_ids.values() for badge_id in ids
        )
        badge_lookup = {
            badge.id: badge for badge in get_badges_by_id(all_badge_ids, _upload_folder())
        }
        options = _layout_options()
        ordered_side_badge_ids: dict[str, list[str]] = {}
        for side, ids in side_badge_ids.items():
            ordered_side_badge_ids[side] = [
                badge.id
                for badge in order_badges(
                    [badge_lookup[badge_id] for badge_id in ids if badge_id in badge_lookup],
                    options.order,
                )
            ]
        ordered_render_ids = _unique_badge_ids(
            badge_id for ids in ordered_side_badge_ids.values() for badge_id in ids
        )
        render_badges = [
            badge_lookup[badge_id]
            for badge_id in ordered_render_ids
            if badge_id in badge_lookup
        ]
        if options.include_logo:
            render_badges = [*render_badges, LOGO_BADGE]
        return ordered_side_badge_ids, render_badges, upload_result.warnings

    def _side_badge_ids(uploaded_ids: list[str]) -> dict[str, list[str]]:
        front_ids = request.form.getlist("front_badges")
        back_ids = request.form.getlist("back_badges")
        legacy_ids = request.form.getlist("badges")
        if not front_ids and not back_ids and legacy_ids:
            front_ids = legacy_ids
            back_ids = legacy_ids
        front_ids = [*front_ids, *uploaded_ids]
        back_ids = [*back_ids, *uploaded_ids]
        return {
            "front": _unique_badge_ids(front_ids),
            "back": _unique_badge_ids(back_ids),
        }

    def _unique_badge_ids(ids) -> list[str]:
        seen = set()
        unique_ids = []
        for badge_id in ids:
            if badge_id and badge_id not in seen:
                seen.add(badge_id)
                unique_ids.append(badge_id)
        return unique_ids

    def _layout_options():
        return parse_layout_options(request.form, request.form.getlist)

    def _panel_text_options(options, page_height: float | None = None) -> dict[str, str | dict]:
        panel_text: dict[str, str | dict] = {
            "front": options.front_text,
            "back": options.back_text,
            "font": options.text_font,
            "size": options.text_size,
        }
        positions = _manual_panel_text_positions(page_height)
        if positions:
            panel_text["positions"] = positions
        return panel_text

    def _manual_panel_text_positions(page_height: float | None) -> dict[str, dict[str, float]]:
        if page_height is None:
            return {}
        points_per_unit = _points_per_unit(_layout_options().unit)
        positions: dict[str, dict[str, float]] = {}
        for side in ("front", "back"):
            manual_x = request.form.get(f"{side}_text_x")
            manual_y = request.form.get(f"{side}_text_y")
            if manual_x is None or manual_y is None:
                continue
            x = _manual_coordinate_points(manual_x, 0.0, points_per_unit)
            preview_y = _manual_coordinate_points(manual_y, 0.0, points_per_unit)
            positions[side] = {"x": x, "y": page_height - preview_y}
        return positions

    def _curve_settings(options) -> dict[str, float] | None:
        if not options.include_curve_effect:
            return None
        return {
            "device": options.curve_device,
            "diameter_inches": options.curve_diameter_inches,
        }

    def _pdf_metadata(options) -> dict[str, str]:
        return {
            "page_size": options.page_size,
            "orientation": options.orientation,
            "mode": options.mode,
            "unit": options.unit,
            "badge_size": options.badge_size,
            "spacing": options.spacing,
            "page_margin": options.page_margin,
            "panel_gap": options.panel_gap,
            "copies": str(options.copies),
            "order": options.order,
            "sides": ",".join(options.sides),
            "mirror": str(options.mirror).lower(),
            "include_logo": str(options.include_logo).lower(),
            "logo_sides": ",".join(options.logo_sides or []),
            "logo_size": options.logo_size,
            "front_logo_size": options.front_logo_size,
            "back_logo_size": options.back_logo_size,
            "include_print_marks": str(options.include_print_marks).lower(),
            "include_cut_lines": str(options.include_cut_lines).lower(),
            "include_yellow_unifier": str(options.include_yellow_unifier).lower(),
            "include_curve_effect": str(options.include_curve_effect).lower(),
            "curve_device": options.curve_device,
            "curve_diameter": options.curve_diameter,
            "text_font": options.text_font,
            "text_size": options.text_size,
        }

    def _layout_from_form(
        badge_ids: dict[str, list[str]], separate_side_pages: bool = False
    ):
        options = _layout_options()
        return place_badges(
            badge_ids=badge_ids,
            sides=options.sides,
            page_size=options.page_size,
            orientation=options.orientation,
            mode=options.mode,
            badge_size_inches=options.badge_size_inches,
            spacing_inches=options.spacing_inches,
            page_margin_inches=options.page_margin_inches,
            panel_gap_inches=options.panel_gap_inches,
            copies=options.copies,
            separate_side_pages=separate_side_pages,
        )

    def _append_logo_placements(layouts: list[PanelLayout]) -> list[PanelLayout]:
        options = _layout_options()
        if not options.include_logo:
            return layouts
        return append_logo_placements(
            layouts,
            {
                "front": options.front_logo_size_inches,
                "back": options.back_logo_size_inches,
                "default": options.logo_size_inches,
            },
            options.logo_sides,
        )

    def _apply_manual_placements(
        layouts: list[PanelLayout], page_size: tuple[float, float]
    ) -> list[PanelLayout]:
        page_height = page_size[1]
        adjusted_layouts: list[PanelLayout] = []
        for layout_index, layout in enumerate(layouts):
            placements: list[Placement] = []
            for placement_index, placement in enumerate(layout.placements):
                prefix = f"manual_{layout_index}_{placement_index}"
                manual_x = request.form.get(f"{prefix}_x")
                manual_y = request.form.get(f"{prefix}_y")
                manual_rotation = request.form.get(f"{prefix}_rotation")
                if manual_x is None and manual_y is None and manual_rotation is None:
                    placements.append(placement)
                    continue
                points_per_unit = _points_per_unit(_layout_options().unit)
                x = _manual_coordinate_points(manual_x, placement.x, points_per_unit)
                preview_y = _manual_coordinate_points(
                    manual_y, page_height - placement.y - placement.height, points_per_unit
                )
                y = page_height - preview_y - placement.height
                rotation = _manual_float(manual_rotation, placement.rotation)
                placements.append(
                    Placement(
                        badge_id=placement.badge_id,
                        x=x,
                        y=y,
                        width=placement.width,
                        height=placement.height,
                        rotation=rotation,
                    )
                )
            adjusted_layouts.append(
                PanelLayout(
                    layout.side, layout.x, layout.y, layout.width, layout.height, placements
                )
            )
        return adjusted_layouts

    def _manual_coordinate_points(
        value: str | None, default: float, points_per_unit: float
    ) -> float:
        try:
            return float(value) * points_per_unit if value not in {None, ""} else default
        except (TypeError, ValueError):
            return default

    def _manual_float(value: str | None, default: float) -> float:
        try:
            return float(value) if value not in {None, ""} else default
        except (TypeError, ValueError):
            return default

    def _points_per_unit(unit: str) -> float:
        return points_per_unit(unit)

    def _first_uploaded_file(field_name: str):
        for upload in request.files.getlist(field_name):
            if getattr(upload, "filename", ""):
                return upload
        return None

    def _api_error(
        code: str,
        message: str,
        status: int,
        field: str | None = None,
        allowed_values: list[str] | None = None,
        failures: list[dict[str, str]] | None = None,
    ) -> tuple[Response, int]:
        error: dict[str, str | list[str] | list[dict[str, str]]] = {"code": code, "message": message}
        if field:
            error["field"] = field
        if allowed_values:
            error["allowed_values"] = allowed_values
        if failures:
            error["failures"] = failures
        return jsonify({"error": error}), status

    def _pdf_asset_failures(badges: list[Badge]) -> list[dict[str, str]]:
        pdf_module = importlib.import_module("tshirt_templates.pdf")
        verifier = getattr(pdf_module, "verify_pdf_assets", lambda badge_list: [])
        return verifier(badges)

    def _pdf_asset_failure_response(failures: list[dict[str, str]]) -> tuple[Response, int]:
        return _api_error(
            "asset_verification_failed",
            "One or more badge assets could not be fetched or rendered.",
            422,
            failures=failures,
        )

    def _template_folder() -> Path:
        return Path(app.config["TEMPLATE_FOLDER"])

    def _template_name(value) -> str | None:
        name = str(value or "").strip()
        if name.endswith(".json"):
            name = name[:-5]
        if not name or len(name) > 80:
            return None
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
        if any(character not in allowed for character in name):
            return None
        if name in {".", ".."} or ".." in name.split("."):
            return None
        return name

    def _template_path(name: str) -> Path | None:
        safe_name = _template_name(name)
        if safe_name is None:
            return None
        return _template_folder() / f"{safe_name}.json"

    def _template_summary(path: Path) -> dict | None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        template = payload.get("template", {})
        if not isinstance(template, dict):
            template = {}
        badge_ids = template.get("badge_ids", []) if isinstance(template.get("badge_ids"), list) else []
        side_badge_ids = template.get("side_badge_ids", {}) if isinstance(template.get("side_badge_ids"), dict) else {}
        side_ids = [
            badge_id
            for side in ("front", "back")
            for badge_id in side_badge_ids.get(side, [])
            if isinstance(side_badge_ids.get(side, []), list)
        ]
        return {
            "name": payload.get("name", path.stem),
            "created_at": payload.get("created_at"),
            "updated_at": payload.get("updated_at"),
            "badge_count": len(_unique_badge_ids([*badge_ids, *side_ids])),
            "options": template.get("options", {}) if isinstance(template.get("options"), dict) else {},
        }

    def _list_saved_templates() -> list[dict]:
        folder = _template_folder()
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError:
            return []
        summaries = []
        for path in sorted(folder.glob("*.json")):
            summary = _template_summary(path)
            if summary is not None:
                summaries.append(summary)
        return summaries

    def _read_saved_template(name: str) -> dict | None:
        path = _template_path(name)
        if path is None or not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    def _normalize_template_payload(template) -> dict | None:
        if not isinstance(template, dict):
            return None
        badge_ids = template.get("badge_ids", [])
        options = template.get("options", {})
        manual_placements = template.get("manual_placements", [])
        side_badge_ids = template.get("side_badge_ids", {})
        if not isinstance(badge_ids, list) or not isinstance(options, dict):
            return None
        if not isinstance(manual_placements, list):
            manual_placements = []
        normalized = {
            "badge_ids": [str(badge_id) for badge_id in badge_ids],
            "options": options,
            "manual_placements": [item for item in manual_placements if isinstance(item, dict)],
        }
        if isinstance(side_badge_ids, dict) and "side_badge_ids" in template:
            normalized["side_badge_ids"] = {
                side: [str(badge_id) for badge_id in side_badge_ids.get(side, [])]
                for side in ("front", "back")
                if isinstance(side_badge_ids.get(side, []), list)
            }
        return normalized

    def _save_template_payload(payload: dict) -> tuple[dict | None, dict | None]:
        safe_name = _template_name(payload.get("name"))
        if safe_name is None:
            return None, {
                "code": "invalid_template_name",
                "message": "Template name must be 1-80 characters using letters, numbers, dots, dashes, or underscores.",
                "field": "name",
            }
        template = _normalize_template_payload(payload.get("template"))
        if template is None:
            return None, {
                "code": "invalid_template",
                "message": "Template must include badge_ids as an array and options as an object.",
                "field": "template",
            }
        folder = _template_folder()
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError:
            return None, {
                "code": "template_storage_unavailable",
                "message": "Template storage folder cannot be created.",
                "field": "name",
            }
        path = folder / f"{safe_name}.json"
        now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        existing = _read_saved_template(safe_name) or {}
        saved = {
            "name": safe_name,
            "created_at": existing.get("created_at", now),
            "updated_at": now,
            "template": template,
        }
        try:
            path.write_text(json.dumps(saved, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except OSError:
            return None, {
                "code": "template_storage_unavailable",
                "message": "Template file cannot be written.",
                "field": "name",
            }
        return saved, None

    def _delete_saved_template(name: str) -> str | None:
        path = _template_path(name)
        if path is None or not path.exists():
            return None
        try:
            path.unlink()
        except OSError:
            return None
        return path.stem

    def _json_layout_parts(payload: dict, separate_side_pages: bool = False):
        raw_options = payload.get("options", {})
        if not isinstance(raw_options, dict):
            raw_options = {}
        options = parse_layout_options(json_form_values(raw_options), json_getlist(raw_options))
        raw_badge_ids = payload.get("badge_ids", [])
        if not isinstance(raw_badge_ids, list):
            raw_badge_ids = []
        badge_ids = [str(badge_id) for badge_id in raw_badge_ids]
        badges = get_badges_by_id(badge_ids, _upload_folder())
        ordered_badges = order_badges(badges, options.order)
        ordered_ids = [badge.id for badge in ordered_badges]
        render_badges = [*ordered_badges, LOGO_BADGE] if options.include_logo else ordered_badges
        page_size, layouts = place_badges(
            badge_ids=ordered_ids,
            sides=options.sides,
            page_size=options.page_size,
            orientation=options.orientation,
            mode=options.mode,
            badge_size_inches=options.badge_size_inches,
            spacing_inches=options.spacing_inches,
            page_margin_inches=options.page_margin_inches,
            panel_gap_inches=options.panel_gap_inches,
            copies=options.copies,
            separate_side_pages=separate_side_pages,
        )
        if options.include_logo:
            layouts = append_logo_placements(
                layouts,
                {
                    "front": options.front_logo_size_inches,
                    "back": options.back_logo_size_inches,
                    "default": options.logo_size_inches,
                },
                options.logo_sides,
            )
        manual_placements = payload.get("manual_placements", [])
        if not isinstance(manual_placements, list):
            manual_placements = []
        layouts = apply_json_manual_placements(
            layouts, page_size[1], options.unit, manual_placements
        )
        return options, render_badges, page_size, layouts

    def _layout_from_json(payload: dict) -> dict:
        options, render_badges, page_size, layouts = _json_layout_parts(
            payload, separate_side_pages=True
        )
        divisor = points_per_unit(options.unit)
        return {
            "page": {
                "width": page_size[0] / divisor,
                "height": page_size[1] / divisor,
                "unit": options.unit,
                "points": {"width": page_size[0], "height": page_size[1]},
            },
            "badges": [badge_to_dict(badge) for badge in render_badges],
            "layouts": [layout_to_dict(layout, options.unit) for layout in layouts],
            "options": {
                "page_size": options.page_size,
                "orientation": options.orientation,
                "mode": options.mode,
                "unit": options.unit,
                "badge_size": options.badge_size,
                "spacing": options.spacing,
                "page_margin": options.page_margin,
                "panel_gap": options.panel_gap,
                "include_logo": options.include_logo,
                "logo_sides": options.logo_sides,
                "logo_size": options.logo_size,
                "front_logo_size": options.front_logo_size,
                "back_logo_size": options.back_logo_size,
                "copies": options.copies,
                "order": options.order,
                "sides": options.sides,
                "mirror": options.mirror,
                "include_print_marks": options.include_print_marks,
                "include_cut_lines": options.include_cut_lines,
                "include_yellow_unifier": options.include_yellow_unifier,
                "include_curve_effect": options.include_curve_effect,
                "curve_device": options.curve_device,
                "curve_diameter": options.curve_diameter,
                "front_text": options.front_text,
                "back_text": options.back_text,
                "text_font": options.text_font,
                "text_size": options.text_size,
            },
        }

    def _mcp_metadata() -> dict:
        return {
            "name": "tshirt_templates",
            "version": APP_VERSION,
            "protocol": "mcp-json-rpc",
            "endpoint": "/mcp",
            "transport": MCP_TRANSPORT,
            "capabilities": {"tools": True, "resources": True, "prompts": True},
            "tools": [
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
            ],
            "resources": ["tshirt://options", "tshirt://badges", "tshirt://templates"],
            "resource_templates": [MCP_BADGES_URI_TEMPLATE],
            "port_note": MCP_PORT_NOTE,
        }

    def _mcp_tools() -> list[dict]:
        layout_options_schema = {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": list(LAYOUT_MODES.keys()),
                    "description": (
                        "Placement mode. Use m-pixels-no-shrink to preserve badge size "
                        "and place overflow around the M."
                    ),
                }
            },
        }
        return [
            {
                "name": "get_options",
                "description": "Return supported template options and defaults.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "list_badges",
                "description": "Return available badge artwork.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "refresh": {"type": "boolean"},
                        "order": {"type": "string"},
                        "logo_sides": {
                            "description": (
                                "Preferred: include the MakeSpace logo when one or more "
                                "panel sides are selected."
                            ),
                            "oneOf": [
                                {
                                    "type": "array",
                                    "items": {"type": "string", "enum": ["front", "back"]},
                                },
                                {"type": "string"},
                            ],
                        },
                        "include_logo": {
                            "type": "boolean",
                            "description": "Legacy compatibility flag; prefer logo_sides.",
                        },
                    },
                },
            },
            {
                "name": "compute_layout",
                "description": "Compute a template layout from badge IDs and options.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "badge_ids": {"type": "array", "items": {"type": "string"}},
                        "options": layout_options_schema,
                    },
                },
            },
            {
                "name": "render_pdf",
                "description": "Render a PDF from badge IDs, options, and optional manual placements.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "badge_ids": {"type": "array", "items": {"type": "string"}},
                        "options": layout_options_schema,
                        "manual_placements": {"type": "array", "items": {"type": "object"}},
                        "allow_partial": {"type": "boolean"},
                    },
                },
            },
            {
                "name": "upload_badge_artwork",
                "description": "Save one base64-encoded badge artwork file and return its badge record.",
                "inputSchema": {
                    "type": "object",
                    "required": ["filename", "content_base64"],
                    "properties": {
                        "filename": {"type": "string"},
                        "content_base64": {"type": "string"},
                    },
                },
            },
            {
                "name": "validate_template",
                "description": "Return normalized options and warnings for a template request.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "badge_ids": {"type": "array", "items": {"type": "string"}},
                        "options": layout_options_schema,
                        "manual_placements": {"type": "array", "items": {"type": "object"}},
                    },
                },
            },
            {
                "name": "list_saved_templates",
                "description": "List saved JSON template files for repeatable local workflows.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "save_template",
                "description": "Save a named JSON template request with badge IDs, options, and optional manual placements.",
                "inputSchema": {
                    "type": "object",
                    "required": ["name", "template"],
                    "properties": {
                        "name": {"type": "string"},
                        "template": {"type": "object"},
                    },
                },
            },
            {
                "name": "get_saved_template",
                "description": "Read a saved JSON template file by name.",
                "inputSchema": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {"name": {"type": "string"}},
                },
            },
            {
                "name": "delete_saved_template",
                "description": "Delete a saved JSON template file by name.",
                "inputSchema": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {"name": {"type": "string"}},
                },
            },
        ]

    def _mcp_result(message_id, payload: dict) -> dict:
        return {"jsonrpc": "2.0", "id": message_id, "result": payload}

    def _mcp_error(message_id, code: int, message: str, data: dict | None = None) -> dict:
        error = {"code": code, "message": message}
        if data:
            error["data"] = data
        return {"jsonrpc": "2.0", "id": message_id, "error": error}

    def _mcp_tool_result(structured_content: dict, text: str | None = None) -> dict:
        result = {"structuredContent": structured_content}
        if text:
            result["content"] = [{"type": "text", "text": text}]
        return result

    def _mcp_json_resource(uri: str, payload: dict) -> dict:
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(payload, sort_keys=True),
                }
            ]
        }

    def _mcp_render_pdf(arguments: dict) -> dict:
        options, render_badges, page_size, layouts = _json_layout_parts(
            arguments, separate_side_pages=True
        )
        requested_ids = [str(badge_id) for badge_id in arguments.get("badge_ids", []) if str(badge_id)]
        render_badge_ids = [badge.id for badge in render_badges]
        resolved_ids = set(render_badge_ids)
        missing_ids = [badge_id for badge_id in requested_ids if badge_id not in resolved_ids]
        placement_count = sum(len(layout.placements) for layout in layouts)
        warnings = []
        if missing_ids:
            warnings.append(
                {
                    "code": "unknown_badges",
                    "message": "Some requested badge IDs were not found and would be omitted from the PDF.",
                    "badge_ids": missing_ids,
                }
            )
        if placement_count == 0:
            warnings.append(
                {
                    "code": "empty_layout",
                    "message": "The render request produced no badge placements.",
                }
            )
        allow_partial = bool(arguments.get("allow_partial"))
        if warnings and not allow_partial:
            _log_event(
                app,
                logging.WARNING,
                "pdf_generation_failed",
                route="/mcp",
                reason="render_preflight_failed",
                failure_count=len(warnings),
            )
            return {
                "error": {
                    "code": "render_preflight_failed",
                    "message": "MCP PDF render preflight failed; fix the warnings or set allow_partial=true to render anyway.",
                    "failures": warnings,
                }
            }
        asset_failures = _pdf_asset_failures(render_badges)
        if asset_failures:
            warnings.append(
                {
                    "code": "asset_verification_failed",
                    "message": "One or more badge assets could not be fetched or rendered; placeholders will be drawn for failed assets.",
                    "failures": asset_failures,
                }
            )
        if asset_failures and not allow_partial:
            _log_event(
                app,
                logging.WARNING,
                "pdf_generation_failed",
                route="/mcp",
                reason="asset_verification_failed",
                failure_count=len(asset_failures),
            )
            return {
                "error": {
                    "code": "asset_verification_failed",
                    "message": "One or more badge assets could not be fetched or rendered.",
                    "failures": asset_failures,
                }
            }
        from .pdf import render_pdf

        metadata = _pdf_metadata(options)
        if asset_failures:
            _log_event(
                app,
                logging.WARNING,
                "pdf_generation_partial",
                route="/mcp",
                reason="asset_verification_failed",
                failure_count=len(asset_failures),
            )
            metadata["asset_failures"] = str(len(asset_failures))
            metadata["allow_partial"] = "true"

        content = render_pdf(
            render_badges,
            page_size,
            layouts,
            mirror=options.mirror,
            panel_text=_panel_text_options(options, page_size[1]),
            print_marks=options.include_print_marks,
            cut_lines=options.include_cut_lines,
            yellow_unifier=options.include_yellow_unifier,
            curve_settings=_curve_settings(options),
            metadata=metadata,
            one_layout_per_page=True,
        )
        encoded = base64.b64encode(content).decode("ascii")
        return {
            "mime_type": "application/pdf",
            "filename": "tshirt-badge-template.pdf",
            "pdf_base64": encoded,
            "byte_length": len(content),
            "warnings": warnings,
            "diagnostics": {
                "requested_badge_ids": requested_ids,
                "render_badge_ids": render_badge_ids,
                "missing_badge_ids": missing_ids,
                "layout_count": len(layouts),
                "placement_count": placement_count,
                "allow_partial": allow_partial,
            },
            "resource": {
                "uri": "tshirt://generated/tshirt-badge-template.pdf",
                "mimeType": "application/pdf",
                "blob": encoded,
            },
        }

    def _mcp_upload_badge(arguments: dict) -> dict:
        filename = str(arguments.get("filename", ""))
        encoded_content = arguments.get("content_base64", "")
        if not isinstance(encoded_content, str):
            return {"error": {"code": "invalid_upload", "message": "content_base64 must be a string."}}
        try:
            content = base64.b64decode(encoded_content, validate=True)
        except (binascii.Error, ValueError):
            return {"error": {"code": "invalid_upload", "message": "content_base64 is not valid base64."}}
        badge, warnings = save_uploaded_badge_bytes_with_warnings(filename, content, _upload_folder())
        if not badge:
            return {
                "error": {
                    "code": "invalid_upload",
                    "message": "Upload one valid, non-empty SVG, PNG, JPG, or JPEG file within the size limit.",
                    "field": "filename",
                }
            }
        return {"badge": badge_to_dict(badge), "warnings": upload_warnings_to_dicts(warnings)}

    def _mcp_validate_template(arguments: dict) -> dict:
        normalized = _layout_from_json(arguments)
        requested_ids = [str(badge_id) for badge_id in arguments.get("badge_ids", [])]
        resolved_ids = {badge["id"] for badge in normalized["badges"]}
        missing_ids = [badge_id for badge_id in requested_ids if badge_id not in resolved_ids]
        warnings = []
        if missing_ids:
            warnings.append(
                {
                    "code": "unknown_badges",
                    "message": "Some requested badge IDs were not found and will be skipped.",
                    "badge_ids": missing_ids,
                }
            )
        if not normalized["layouts"] or not any(
            layout["placements"] for layout in normalized["layouts"]
        ):
            warnings.append(
                {
                    "code": "empty_layout",
                    "message": "No badge placements were produced for this template.",
                }
            )
        return {"normalized": normalized, "warnings": warnings}

    def _truthy(value) -> bool:
        return str(value).lower() in {"1", "true", "yes", "on"}

    def _mcp_badges_from_uri(uri: str) -> list[Badge] | None:
        parsed = urlsplit(uri)
        if parsed.scheme != "tshirt" or parsed.netloc != "badges" or parsed.path not in {"", "/"}:
            return None
        query = parse_qs(parsed.query)
        if _truthy(query.get("refresh", [False])[0]):
            refresh_badges()
        order = str(query.get("order", ["alphabetical"])[0])
        badges = order_badges(_available_badges(), order)
        if _truthy(query.get("include_logo", [False])[0]) or logo_requested_from_sides(
            query.get("logo_sides", [])
        ):
            badges = [*badges, LOGO_BADGE]
        return badges

    def _handle_mcp_payload(message) -> dict | list[dict]:
        if isinstance(message, list):
            if not message:
                return _mcp_error(None, -32600, "Invalid MCP request: batch must not be empty.")
            return [
                _handle_mcp_message(item)
                if isinstance(item, dict)
                else _mcp_error(None, -32600, "Invalid MCP request: batch items must be JSON-RPC objects.")
                for item in message
            ]
        if not isinstance(message, dict):
            return _mcp_error(None, -32600, "Invalid MCP request: submit a JSON-RPC object or batch array.")
        return _handle_mcp_message(message)

    def _handle_mcp_message(message: dict) -> dict:
        method = message.get("method")
        message_id = message.get("id")
        params = message.get("params", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            return _mcp_error(message_id, -32602, "Invalid MCP params: params must be an object.")
        if method == "initialize":
            requested_version = params.get("protocolVersion")
            return _mcp_result(
                message_id,
                {
                    "protocolVersion": requested_version or "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                        "prompts": {"listChanged": False},
                    },
                    "serverInfo": {"name": "tshirt_templates", "version": APP_VERSION},
                },
            )
        if method == "ping":
            return _mcp_result(message_id, {})
        if method == "notifications/initialized":
            return _mcp_result(message_id, {})
        if method == "tools/list":
            return _mcp_result(message_id, {"tools": _mcp_tools()})
        if method == "resources/list":
            return _mcp_result(
                message_id,
                {
                    "resources": [
                        {"uri": "tshirt://options", "name": "Template options", "mimeType": "application/json"},
                        {"uri": "tshirt://badges", "name": "Badge catalog", "mimeType": "application/json"},
                        {"uri": "tshirt://templates", "name": "Saved templates", "mimeType": "application/json"},
                    ]
                },
            )
        if method == "resources/templates/list":
            return _mcp_result(
                message_id,
                {
                    "resourceTemplates": [
                        {
                            "uriTemplate": MCP_BADGES_URI_TEMPLATE,
                            "name": "Badge catalog with optional ordering and logo inclusion",
                            "mimeType": "application/json",
                        },
                        {
                            "uriTemplate": "tshirt://templates/{name}",
                            "name": "Saved template by name",
                            "mimeType": "application/json",
                        }
                    ]
                },
            )
        if method == "resources/read":
            uri = params.get("uri")
            if uri == "tshirt://options":
                return _mcp_result(message_id, _mcp_json_resource(uri, options_payload()))
            if uri == "tshirt://templates":
                return _mcp_result(message_id, _mcp_json_resource(uri, {"templates": _list_saved_templates()}))
            if isinstance(uri, str) and uri.startswith("tshirt://templates/"):
                template_name = uri.removeprefix("tshirt://templates/")
                template = _read_saved_template(template_name)
                if template is not None:
                    return _mcp_result(message_id, _mcp_json_resource(uri, template))
                return _mcp_error(message_id, -32602, f"Unknown template resource: {uri}")
            badges = _mcp_badges_from_uri(str(uri))
            if badges is not None:
                return _mcp_result(
                    message_id,
                    _mcp_json_resource(str(uri), {"badges": [badge_to_dict(badge) for badge in badges]}),
                )
            return _mcp_error(message_id, -32602, f"Unknown resource: {uri}")
        if method == "prompts/list":
            return _mcp_result(
                message_id,
                {
                    "prompts": [
                        {"name": "design_tshirt_template", "description": "Choose badges and layout options for a shirt concept."},
                        {"name": "optimize_cut_sheet", "description": "Suggest options that reduce wasted transfer paper."},
                        {"name": "explain_layout", "description": "Explain a computed layout and its print settings."},
                    ]
                },
            )
        if method == "prompts/get":
            prompt_name = params.get("name")
            prompts = {
                "design_tshirt_template": "Choose badge IDs, layout options, panel text, and print settings for this shirt concept.",
                "optimize_cut_sheet": "Suggest layout options that reduce transfer-paper waste while preserving badge legibility.",
                "explain_layout": "Explain the selected placement mode, badge order, page setup, and PDF mirroring choices.",
            }
            if prompt_name not in prompts:
                return _mcp_error(message_id, -32602, f"Unknown prompt: {prompt_name}")
            return _mcp_result(
                message_id,
                {
                    "description": prompts[prompt_name],
                    "messages": [
                        {
                            "role": "user",
                            "content": {"type": "text", "text": prompts[prompt_name]},
                        }
                    ],
                },
            )
        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", params.get("input", {})) or {}
            if not isinstance(arguments, dict):
                arguments = {}
            if tool_name == "get_options":
                return _mcp_result(
                    message_id,
                    _mcp_tool_result(options_payload(), "Returned supported template options and defaults."),
                )
            if tool_name == "list_badges":
                if arguments.get("refresh"):
                    refresh_badges()
                order = str(arguments.get("order", "alphabetical"))
                badges = order_badges(_available_badges(), order)
                if arguments.get("include_logo") or logo_requested_from_sides(
                    arguments.get("logo_sides")
                ):
                    badges = [*badges, LOGO_BADGE]
                payload = {"badges": [badge_to_dict(badge) for badge in badges]}
                return _mcp_result(
                    message_id,
                    _mcp_tool_result(payload, f"Returned {len(payload['badges'])} badges."),
                )
            if tool_name == "compute_layout":
                payload = _layout_from_json(arguments)
                return _mcp_result(message_id, _mcp_tool_result(payload, "Computed template layout."))
            if tool_name == "render_pdf":
                payload = _mcp_render_pdf(arguments)
                if "error" in payload:
                    return _mcp_error(
                        message_id,
                        -32602,
                        payload["error"]["message"],
                        {"code": payload["error"]["code"], "failures": payload["error"].get("failures", [])},
                    )
                result = _mcp_tool_result(payload, f"Rendered {payload['byte_length']} PDF bytes.")
                result["content"].append({"type": "resource", "resource": payload["resource"]})
                return _mcp_result(message_id, result)
            if tool_name == "upload_badge_artwork":
                result = _mcp_upload_badge(arguments)
                if "error" in result:
                    return _mcp_error(message_id, -32602, result["error"]["message"])
                return _mcp_result(message_id, _mcp_tool_result(result, "Uploaded badge artwork."))
            if tool_name == "validate_template":
                payload = _mcp_validate_template(arguments)
                return _mcp_result(
                    message_id,
                    _mcp_tool_result(payload, f"Validation returned {len(payload['warnings'])} warnings."),
                )
            if tool_name == "list_saved_templates":
                payload = {"templates": _list_saved_templates()}
                return _mcp_result(
                    message_id,
                    _mcp_tool_result(payload, f"Returned {len(payload['templates'])} saved templates."),
                )
            if tool_name == "save_template":
                result, error = _save_template_payload(arguments)
                if error:
                    return _mcp_error(message_id, -32602, error["message"])
                return _mcp_result(message_id, _mcp_tool_result(result, "Saved template."))
            if tool_name == "get_saved_template":
                template = _read_saved_template(str(arguments.get("name", "")))
                if template is None:
                    return _mcp_error(message_id, -32602, "No saved template exists for that name.")
                return _mcp_result(message_id, _mcp_tool_result(template, "Returned saved template."))
            if tool_name == "delete_saved_template":
                deleted = _delete_saved_template(str(arguments.get("name", "")))
                if deleted is None:
                    return _mcp_error(message_id, -32602, "No saved template exists for that name.")
                return _mcp_result(message_id, _mcp_tool_result({"deleted": deleted}, "Deleted saved template."))
            return _mcp_error(message_id, -32602, f"Unknown tool: {tool_name}")
        return _mcp_error(message_id, -32601, f"Unknown MCP method: {method}")

    return app


app = create_app()
