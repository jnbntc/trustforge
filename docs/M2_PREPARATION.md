# M2 — preparación del siguiente sprint, sin implementación

Preparado el 2026-10-29 conforme a ADR-003/005/006/008 y la experiencia del bootstrap independiente. No añade Cosign a la CLI, Gate M3, firmas, imágenes ni workflows nuevos. TF-003 no debe depender circularmente de M2/M3.

## Conceptos que debemos demostrar

- Referrers descubre descriptores declarados por un registro. El descubrimiento, incluso con hashes correctos, no autentica la asociación ni al publicador. Cosign verifica evidencia firmada conforme a una política de confianza; no sustituirlo por parsing de JSON.
- La firma dedicada de imagen vincula un digest a un firmante autorizado; no puede sustituirse por una atestación SBOM o provenance. En el bootstrap fijado, el statement sign/v1 y la anotación firmada de repositorio distinguen ese rol. M2 deberá definir y revisar su propio contrato antes de implementar.
- Una SBOM describe componentes declarados: autenticarla no prueba cobertura perfecta ni ausencia de vulnerabilidades. Provenance describe source/builder/invocación/materiales; la custom del bootstrap es una afirmación autenticada del workflow, sin builder independiente ni nivel SLSA demostrado.
- Keyless requiere cadena de certificados/TrustedRoot aprobada e issuer/SAN exactos. La identidad de workflow incorpora repositorio, ruta y ref; el source/workflow SHA, trigger y parámetros también se restringen. Un workflow autorizado comprometido sigue siendo un riesgo.
- Transparency log aporta evidencia de registro/inclusión bajo sus raíces y verificaciones; no avala que el software sea seguro, ni su contenido ni una autorización de despliegue. Conservar verificación de tlog/SCT y no introducir bypasses.
- Digest identifica bytes: índice, manifest hijo, archivo OCI y bundle tienen digests diferentes. Firmar/atestar/verificar el artefacto final publicado y consumir exactamente ese mismo digest; no volver a resolver un tag durante promoción.
- El futuro Gate M3 recibirá exclusivamente claims autenticados y normalizados y aplicará DENY por defecto para identidad/issuer/origen/builder/materiales/evidencias ausentes o no autorizados. Un resultado criptográfico válido seguirá separado de autorización humana para ejecutar/desplegar.

Referencias primarias ya utilizadas: [Cosign 3.1.4](https://github.com/sigstore/cosign/tree/v3.1.4), [contrato revisado del bootstrap](https://github.com/jnbntc/distrobox-stack/blob/541115eecce9e72bd4989ad5ac1c28f14a1a0c59/workspaces/trustforge-dev/COSIGN_INTERFACE.md), [OCI Distribution Referrers](https://github.com/opencontainers/distribution-spec/blob/v1.1.1/spec.md#listing-referrers). Las pruebas con mocks no demuestran criptografía ni interoperabilidad real.

## Primera issue propuesta: TF-201 / #11

Recomendación para el siguiente sprint, después de decisión de alcance: una aplicación inocua mínima con salida determinista y tests, dependencias fijadas y receta rootless pequeña. Reutilizar el proyecto Python existente; no introducir servicios/frameworks ni duplicar el workspace de distrobox-stack. Separar en su revisión código/receta, autorización de build y aceptación del resultado. Este documento no comienza ese trabajo.

Dependencias: aceptación humana de los pendientes M1, corrección #41 integrada en 07b1eafa6879c17750bbb5e8a604d67db912837e, gobernanza efectiva, plataforma/entradas/criterio de reproducibilidad acordados y autorizaciones operativas separadas. No exigir que el descubridor M1 haga verificación criptográfica para aceptarlo.

Después se abordarán TF-202–205 en sus issues: publisher de privilegios mínimos, identidad keyless exacta, SBOM y provenance. Definir raíces y contrato de evidencias antes de ejecutar; no aprobarlos en nombre del propietario.

## Evidencia mínima futura

1. Tests de app/receta y construcción autorizada; inventario de entradas móviles y distinción entre repetición por digest y reproducibilidad de build.
2. Digest final capturado y tres roles independientes autenticados; política, binario y raíces por canales independientes aprobados.
3. Negativos reales, cuando se autoricen: digest alterado, otro repositorio, firma dedicada ausente, atestación como firma, signer/issuer/workflow/ref/source incorrectos, evidencia ausente/malformada/duplicada y fallo de cada verificación.
4. Fallos de transporte/referrers/formato/transparencia deben bloquear, sin desactivar controles. El mock prueba contratos; la prueba real debe usar artefactos autorizados publicados por digest.
5. Reporte con herramientas/raíces/política/source/digest/run, resultados y límites; ninguna decisión VERIFIED/ALLOW concede por sí sola despliegue.
