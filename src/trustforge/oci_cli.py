"""OCI inspection presentation; no implicit trust or deployment decision."""

from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from trustforge.oci.client import inspect_reference
from trustforge.oci.errors import OciError
from trustforge.oci.models import Descriptor, ImageIndex

app = typer.Typer(
    help="Read-only OCI metadata inspection.", no_args_is_help=True, add_completion=False
)


def platform_label(descriptor: Descriptor) -> str:
    platform = descriptor.platform
    if platform is None:
        return "unknown"
    parts = [platform.os, platform.architecture]
    if platform.variant:
        parts.append(platform.variant)
    return "/".join(parts)


@app.command("inspect")
def inspect_command(
    reference: Annotated[str, typer.Argument(help="Registry reference, tag or sha256 digest.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON metadata.")] = False,
) -> None:
    """Read one manifest/index; do not download layers or execute an image."""
    try:
        result = inspect_reference(reference)
    except OciError as error:
        if json_output:
            import json

            typer.echo(
                json.dumps(
                    {"schema_version": 1, "error": {"code": error.code, "message": str(error)}},
                    sort_keys=True,
                ),
                err=True,
            )
        else:
            Console(stderr=True).print(f"{error.code}: {error}", style="red", markup=False)
        raise typer.Exit(code=error.exit_code) from None
    if json_output:
        typer.echo(result.model_dump_json(by_alias=True))
        return
    console = Console(highlight=False)
    console.print(f"Kind: {result.kind}", markup=False)
    console.print(f"Media type: {result.media_type}", markup=False)
    console.print(f"Digest: {result.digest}", markup=False)
    console.print(f"Metadata bytes: {result.size_bytes}", markup=False)
    console.print(f"Resolved: {result.resolved_reference}", markup=False)
    console.print(
        "Platform is reported from descriptors only; config/child manifests are not fetched."
    )
    table = Table(title="Observed descriptors (not fetched)")
    for name in ("Role", "Media type", "Digest", "Bytes", "Platform"):
        table.add_column(name)
    document = result.document
    if isinstance(document, ImageIndex):
        descriptors = [("manifest", descriptor) for descriptor in document.manifests]
    else:
        descriptors = [
            ("config", document.config),
            *(("layer", layer) for layer in document.layers),
        ]
    if document.subject is not None:
        descriptors.append(("subject", document.subject))
    for role, descriptor in descriptors:
        table.add_row(
            role,
            descriptor.media_type,
            descriptor.digest,
            str(descriptor.size),
            platform_label(descriptor),
        )
    console.print(table)
    console.print("Metadata integrity only; authenticity and deployment are not verified.")
