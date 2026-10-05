import json
import sys
from types import SimpleNamespace

import pytest

from tshirt_templates.badges import Badge
from tshirt_templates.cli import generate_pdf_from_file, main


DEMO_BADGE = Badge(
    id="demo-badge.svg",
    name="Demo Badge",
    path="demo-badge.svg",
    raw_url="/static/demo-badge.svg",
    extension=".svg",
)


def test_generate_pdf_from_file_writes_output(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(render_pdf=lambda *args, **kwargs: calls.append((args, kwargs)) or b"%PDF-1.4\n%%EOF"),
    )
    template = tmp_path / "template.json"
    output = tmp_path / "out" / "template.pdf"
    template.write_text(
        json.dumps(
            {
                "badge_ids": [DEMO_BADGE.id],
                "options": {"sides": ["front"], "front_text": "Ada", "include_print_marks": True},
            }
        ),
        encoding="utf-8",
    )

    content = generate_pdf_from_file(template, output)

    assert content == b"%PDF-1.4\n%%EOF"
    assert output.read_bytes() == content
    assert calls[0][1]["panel_text"]["front"] == "Ada"
    assert calls[0][1]["print_marks"] is True


def test_cli_generate_pdf_command(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("tshirt_templates.cli.generate_pdf_from_file", lambda *args: b"%PDF")
    template = tmp_path / "template.json"
    output = tmp_path / "template.pdf"
    template.write_text("{}", encoding="utf-8")

    assert main(["generate-pdf", str(template), str(output)]) == 0

    assert "Wrote 4 bytes" in capsys.readouterr().out


def test_cli_cleanup_uploads_reports_removed_files(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("tshirt_templates.cli.cleanup_stale_uploads", lambda *args, **kwargs: ["old.svg"])

    assert main(["cleanup-uploads", "--upload-folder", str(tmp_path), "--max-age-days", "7"]) == 0

    output = capsys.readouterr().out
    assert "Removed 1 stale upload(s)." in output
    assert "old.svg" in output


def test_generate_pdf_from_file_rejects_non_object_json(tmp_path):
    template = tmp_path / "template.json"
    template.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="Template JSON must be an object"):
        generate_pdf_from_file(template, tmp_path / "template.pdf")


def test_run_development_server_serves_app_api_and_mcp(monkeypatch):
    calls = []

    class StubApp:
        def run(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr("tshirt_templates.cli.create_app", lambda: StubApp())

    from tshirt_templates.cli import run_development_server

    run_development_server(host="0.0.0.0", port=8080, debug=True)

    assert calls == [{"host": "0.0.0.0", "port": 8080, "debug": True}]


def test_cli_serve_command_runs_unified_server(monkeypatch):
    calls = []
    monkeypatch.setattr("tshirt_templates.cli.run_development_server", lambda **kwargs: calls.append(kwargs))

    assert main(["serve", "--host", "0.0.0.0", "--port", "8080", "--debug"]) == 0

    assert calls == [{"host": "0.0.0.0", "port": 8080, "debug": True}]
