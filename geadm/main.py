"""geadm — read-only troubleshooting / debug / stats CLI for Google Gemini Enterprise.

Targets the Discovery Engine / Agentspace product (discoveryengine.googleapis.com).
Strictly read-only: needs only roles/discoveryengine.viewer, roles/logging.viewer
and roles/monitoring.viewer. Auth is Application Default Credentials.
"""

from __future__ import annotations

from dataclasses import dataclass

import typer

app = typer.Typer(
    name="geadm",
    help=__doc__,
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@dataclass
class AppState:
    project: str | None
    location: str


@app.callback()
def main(
    ctx: typer.Context,
    project: str = typer.Option(
        None,
        "--project",
        "-p",
        help="GCP project ID (defaults to the ADC project).",
        envvar="GOOGLE_CLOUD_PROJECT",
    ),
    location: str = typer.Option(
        "global",
        "--location",
        "-l",
        help="Gemini Enterprise location (e.g. global, us, eu).",
    ),
) -> None:
    """Read-only troubleshooting CLI for Google Gemini Enterprise."""
    ctx.obj = AppState(project=project, location=location)


# ---- command groups (implemented in geadm/commands/) -----------------------

ls_app = typer.Typer(help="List Gemini Enterprise resources (read-only).", no_args_is_help=True)
logs_app = typer.Typer(help="Inspect Gemini Enterprise Cloud Logging output.", no_args_is_help=True)

app.add_typer(ls_app, name="ls")
app.add_typer(logs_app, name="logs")


@app.command()
def stats(ctx: typer.Context) -> None:
    """Query volume, latency and connector sync freshness (stub)."""
    raise typer.Exit(code=1)


@app.command()
def doctor(ctx: typer.Context) -> None:
    """Composite read-only health check (stub)."""
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
