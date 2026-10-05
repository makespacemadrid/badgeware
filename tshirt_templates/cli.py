"""Command-line helpers for generating t-shirt template PDFs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .app import create_app
from .uploads import cleanup_stale_uploads


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tshirt_templates.cli",
        description="Generate t-shirt sublimation template assets from JSON requests.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    generate_pdf = subcommands.add_parser(
        "generate-pdf",
        help="Generate a PDF from a JSON template request file.",
    )
    generate_pdf.add_argument(
        "template",
        type=Path,
        help="JSON file with badge_ids, options, and optional manual_placements.",
    )

    cleanup = subcommands.add_parser("cleanup-uploads", help="Delete stale locally uploaded artwork.")
    cleanup.add_argument("--upload-folder", type=Path, required=True, help="Upload folder to clean.")
    cleanup.add_argument("--max-age-days", type=float, default=30, help="Delete files older than this many days.")
    cleanup.add_argument("--dry-run", action="store_true", help="List stale files without deleting them.")
    generate_pdf.add_argument(
        "output",
        type=Path,
        help="Destination PDF path.",
    )
    generate_pdf.add_argument(
        "--upload-folder",
        type=Path,
        help="Folder containing previously uploaded badge artwork referenced by upload: IDs.",
    )

    serve = subcommands.add_parser(
        "serve",
        help="Run the browser app, JSON API, and MCP endpoint in one Flask server.",
    )
    serve.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface for the development server (default: 127.0.0.1).",
    )
    serve.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port for the development server (default: 5000).",
    )
    serve.add_argument(
        "--debug",
        action="store_true",
        help="Enable Flask debug mode.",
    )
    return parser


def generate_pdf_from_file(
    template_path: Path, output_path: Path, upload_folder: Path | None = None
) -> bytes:
    """Generate PDF bytes from a JSON template file and write them to output_path."""

    payload = json.loads(template_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Template JSON must be an object.")

    app = create_app()
    if upload_folder is not None:
        app.config["UPLOAD_FOLDER"] = str(upload_folder)

    response = app.test_client().post("/api/v1/pdfs", json=payload)
    if response.status_code != 200:
        error_payload = response.get_json(silent=True) or {}
        message = error_payload.get("error", {}).get("message", response.get_data(as_text=True))
        raise RuntimeError(f"PDF generation failed: {message}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.data)
    return response.data


def run_development_server(
    host: str = "127.0.0.1", port: int = 5000, debug: bool = False
) -> None:
    """Run the Flask app that serves the browser UI, JSON API, and MCP endpoint."""

    app = create_app()
    app.run(host=host, port=port, debug=debug)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the tshirt_templates command-line interface."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "serve":
        run_development_server(host=args.host, port=args.port, debug=args.debug)
        return 0

    if args.command == "generate-pdf":
        try:
            content = generate_pdf_from_file(args.template, args.output, args.upload_folder)
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
            parser.error(str(error))
        print(f"Wrote {len(content)} bytes to {args.output}")
        return 0

    if args.command == "cleanup-uploads":
        removed = cleanup_stale_uploads(args.upload_folder, args.max_age_days, dry_run=args.dry_run)
        action = "Would remove" if args.dry_run else "Removed"
        print(f"{action} {len(removed)} stale upload(s).")
        for filename in removed:
            print(filename)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
