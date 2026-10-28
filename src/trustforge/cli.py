"""CLI foundation and read-only OCI metadata inspection."""

import json
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from trustforge import __version__
from trustforge.doctor import collect_checks
from trustforge.oci_cli import app as oci_app

app = typer.Typer(
    name="trustforge",
    help="TrustForge: development diagnostics and read-only OCI metadata inspection.",
    no_args_is_help=True,
    add_completion=False,
)
app.add_typer(oci_app, name="oci")


@app.command()
def version() -> None:
    """Print the installed application version."""
    typer.echo(f"TrustForge {__version__}")


@app.command()
def doctor(
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit a machine-readable report without host paths.")
    ] = False,
) -> None:
    """Check development prerequisites using Python/PATH only."""
    report = collect_checks()
    if json_output:
        payload = report.model_dump(mode="json")
        payload["ready"] = report.is_ready()
        typer.echo(json.dumps(payload, sort_keys=True))
    else:
        table = Table(title="Development prerequisites")
        table.add_column("Requirement")
        table.add_column("Status")
        for check in report.checks:
            table.add_row(check.requirement, "PASS" if check.available else "MISSING")
        console = Console(highlight=False)
        console.print(table)
        console.print(
            "Ready for local development."
            if report.is_ready()
            else "Missing development prerequisites."
        )
    if not report.is_ready():
        raise typer.Exit(code=1)


def main() -> None:
    """Installed console entry point."""
    app()


if __name__ == "__main__":
    main()
