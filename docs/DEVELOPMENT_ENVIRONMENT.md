# TF-003 — Contrato consumidor de trustforge-dev

Estado: propuesta corregida para nueva revisión; sin build, publicación, firma real ni despliegue.
Issue: [TF-003 / #3](https://github.com/jnbntc/trustforge/issues/3).
Fuente única: [distrobox-stack PR #18](https://github.com/jnbntc/distrobox-stack/pull/18), [snapshot canónico](https://github.com/jnbntc/distrobox-stack/tree/2998e59790416c491d65fced798554a97c3e3b02/workspaces/trustforge-dev), commit `2998e59790416c491d65fced798554a97c3e3b02`.
Decisión: [ADR-013 corregido](adr/013-distrobox-stack-workspace.md).

## Uso y responsabilidades
trustforge-dev es un workspace de **desarrollo confiable**, no un sandbox de seguridad. Se utiliza para código y pruebas confiables; M4 no ejecutará artefactos adversarios en este entorno.
distrobox-stack conserva Containerfile, manifest, toolchain/locks, workflows y bootstrap independiente. Este repositorio solo define requisitos de consumo y aceptación; no duplica esas definiciones ni importa Gate M3 para aceptar el primer entorno.

Plataforma inicial linux/amd64 y Podman rootless. Fedora Toolbox 44/uv por los digests ya comprobados, Python 3.13.18 gestionado y herramientas/lock según [contract.json](https://github.com/jnbntc/distrobox-stack/tree/2998e59790416c491d65fced798554a97c3e3b02/workspaces/trustforge-dev/contract.json).
No sustituir Python del host ni /usr/bin/python3. Dependencias de la aplicación se fijarán en TF-004, sin confundirlas con el venv de herramientas.
HOME/cachés dedicados y checkout explícito ~/Proyectos/trustforge -> /workspace/trustforge:rw, conforme a la fuente única. Sin cambio de graphroot/storage.conf, políticas SELinux, servicios, workspaces o pipelines existentes.

## Modelo de seguridad delimitado
Distrobox 1.8.2.5 añade --privileged y label=disable dentro del contexto rootless. HOME original y /run/user pueden seguir compartidos, con visibilidad potencial de sockets del usuario.
Rootless limita privilegios respecto del host; no elimina permisos/montajes heredados ni garantiza confinamiento SELinux. El host puede seguir Enforcing mientras las etiquetas del contenedor están desactivadas.
La revisión acepta esa integración para desarrollo confiable. Flags/mounts/sockets efectivos requieren prueba autorizada posterior; no se ha creado un contenedor para medirlos.
M4 tendrá frontera y aceptación propias: runtime restringido explícitamente para bajo riesgo o VM desechable si el riesgo exige ese aislamiento. No se implementa M4 ni se reutiliza el workspace como sandbox.

## Bootstrap de confianza independiente de M3
Usar el [procedimiento canónico exacto](https://github.com/jnbntc/distrobox-stack/tree/2998e59790416c491d65fced798554a97c3e3b02/workspaces/trustforge-dev/BOOTSTRAP.md) desde código revisado y fijado por commit, fuera de la imagen a aceptar.
El adaptador provisional delega criptografía a Cosign fijado e independiente. Comprueba firma por identidad/issuer/workflow/source exactos, raíces aprobadas, digest final, atestaciones autenticadas del mismo subject, SBOM, provenance y parámetros/materiales esperados.
La política de ejemplo sigue sin aprobar, sin source commit ni raíz inventados. El operador aporta una política externa revisada y anclas independientes; no acepta archivos suministrados por la imagen como prueba de sí mismos.
Cosign/acciones y Syft están fijados en el contrato canónico; el futuro publisher genera SBOM y provenance custom y los atesta por digest. No se atribuye nivel SLSA ni evidencia de builder independiente.
VERIFIED solo informa verificación bajo esas anclas; no autoriza despliegue. La aprobación humana de creación/primer inicio debe ser posterior, nueva y para el mismo digest. El renderer de manifest no es un verificador.

## Criterios de aceptación de TF-003
- [x] Definición única optativa; pins base/uv/Python y lock con hashes conservados.
- [x] Modelo de desarrollo confiable y frontera M4 independiente documentados en ADR-013.
- [x] Bootstrap sin dependencia circular con Gate; código/política/workflow preparados, denegación por defecto y tests con fixtures.
- [x] Validación específica de Containerfile, JSON/INI, scripts, locks, workflows y bootstrap en CI de PR, sin build/publicación ni expansión a nueve imágenes.
- [ ] Nueva revisión de ambas PRs y aceptación documental de ADR-013.
- [ ] Aprobar anclas, identidad/issuer/workflow/source commit, entorno protegido y permisos de publicación/firma.
- [ ] Autorizar por separado build, publicación/firma y verificación real; generar digest y evidencias auténticas.
- [ ] Probar fallos reales de firma/identidad/issuer/subject/source, compatibilidad de Cosign/GHCR/referrers y consistencia del output.
- [ ] Aprobar despliegue y probar mounts/flags/sockets, rootless, herramientas, checkout/persistencia, red y efectos SELinux.
- [ ] Documentar repetición de despliegue por digest y evaluar reproducibilidad de build con RPM/inicialización móviles, no solo inventario.
- [ ] Validar rollback limitado a recursos nuevos y revisar cierre; no cerrar #3 por estas correcciones estáticas.

## Validación e impactos
Datos del host aportados por el usuario; este ejecutor no realizó una nueva auditoría del host ni publicó salidas completas.
Las fixtures simulan respuestas de Cosign para probar parsers/controles; no son certificados, firmas o evidencia criptográfica real.
El nuevo CI de PR es específico y solo ejecuta validaciones estáticas/offline con biblioteca estándar. Build/publicación/firma siguen en workflow_dispatch main-only; no se ejecutaron. Los cuatro pipelines anteriores, manifests/orquestación y workspaces existentes conservan sus fuentes.
Impacto futuro: imagen/capa/cachés en almacenamiento rootless existente, HOME dedicado y escrituras del checkout y otros recursos integrados por Distrobox. Tamaño efectivo y runtime no probados.
Rollback canónico: solo el nuevo contenedor y recursos identificados como nuevos; conservar checkout/evidencia, revisar HOME/cachés, no prune/reset, borrar graphroot ni recrear el stack.

## Garantías pendientes
Digest comprueba integridad, firma/identidad autenticidad, provenance describe origen/build autenticados bajo el modelo aprobado, repetir por digest consume el mismo artefacto y reconstruir exige controlar entradas móviles. No son equivalentes.
RPM e inicialización no están fijados por un snapshot; inventario no demuestra rebuild idéntico. SBOM/firma/provenance reales, herramientas ejecutadas y reproducibilidad siguen pendientes de ejecución autorizada.
