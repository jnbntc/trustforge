# ADR-013 — Entorno gestionado por distrobox-stack

Fecha: 2026-10-27.
Estado: PROPUESTO; requiere revisión arquitectónica. No reemplaza silenciosamente los ADR-002/003/009/012.
Solicitud: integración declarativa de TF-003 con el repositorio existente del usuario.

## Contexto
El entorno dedicado ya está acordado, pero duplicar Containerfile/manifest/locks en TrustForge generaría dos fuentes de verdad.
distrobox-stack contiene gestión y publicación OCI de otros workspaces, con operaciones masivas y tags latest. La incorporación no debe alterar esos workspaces ni activar sus publicaciones.

## Propuesta
Definición única y optativa bajo workspaces/trustforge-dev en distrobox-stack; TrustForge mantiene requisitos de consumo, criterios de prueba y referencias al commit revisado. Un workflow nuevo exclusivamente manual construye/publica solo el candidato nuevo cuando se autorice. No cambia el publicador, orquestador o manifest existente.
Se fija plataforma linux/amd64, base por digest, uv/Python y herramientas en un contrato/lock; los RPM/inicialización móviles se declaran como límite.

## Alternativas y consecuencias
Copiar la definición en ambos repositorios se descarta por divergencia.
Agregarla al manifest/matriz masivos se descarta en esta propuesta por el alcance sobre workspaces existentes.
Usar Podman genérico u otro mecanismo de aislamiento sería una decisión nueva; no se implementa ni se presenta como sustituto validado.

## Seguridad y decisión pendiente
Distrobox 1.8.2.5 añade privileged/label=disable y comparte HOME/runtime. unshare_all y rootless no eliminan esa integración. No se puede aceptar una garantía de «sin privilegios/sockets heredados» mediante el manifest solamente.
La revisión debe resolver si se acepta explícitamente esa integración para desarrollo confiable o se solicita otro diseño/configuración/versionado. Hasta entonces, despliegue bloqueado.
SBOM, Cosign, provenance y gate de verificación permanecen pendientes; no aprobar identidades/raíces por inferencia ni atribuir SLSA sin evidencia.

## Evidencia y estado
Ver [contrato consumidor](../DEVELOPMENT_ENVIRONMENT.md) y [PR canónica](https://github.com/jnbntc/distrobox-stack/pull/18).
Solo metadatos/validación estática. Sin build, publicación, creación ni pruebas reales de compatibilidad/reproducibilidad. TF-003 abierta.
