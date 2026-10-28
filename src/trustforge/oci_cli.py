"""OCI inspection presentation; no implicit trust or deployment decision."""

from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from trustforge.oci.client import PlatformInspection, inspect_reference
from trustforge.oci.errors import OciError
from trustforge.oci.head import head_reference
from trustforge.oci.models import Descriptor, ImageIndex
from trustforge.oci.referrers import list_referrers

app = typer.Typer(
    help="Read-only OCI metadata inspection.", no_args_is_help=True, add_completion=False
)


def operation_error(error: OciError, json_output: bool) -> None:
    """Shared sanitized CLI error contract for metadata commands."""
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
    platform: Annotated[
        str | None,
        typer.Option("--platform", help="Select os/architecture with an optional /variant."),
    ] = None,
) -> None:
    """Read one manifest/index; do not download layers or execute an image."""
    try:
        result = (
            inspect_reference(reference)
            if platform is None
            else inspect_reference(reference, platform=platform)
        )
    except OciError as error:
        operation_error(error, json_output)
        return
    if json_output:
        typer.echo(result.model_dump_json(by_alias=True))
        return
    console = Console(highlight=False)
    console.print(f"Kind: {result.kind}", markup=False)
    console.print(f"Media type: {result.media_type}", markup=False)
    console.print(f"Digest: {result.digest}", markup=False)
    console.print(f"Metadata bytes: {result.size_bytes}", markup=False)
    console.print(f"Resolved: {result.resolved_reference}", markup=False)
    console.print("Platforms are index claims; configs and layers are never fetched.")
    if isinstance(result, PlatformInspection):
        selection = result.selection
        console.print(f"Index digest: {selection.index_digest}", markup=False)
        console.print(f"Selected platform: {platform_label(selection.descriptor)}", markup=False)
        console.print(f"Child manifest digest: {selection.manifest_digest}", markup=False)
        console.print(f"Child resolved: {selection.resolved_reference}", markup=False)
        console.print(f"Child metadata bytes: {selection.manifest.size_bytes}", markup=False)
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


@app.command("head")
def head_command(
    reference: Annotated[str, typer.Argument(help="Registry reference by tag or digest.")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit JSON header observations.")
    ] = False,
) -> None:
    """Observe manifest headers without reading its body or verifying content."""
    try:
        result = head_reference(reference)
    except OciError as error:
        operation_error(error, json_output)
        return
    if json_output:
        typer.echo(result.model_dump_json(by_alias=True))
        return
    console = Console(highlight=False)
    console.print(f"Registry digest claim: {result.digest}", markup=False)
    console.print(f"Media type: {result.media_type}", markup=False)
    console.print(f"Declared metadata bytes: {result.size_bytes}", markup=False)
    console.print(
        "HEAD headers only; content integrity, authenticity and deployment are not verified."
    )


@app.command("referrers")
def referrers_command(
    reference: Annotated[str, typer.Argument(help="Subject reference by tag or digest.")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit registry referrer claims.")
    ] = False,
    artifact_type: Annotated[
        str | None, typer.Option("--artifact-type", help="Filter by exact artifact media type.")
    ] = None,
) -> None:
    """Discover registry-declared referrers without downloading their payloads."""
    try:
        result = list_referrers(reference, artifact_type=artifact_type)
    except OciError as error:
        operation_error(error, json_output)
        return
    if json_output:
        typer.echo(result.model_dump_json(by_alias=True))
        return
    console = Console(highlight=False)
    console.print(f"Subject digest: {result.subject_digest}", markup=False)
    console.print(f"List source: {result.source}; status: {result.status}", markup=False)
    table = Table(title="Registry-declared referrers (payloads not fetched)")
    for name in ("Artifact type", "Media type", "Digest", "Bytes", "Annotations"):
        table.add_column(name)
    for item in result.referrers:
        table.add_row(
            item.artifact_type or "unspecified",
            item.media_type,
            item.digest,
            str(item.size),
            str(len(item.annotations)),
        )
    console.print(table)
    console.print("Registry claims only; subject associations and authenticity are not verified.")
