# T-Shirt Sublimation Template Generator

A Flask web application that builds printable PDF templates for front and back t-shirt sublimation sheets using badge artwork from [`makespacemadrid/open-badges`](https://github.com/makespacemadrid/open-badges).

The app discovers badge image assets from the GitHub repository, lets you select badges, choose automatic placement strategies, preview the generated layout, and export a PDF ready for printing.

## Features

- Fetches SVG/PNG/JPG badge assets from the GitHub repository via the GitHub contents API, with an automatic 10-minute refresh window plus a **Refresh badges from GitHub** action to pick up newly added upstream files immediately.
- Front and back print panels with independent layout generation.
- Automatic placement modes:
  - **Grid**: even rows and columns.
  - **Rows**: staggered horizontal bands.
  - **Diagonal**: sash-style diagonal placement.
  - **Scatter**: deterministic pseudo-random distribution.
  - **Circle wreath**: badges arranged around an oval ring.
  - **Spiral trail**: badges flowing outward from the panel center.
  - **Wave ribbon**: badges following a horizontal sine-wave band.
  - **Border**: perimeter frame layout for collar/sleeve-style badge accents.
  - **M pixel shape**: pixel-art capital M that repeats the selected badges as mosaic pixels, expands to denser M grids for larger selections, and scales dense mosaics down only as needed to stay inside the selected panel. A no-shrink variant keeps badge artwork at the requested size and moves overflow badges first to a line above the M, then lines above and below, then a square frame, and finally a double-square frame.
- Configurable page size (A4 by default), page orientation, centimeter/inch units, page margin/panel gap controls, badge size presets, spacing presets with density-aware automatic shrinking for crowded grid/row layouts, copies per badge, mirroring, and panel selection, with invalid form values safely normalized and grouped into step-by-step controls plus a quick print guide.
- Optional front/back panel text for names or short labels, with Ubuntu as the default font plus Fredoka One, Helvetica, Times, Courier, and DejaVu Sans choices.
- User uploads for additional SVG/PNG/JPG badge artwork stored under the Flask `instance/uploads/` folder, with browser and API replacement/deletion for saved uploads and validation notices for questionable image dimensions or invalid artwork.
- Optional mirroring for sublimation transfer workflows plus badge cut-line outlines, crop/registration print marks, a yellow unifier layer for evening out badge yellow tones, a mug/canteen curved-adapter effect with device presets and configurable diameter, and a calibration page with rulers/mirror warnings for alignment.
- Optional MakeSpace Madrid logo element with configurable size.
- Badge picker cards are selected by default, searchable/filterable by category, bulk selectable with live selected/visible counts, and drag-and-droppable before previewing to customize selection-order layouts.
- MakeSpace-inspired black/yellow monospace UI theme plus browser save/load/delete controls for design templates, preview with manual drag/coordinate placement adjustments, multi-select group movement, reset controls, zoom, snap-to-grid, snap-to-panel-edge controls, keyboard nudging, panel alignment/distribution tools, rotation presets, overlap warnings, and PDF download.
- JSON API endpoints for health/options/badges, API uploads, layout previews, saved template files (including optional front/back `side_badge_ids` for browser-saved designs), and direct PDF generation, plus MCP-compatible tools/resources/prompts and a CLI for agent-driven or repeatable local PDF workflows.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m tshirt_templates.cli serve --debug
```

Open <http://127.0.0.1:5000>. The same server also exposes API discovery at `/api/v1`, the JSON API under `/api/v1`, and the MCP JSON-RPC endpoint at `/mcp`, so the browser UI, API clients, and MCP clients all run from one app process. MCP clients do not need a reserved port; configure them with the reachable `http://HOST:PORT/mcp` URL and use `--port` only when you want a stable local/container port.

## Docker

Build and run the production container with Docker Compose:

```bash
docker compose up --build
```

Open <http://127.0.0.1:5000>. Uploaded artwork and saved templates are kept in
the `badgeware-data` volume, which is mounted at `/app/instance` in the
container. Stop the service with `docker compose down`; add `--volumes` only
when you also want to delete that persisted application data.

To publish the app on another port, set `PORT` for both the container and the
host mapping:

```bash
PORT=8080 docker compose up --build
```

For a public deployment, also provide a stable, random Flask session secret
(do not commit it to the Compose file):

```bash
SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')" docker compose up --build
```

Store that value in your deployment platform's secret manager or a local
`.env` file so browser sessions remain valid after container restarts. The
development fallback is intentionally suitable only for local use.

You can also use Docker directly:

```bash
docker build -t badgeware .
docker run --rm -p 5000:5000 -v badgeware-data:/app/instance badgeware
```

The image runs Gunicorn as an unprivileged user, writes access and error logs
to the container log stream, allows `WEB_CONCURRENCY` and `GUNICORN_TIMEOUT`
to tune worker count and long-running PDF requests, and includes a health check
for `/api/v1/health`.

If you prefer Flask's built-in CLI, this equivalent command serves the same UI, API, and MCP routes:

```bash
flask --app tshirt_templates.app run --debug
```

## CLI PDF generation

Generate a PDF from the same JSON request shape used by `/api/v1/pdfs`:

```bash
python -m tshirt_templates.cli generate-pdf template.json tshirt-badge-template.pdf
```

Use `--upload-folder instance/uploads` when the JSON references previously uploaded `upload:` badge IDs.

## Documentation

- [`docs/SPECS.md`](docs/SPECS.md): Technical specifications for the current application.
- [`docs/APIDOCS.md`](docs/APIDOCS.md): Initial API/MCP endpoints and future integration details.
- [`docs/IDEAS.md`](docs/IDEAS.md): Potential product, layout, API, testing, and accessibility improvements.

## Testing

```bash
python -m py_compile tshirt_templates/*.py
python -m ruff check .
python -m pytest
```

The pytest suite includes dependency-light unit coverage for layout, badge discovery, uploads, option parsing, CLI generation, API option payloads, yellow-unifier PDF metadata/drawing, saved design template round trips, PDF handoff behavior, and MCP resources/tools. Flask route integration tests are also included and run automatically when the runtime dependencies from `requirements.txt` are installed.

## Notes

- The app caches the GitHub badge listing in memory for 10-minute windows to avoid repeated API calls; use the refresh button to clear that cache and fetch the latest repository `HEAD` immediately.
- Badge refreshes, upload saves/rejections, and PDF asset/preflight failures are logged as JSON event records through Flask's application logger so local operators can filter them by `event`, `route`, `reason`, and count fields.
- If GitHub cannot be reached, a built-in demo badge is shown so the UI and PDF flow remain usable.
- SVG rendering in PDFs is handled with `svglib` and `reportlab`.
