"""CLI wiring smoke tests: every command exposes working --help."""

import pytest

from geadm.main import app


@pytest.mark.parametrize(
    "args",
    [
        ["--help"],
        ["ls", "--help"],
        ["ls", "engines", "--help"],
        ["ls", "datastores", "--help"],
        ["ls", "connectors", "--help"],
        ["ls", "agents", "--help"],
        ["logs", "--help"],
        ["logs", "connector", "--help"],
        ["logs", "user", "--help"],
        ["stats", "--help"],
        ["quota", "--help"],
        ["doctor", "--help"],
    ],
)
def test_help_screens(app_runner, args):
    result = app_runner.invoke(app, args)
    assert result.exit_code == 0, result.output


def test_help_names_viewer_roles(app_runner):
    combined = ""
    for args in (["ls", "--help"], ["logs", "--help"], ["stats", "--help"]):
        combined += app_runner.invoke(app, args).output
    assert "discoveryengine.viewer" in combined
    assert "logging.viewer" in combined
    assert "monitoring.viewer" in combined


def test_logs_user_help_mentions_prompt_logging(app_runner):
    out = app_runner.invoke(app, ["logs", "user", "--help"]).output
    assert "prompt/response" in out
