# ADR-013 — Workspace confiable y bootstrap independiente en distrobox-stack

Fecha: 2026-10-27.
Estado: INTEGRADA como decisión de desarrollo confiable mediante stack #18 (541115eecce9e72bd4989ad5ac1c28f14a1a0c59) y TrustForge #30 (da596a15dfc107b358b662b02a8ac228396ac69e), squash confirmado el 28-10-2026. La implementación operativa sigue pendiente.
La revisión arquitectónica del usuario acepta conservar Distrobox **para desarrollo confiable** con los límites siguientes. La aceptación de ese alcance no autoriza merge, build, publicación, firma ni despliegue.

## Decisión 1: fuente única y uso confiable
distrobox-stack define la imagen, toolchain, manifest individual, construcción/publicación y mecanismo provisional de verificación. TrustForge mantiene solamente el contrato consumidor y criterios de aceptación, con referencia al commit revisado.
trustforge-dev se usa exclusivamente para desarrollo y pruebas confiables. No es un sandbox ni se ejecutan en él artefactos adversarios no confiables.
Se conserva la integración optativa fuera del manifest, orquestador y pipelines de las nueve imágenes existentes.

## Rootless, privilegios y SELinux son límites distintos
Podman rootless ejecuta el contenedor bajo el usuario del host; no elimina los privilegios dentro de su user namespace.
Se inspeccionó el código upstream de Distrobox 1.8.2.5: inyecta --privileged y --security-opt label=disable, además de otros ajustes de integración. HOME original y /run/user pueden compartirse aunque se elija HOME dedicado; los sockets del usuario podrían resultar accesibles.
unshare_all no elimina todos esos efectos. SELinux Enforcing del host no equivale a confinamiento del contenedor por etiquetas cuando está label=disable.
No se modificó Distrobox ni se añadieron capacidades/dispositivos/sockets explícitos. La visibilidad efectiva de mounts/sockets del futuro contenedor se probará solo con autorización; la evidencia actual es de código fuente, no de inspección de un runtime creado.

## Decisión 2: frontera independiente para M4
El laboratorio adversario de M4 tendrá un mecanismo separado y criterios propios de aislamiento. Priorizar contenedores con restricciones explícitas para casos de bajo riesgo; usar VMs desechables cuando el riesgo y aislamiento exigido lo justifiquen.
No reutilizar trustforge-dev, su HOME o sus sockets/credenciales como sandbox adversario. No se implementa M4 ahora. Cualquier virtualización necesaria antes del hito general de bootc requerirá alcance/autorización específicos; no se activa KVM/libvirt por este ADR.

## Decisión 3: bootstrap sin dependencia circular de Gate M3
El entorno inicial no espera a TrustForge Gate. Se prepara un verificador independiente que delega criptografía a Cosign fijado en un entorno ya confiable, fuera de la imagen objetivo.
Exige imagen final por digest, identidad e issuer exactos, workflow/repository/ref/trigger/source SHA, raíces Sigstore independientes aprobadas, firma y atestaciones SBOM/provenance con el mismo subject/digest, origen y parámetros/materiales esperados.
Errores/evidencias ausentes o incoherentes se deniegan sin fallback. Ningún SHA-256 solo demuestra autenticidad. La política entregada no está aprobada y carece del source commit/raíz reales que debe aportar la revisión humana.
Un resultado VERIFIED no autoriza el despliegue: se requiere una autorización explícita nueva para ese digest. No se implementa la CLI/política de M3 dentro de este bootstrap provisional.

## Evidencias y garantías diferentes
Se preparan generación futura con herramientas/acciones oficiales fijadas y validación estática específica. No existen aún build, firma, SBOM, provenance ni verificación criptográfica reales de esta imagen.
La provenance custom es una declaración del workflow autenticada por Cosign si su firma futura tiene éxito; no es builder independiente ni nivel SLSA. Una firma válida no prueba que el builder o contenido sean seguros.
Los RPM y la inicialización Distrobox siguen móviles: inventario no equivale a snapshot. Integridad, autenticidad, provenance, repetición de consumo por digest y reproducibilidad de construcción se evalúan separadamente.

## Alternativas y revisión
Definiciones duplicadas se rechazan por divergencia. Incorporación a operaciones masivas se rechaza por el alcance sobre otros workspaces. Un runtime aislado queda reservado al diseño separado de M4, no como reemplazo silencioso del workspace confiable.
[Contrato consumidor](../DEVELOPMENT_ENVIRONMENT.md), [definición y bootstrap canónicos](https://github.com/jnbntc/distrobox-stack/tree/541115eecce9e72bd4989ad5ac1c28f14a1a0c59/workspaces/trustforge-dev) y comentarios de revisión en [PR #18](https://github.com/jnbntc/distrobox-stack/pull/18) / [PR #30](https://github.com/jnbntc/trustforge/pull/30).
TF-003 abierta; integración de fuente completada, sin autorización ni evidencia nueva de build, publicación o despliegue.
