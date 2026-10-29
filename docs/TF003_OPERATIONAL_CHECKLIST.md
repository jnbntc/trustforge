# TF-003 — primera validación operativa, pendiente de autorización

Preparado el 2026-10-29. Fuente única: [distrobox-stack, commit revisado 541115eecce9e72bd4989ad5ac1c28f14a1a0c59](https://github.com/jnbntc/distrobox-stack/tree/541115eecce9e72bd4989ad5ac1c28f14a1a0c59/workspaces/trustforge-dev). Este documento consume el contrato; no duplica Containerfile, manifest, locks ni verificador. [ADR-013](adr/013-distrobox-stack-workspace.md) sigue vigente.

**No ejecutar esta secuencia todavía.** Cada puerta exige una decisión humana registrada. La preparación ejecutó únicamente los 27 tests estáticos/offline canónicos; Cosign y la imagen reales no se ejecutaron. No se aprueba aquí identidad, política ni raíz alguna.

## 1. Prerrequisitos y gobernanza — puerta humana G0

- Confirmar host Fedora Atomic real y usuario normal mediante la guía [preflight](FEDORA_ATOMIC_PREFLIGHT.md); conservar evidencia privada. Los datos históricos aportados por el propietario no sustituyen una comprobación actual. No instalar/reparar herramientas en este paso.
- Disponer de checkout de stack revisado, Python estándar y, para las operaciones futuras aprobadas, gh autenticado con los permisos existentes. Si faltan, registrar el bloqueo; no instalar herramientas globales.
- Aplicar y verificar por el propietario [main/checks/environment](GITHUB_GOVERNANCE.md). La lista de colaboradores requiere reautenticación y no fue comprobada: identificar un revisor elegible diferente del iniciador, o mantener publicación bloqueada.
- Registrar inventario y recursos previos cuando se autorice consultar Podman/Distrobox; nunca sustituir o reiniciar un workspace existente. Confirmar espacio/arquitectura y alcance de HOME/cachés/checkout. No ejecutar contenido adversario.

Comprobaciones futuras desde el checkout revisado; no son comandos de configuración:

```bash
TF_STACK_SHA=541115eecce9e72bd4989ad5ac1c28f14a1a0c59
test "$(git rev-parse HEAD)" = "$TF_STACK_SHA"
test -z "$(git status --porcelain)"
python3 -B workspaces/trustforge-dev/validate-static.py
gh api repos/jnbntc/distrobox-stack/branches/main --jq '.commit.sha, .protected'
gh api repos/jnbntc/distrobox-stack/rulesets
gh api repos/jnbntc/distrobox-stack/environments/trustforge-bootstrap-publish
```

Detenerse si el main remoto no coincide con el SHA revisado, no hay enforcement efectivo o falta el environment/revisor/regla de rama main. Un ruleset vacío puede coexistir con protección clásica válida: comprobar la protección que realmente se aplique. Un nombre en YAML no demuestra protección.

## 2. Política y anclas independientes — puerta humana GT

| Entrada propuesta por el contrato | Aprobación/evidencia requerida |
|---|---|
| Imagen ghcr.io/jnbntc/trustforge-dev | Digest final aún inexistente; nunca consumir el tag como autorización |
| Issuer https://token.actions.githubusercontent.com | Aceptación explícita del propietario |
| Identity https://github.com/jnbntc/distrobox-stack/.github/workflows/trustforge-dev.yml@refs/heads/main | URI exacta; repository jnbntc/distrobox-stack, ref refs/heads/main, trigger workflow_dispatch y source SHA revisado |
| Cosign v3.1.4 linux/amd64 | Binario obtenido fuera de la imagen mediante canal oficial independiente aprobado; hash del contrato 424e2c97d0b45fd7a6b608a87f090f35633f4c23ece5f092d48bba11aaf4bbfa |
| Sigstore TrustedRoot JSON | Procedencia auténtica e independiente aprobada, por ejemplo distribución Sigstore validada mediante TUF; registrar cadena de adquisición, fecha y SHA-256 real. Un checksum suministrado junto al archivo no demuestra esa procedencia |
| Política externa | Copia privada revisada de trust-policy.example.json: approved solo tras aprobación humana, source_commit exacto y trusted_root_sha256 real. No aprobar ni guardar secretos/anclas nuevas en el repositorio |

El source SHA de la política procede de revisión confiable, nunca de una atestación recibida. Si stack main cambia antes del dispatch, revisar el nuevo SHA y la política de nuevo. Comprobar binario/raíz con sha256sum sobre las rutas independientes aprobadas; no obtenerlos de la imagen a aceptar.

## 3. Candidato sin publicación — puerta humana GB

Solo tras autorización concreta de build para ese commit, plataforma e impactos:

```bash
gh workflow run trustforge-dev.yml --repo jnbntc/distrobox-stack --ref main -F publish=false
gh run list --repo jnbntc/distrobox-stack --workflow trustforge-dev.yml \
  --event workflow_dispatch --commit "$TF_STACK_SHA" --limit 5 \
  --json databaseId,headSha,status,conclusion,url
# Elegir y registrar el ID real; no tomar silenciosamente cualquier último run.
gh run view "$TF_BUILD_RUN_ID" --repo jnbntc/distrobox-stack \
  --json headSha,event,status,conclusion,jobs,url
```

Verificar headSha exacto, evento manual, publish=false, build satisfactorio y publish omitido. Evidencia esperada: artefacto trustforge-dev-candidate con trustforge-dev.oci.tar, workspace.build.json y candidate.sha256; source/workflow/run/attempt/plataforma coherentes, receta y pins del contrato, hashes y logs revisados. La descarga/inspección del archivo OCI pertenece al alcance de ese build futuro, no a esta sesión. El checksum del archivo OCI no es el digest del manifest publicado ni prueba autenticidad. Sin evidencia satisfactoria no avanzar.

Impactos futuros: runner/cachés/descargas OCI y de dependencias, archivo candidato y retención del artefacto durante siete días. No crea Distrobox en Fedora. RPM e inicialización siguen móviles: inventario y repetición por digest no demuestran rebuild idéntico.

## 4. Publicación y firma — puerta humana GP

Autorización independiente para un dispatch publish=true del mismo source revisado, con environment ya protegido y aprobación independiente. **El workflow actual reconstruye en ese segundo run**; no promueve automáticamente el candidato de GB. Esa autorización incluye la nueva construcción y su revisión.

```bash
gh workflow run trustforge-dev.yml --repo jnbntc/distrobox-stack --ref main -F publish=true
```

El job publish usa needs: build, main-only y environment trustforge-bootstrap-publish; únicamente allí solicita packages:write e id-token:write. Verifica archivo/registro, publica, captura workspace.digest y firma/atesta por ese digest final. Esperar firma dedicada sign/v1 con anotación firmada io.trustforge.repository, SBOM SPDX y provenance custom separadas. Evidencia: workspace.digest, workspace.build.json, workspace.sbom.spdx.json, workspace.provenance.json, run/attempt/source y resultado de cada paso. Si falla algo tras push, puede quedar una imagen publicada incompleta: no desplegar ni borrar automáticamente artefactos para ocultar el fallo.

## 5. Verificación independiente — puerta humana GV

Después de aprobar el alcance de consulta criptográfica real y disponer de política, raíz y binario externos aprobados:

```bash
python3 -B workspaces/trustforge-dev/verify-bootstrap.py \
  --image "$TF_FINAL_IMAGE_BY_DIGEST" \
  --policy "$TF_APPROVED_POLICY" \
  --cosign "$TF_INDEPENDENT_COSIGN" \
  --trusted-root "$TF_APPROVED_TRUSTED_ROOT" \
  > "$TF_PRIVATE_EVIDENCE/verification.json"
```

Todas las variables representan valores reales aprobados; rutas absolutas para herramienta/raíz y repositorio permitido con sha256 de 64 hex. Conservar stdout/stderr/exit y hashes sin publicar secretos ni salidas completas del host. El verificador exige tres verificaciones Cosign tipadas, identidad/issuer/workflow/source, claims/tlog/SCT y subject/digest/repositorio; sin fallback. Reproducir negativos reales: firma ausente/sustituida, identidad/issuer/source/subject erróneos y evidencia incompleta. Un fallo de interoperabilidad de Cosign/GHCR es bloqueo, no razón para relajar controles. [Contrato exacto y fuente oficial](https://github.com/jnbntc/distrobox-stack/blob/541115eecce9e72bd4989ad5ac1c28f14a1a0c59/workspaces/trustforge-dev/COSIGN_INTERFACE.md).

## 6. Creación, pruebas y rollback — puerta humana GD

VERIFIED mantiene deployment_authorized=false. Pedir una autorización nueva para crear/iniciar exclusivamente trustforge-dev con ese mismo digest. Antes de cualquier creación, confirmar ausencia de colisión y registrar recursos existentes; renderizar con render-manifest.py --image "$TF_FINAL_IMAGE_BY_DIGEST" --host-home "$TF_HOST_HOME" y revisar el manifest individual. No usar manifest global, stack.sh ni make.

La futura aprobación debe incluir estos comandos individuales, primer inicio/entrada, descarga por digest, rutas/almacenamiento y consultas de runtime. Solo tras GD, con inventario previo y variables revisadas:

```bash
# Una colisión o error del motor aborta; no usar --replace.
if podman container exists trustforge-dev; then
  echo 'trustforge-dev ya existe; detenerse' >&2; exit 1
else
  TF_EXISTS_STATUS=$?
  test "$TF_EXISTS_STATUS" -eq 1 || exit "$TF_EXISTS_STATUS"
fi
python3 -B workspaces/trustforge-dev/render-manifest.py \
  --image "$TF_FINAL_IMAGE_BY_DIGEST" --host-home "$TF_HOST_HOME" > "$TF_MANIFEST"
# Revisar el manifest: una única sección, digest aprobado, pull/start/entry/replace=false.
podman pull "$TF_FINAL_IMAGE_BY_DIGEST"
distrobox assemble create --file "$TF_MANIFEST" --name trustforge-dev
TF_CREATED_CONTAINER_ID=$(podman container inspect trustforge-dev --format '{{.Id}}')
test -n "$TF_CREATED_CONTAINER_ID"
# Conservar ID y baseline en evidencia privada antes del primer inicio.
distrobox enter --name trustforge-dev -- trustforge-python --version
```

La sintaxis de selección individual procede del [assemble fijado de Distrobox](https://github.com/89luca89/distrobox/blob/40c3cd724faa434aeb0a23e28776665b92de68bd/distrobox-assemble). El primer enter inicializa e integra el contenedor: requiere esa aprobación, no es una comprobación inocua de versión del host. Registrar digest, mounts/flags/sockets visibles, rootless, herramientas, red, checkout/persistencia y efectos de SELinux/Distrobox. No usar este workspace como sandbox M4.

Rollback aprobado y acotado: parar/eliminar únicamente el ID nuevo registrado; conservar checkout/evidencia y revisar HOME/cachés antes de borrar recursos identificados como nuevos. Quitar una imagen solo si es nueva y no compartida. Nada de prune/reset, graphroot, otros contenedores o limpieza global. Borrar el contenedor no revierte escrituras en bind mounts. Registrar el resultado y revisar aceptación de TF-003; no cerrar automáticamente.

```bash
# Solo para rollback aprobado del contenedor nuevo registrado en esta intervención.
test -n "$TF_CREATED_CONTAINER_ID"
test "$(podman container inspect trustforge-dev --format '{{.Id}}')" = "$TF_CREATED_CONTAINER_ID"
podman stop "$TF_CREATED_CONTAINER_ID"
podman rm "$TF_CREATED_CONTAINER_ID"
```

**Próxima decisión concreta:** el propietario configura/verifica gobernanza y aprueba GT; después puede autorizar GB con publish=false. Publicación, verificación y despliegue quedan separados. M0 permanece incompleto.
