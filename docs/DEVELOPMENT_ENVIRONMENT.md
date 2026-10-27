# TF-003 — Contrato consumidor de trustforge-dev

Estado: propuesta de integración; revisión arquitectónica pendiente. Sin construcción, publicación ni creación del entorno.
Issue: [TF-003 / #3](https://github.com/jnbntc/trustforge/issues/3).
Definición canónica propuesta: [distrobox-stack PR #18](https://github.com/jnbntc/distrobox-stack/pull/18).
Snapshot revisable: [workspaces/trustforge-dev](https://github.com/jnbntc/distrobox-stack/tree/44851ec911ebc0eabba88eb18c53cb4849229754/workspaces/trustforge-dev), commit `44851ec911ebc0eabba88eb18c53cb4849229754`.

## Responsabilidades y contrato
distrobox-stack define receta, herramientas, locks, plantilla, build/publicación y mantenimiento. TrustForge documenta los requisitos del consumidor y valida que el entorno los cumpla; no contiene otro Containerfile, manifest o lock de herramientas del workspace.

- Plataforma inicial: linux/amd64 sobre Podman rootless. Fedora Toolbox 44, por digest validado de manifiesto de plataforma. Arquitecturas adicionales requieren definición y prueba separadas.
- Python de aplicación: 3.13 gestionado por uv; parche exacto, build y SHA-256 de origen en el [contrato canónico](https://github.com/jnbntc/distrobox-stack/tree/44851ec911ebc0eabba88eb18c53cb4849229754/workspaces/trustforge-dev/contract.json). No reemplazar Python del host ni /usr/bin/python3.
- Herramientas: Git, utilidades OCI de inspección, pytest, Ruff y mypy según ese contrato y su [lock con hashes](https://github.com/jnbntc/distrobox-stack/tree/44851ec911ebc0eabba88eb18c53cb4849229754/workspaces/trustforge-dev/requirements.lock). Pydantic/HTTPX/Typer/Rich y dependencias de la aplicación se fijarán en TF-004 dentro de este repositorio.
- Imagen final: solo `ghcr.io/jnbntc/trustforge-dev@sha256:...` después de verificar sus evidencias. El digest de Fedora base no es el digest del workspace; el segundo aún no existe como resultado de esta tarea.
- Checkout explícito: ~/Proyectos/trustforge en /workspace/trustforge, lectura/escritura. HOME/cachés dedicados según la definición canónica, sin exports al host ni instalaciones en el Python del sistema.
- No configuración de storage.conf, cambio de graphroot, motor anidado ni solicitud explícita de dispositivos/capacidades/sockets. No modificar otros workspaces.

Los datos de preflight del host fueron aportados por el usuario para esta planificación; este ejecutor no los volvió a auditar. No se publican inventarios ni salidas completas del host. Las versiones instaladas comunicadas no prueban funcionamiento del futuro contenedor.

## Evidencia estática disponible
Se verificaron por HTTPS los índices y manifiestos linux/amd64 de Fedora Toolbox 44 y uv: hash de bytes contra cabecera y descriptor, sin descargar capas.
Se contrastó el origen de Python con uv 0.13.6 y se resolvió el lock de herramientas para Python 3.13.18/linux x86_64, sin instalarlas. Pins, hashes, herramientas/resolver y límites están en el contrato y README canónicos; esta página no es una segunda fuente editable de pins.
Pasaron seis pruebas offline del workspace, incluyendo rechazo de tag mutable, repositorio distinto, digest malformado e inyección en rutas. Se validaron YAML, sintaxis shell/Containerfile, enlaces y permisos/triggers; no se ejecutaron motores.
No existe evidencia de build, inicialización Distrobox, acceso al checkout, red, SELinux, herramientas ejecutadas dentro de la imagen ni dos reconstrucciones reproducibles. Hadolint/ShellCheck/actionlint no estaban disponibles en el ejecutor y no se instalaron.

## Bloqueo arquitectónico que debe resolverse antes del despliegue
Distrobox 1.8.2.5 añade internamente --privileged y --security-opt label=disable. Un HOME dedicado y unshare_all no eliminan esos flags ni todos los montajes: HOME original y /run/user pueden compartirse, dando visibilidad a sockets de sesión/runtime.
Por eso rootless no demuestra confinamiento SELinux ni ausencia de accesos heredados. La propuesta no agrega privilegios explícitos; **no satisface aún una garantía estricta de Distrobox sin privilegios o sockets compartidos**.
Revisar [ADR-013 propuesto](adr/013-distrobox-stack-workspace.md): no aceptar silenciosamente la integración ni sustituir el consumidor por otro runtime sin revisión.

## Criterios de validación para completar TF-003
- [x] Definición única, declarativa y revisable en distrobox-stack; referencias de ambos repositorios coherentes.
- [x] Fuentes base/uv por digest, Python gestionado y lock de herramientas con hashes.
- [x] Pruebas estáticas/negativas; preservación de manifests, orquestadores, imágenes y workflows existentes.
- [ ] Revisar y aceptar arquitectura/privilegios/montajes reales de Distrobox.
- [ ] Aprobar y ejecutar build, medir inventario RPM/tamaño y probar la toolchain con Python gestionado.
- [ ] Fijar digest final; generar SBOM, firma Cosign y provenance mediante mecanismos soportados y verificar identidad/subject/builder según política aprobada. No se atribuye nivel SLSA.
- [ ] Aprobar y probar verificación antes del despliegue; el renderer de manifest solo valida formato.
- [ ] Aprobar creación/primer inicio de trustforge-dev y comprobar rootless, mounts, checkout, persistencia, red y SELinux reales, sin tocar otros workspaces.
- [ ] Documentar repetición por digest y límites de reconstrucción: repos RPM e inicialización aún móviles; inventario no es snapshot ni prueba de igualdad.
- [ ] Probar rollback limitado a recursos nuevos y realizar revisión final; no cerrar #3 por completar documentación.

## Despliegue, impacto y rollback
El [procedimiento canónico](https://github.com/jnbntc/distrobox-stack/tree/44851ec911ebc0eabba88eb18c53cb4849229754/workspaces/trustforge-dev/README.md) contiene el orden de aprobaciones, creación de manifest individual, verificación y rollback.
El nuevo workflow es manual, main-only y publish=false por defecto. No se incluye en el manifest, scripts o matrices masivos; integrar PRs no autoriza dispatch, publicación ni creación.
Impacto futuro: almacenamiento rootless ya configurado, imagen/cachés/capa escribible, HOME dedicado y checkout persistente. No se promete un consumo de disco sin medir. Distrobox integra más recursos que el bind explícito y puede escribir en ellos.
Rollback: retirar solo el nuevo contenedor, conservar checkout y evidencia, revisar HOME/cachés nuevos; no prune/reset, no borrar graphroot, no limpiar imágenes compartidas ni recrear el stack completo.

## Actualización de versiones
Cambiar primero la fuente canónica en distrobox-stack mediante PR, revisar digests/locks y pruebas, y actualizar esta referencia al commit aceptado. Si una nueva versión altera compatibilidad, privilegios o límites de confianza, proponer ADR antes del despliegue. No copiar la definición al repositorio consumidor.
