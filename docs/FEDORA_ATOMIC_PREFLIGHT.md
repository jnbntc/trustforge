# TF-003 — Auditoría inicial de Fedora Atomic, solo lectura

Issue: [TF-003 / #3](https://github.com/jnbntc/trustforge/issues/3). Primera tarea operativa de M0.
Estado de este documento: instrucciones preparadas; auditoría NO ejecutada.
No cierra TF-003: la creación reproducible de Distrobox y la validación funcional quedan pendientes.

## Objetivo y límites
Actualización TF-003: el usuario aportó datos del preflight para planificar la [integración con distrobox-stack](DEVELOPMENT_ENVIRONMENT.md). Esta guía sigue siendo solo la fase A de lectura; no habilita build, publicación, inicialización ni creación. La definición canónica propuesta y las aprobaciones pendientes están en el contrato consumidor; no repetir la instalación dentro de este repositorio.

Fase A: identificar el Fedora real y reunir prerrequisitos estáticos para proponer un entorno `trustforge-dev`.
Fase B: crear y validar ese entorno únicamente después de aprobar un plan concreto.
La aprobación del repositorio, esta guía o una PR de documentación no autoriza la fase B.

Trabajar como usuario habitual, sin sudo. Si falta una herramienta, registrar «no disponible» y continuar con las consultas independientes; no instalarla. No ejecutar automáticamente el bootstrap de GitHub.
No usar servicios remotos, SSH, acceso a credenciales ni consultas de red durante la fase A.

Antes de consultar el host, confirmar que la terminal corresponde al Fedora del usuario. Una sesión de Codex puede estar dentro de un contenedor o ejecutor distinto. Si no se puede confirmar el contexto, detener las consultas dependientes y entregar la lista de comprobaciones pendientes. No usar `distrobox-host-exec`, montajes ni escape de contenedor para sortear ese límite.

La intención es no modificar configuración ni estado del runtime. Las lecturas pueden producir registros normales del sistema o actualizar tiempos de acceso; no prometemos ausencia de toda escritura incidental del sistema operativo.

## Comandos permitidos de la fase A
Son bloques de instrucciones para revisar y ejecutar uno por uno, no un instalador.
Registrar comando, salida, código de retorno e interpretación. Un error no autoriza reparación.

### A1. Contexto de ejecución
```bash
id -u
systemd-detect-virt --container
test -e /run/.containerenv
test -e /.dockerenv
```

`test` retorna 0 si existe el indicador y 1 si no existe, sin imprimir salida.
`systemd-detect-virt --container` puede retornar un código distinto de cero al no detectar contenedor. Eso no prueba por sí solo que sea el host: contrastar con el contexto conocido de la terminal.
Si hay indicios de contenedor, no continuar como si fuese evidencia del host.

### A2. Sistema operativo
```bash
cat /etc/os-release
uname -r -m
test -e /run/ostree-booted
```

Registrar edición, versión, arquitectura y kernel sin ejecutar los valores de os-release como código.
El indicador OSTree es una pista de arranque, no prueba suficiente de edición ni de compatibilidad de toda la toolchain.
No ejecutar actualizaciones, rebase, rollback, layering ni consultas que activen innecesariamente servicios.

### A3. Herramientas ya disponibles
```bash
for tool in podman distrobox rpm-ostree git python3 uv newuidmap newgidmap pasta slirp4netns fuse-overlayfs getenforce; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf '%s: disponible\n' "$tool"
  else
    printf '%s: no disponible\n' "$tool"
  fi
done
```

Ejecutar cada consulta de versión solo cuando la herramienta exista:
```bash
podman --version
distrobox --version
rpm-ostree --version
git --version
python3 --version
uv --version
```

La disponibilidad no prueba funcionamiento ni compatibilidad.
No usar en esta fase `podman info`, `podman ps`, `podman images`, `podman unshare`, `distrobox list` ni `distrobox enter`: esta auditoría conservadora evita consultas que entren al runtime y puedan inicializar almacenamiento, crear namespaces o iniciar contenedores.
No conectar a sockets de Podman/Docker ni a motores remotos.

### A4. SELinux, cgroups y namespaces
```bash
getenforce
cat /sys/fs/cgroup/cgroup.controllers
cat /proc/sys/user/max_user_namespaces
```

Si no existe un archivo/comando, registrar el límite. La presencia de controladores no prueba delegación al usuario; un valor positivo de namespaces no prueba que un contenedor pueda ejecutarse. No cambiar SELinux ni parámetros del kernel.

Consultar solo los rangos de subidentificadores del usuario actual, sin volcar las tablas completas:
```bash
for table in /etc/subuid /etc/subgid; do
  if test -r "$table"; then
    printf '%s: ' "$table"
    awk -F: -v account="$(id -un)" -v uid="$(id -u)" '
      $1 == account || $1 == uid { ranges++; total += $3 }
      END { printf "matching_ranges=%d allocated_ids=%d\n", ranges, total }
    ' "$table"
  else
    printf '%s: no legible o ausente\n' "$table"
  fi
done
```

Registrar conteo y tamaño total, sin nombres ni identificadores de otros usuarios. Estos archivos son una comprobación parcial: otros mecanismos de asignación pueden existir. No ejecutar `usermod`, `newuidmap` ni `newgidmap`.

### A5. Capacidad y señales de configuración existente
```bash
df -h / "$HOME"
df -i / "$HOME"
free -h
findmnt -n -o FSTYPE -T "$HOME"
```

Mantener salidas con rutas/dispositivos en el informe privado. No fijar un mínimo universal: estimar espacio para imagen base, dependencias, cachés y pruebas en el plan posterior.

Para detectar únicamente presencia de configuración propia y almacenamiento en la ruta por defecto:
```bash
test -e "${XDG_CONFIG_HOME:-$HOME/.config}/containers/storage.conf"
test -e "${XDG_CONFIG_HOME:-$HOME/.config}/containers/containers.conf"
test -d "${XDG_DATA_HOME:-$HOME/.local/share}/containers/storage"
```

La ausencia no descarta configuración global ni rutas personalizadas. No leer auth.json, conexiones remotas, claves, variables de entorno completas, historiales ni configuraciones de registro privadas. No listar contenedores, imágenes o volúmenes. La existencia de `trustforge-dev` queda sin verificar hasta una consulta al runtime autorizada.

## Fuera de alcance de la fase A
- Instalación de paquetes en host o HOME; `dnf`, `rpm-ostree install`, instaladores descargados o `uv sync`.
- Pull, build, run, create, start, enter, login, prune, reset o migrate de cualquier motor.
- Pruebas funcionales de red o puertos, registro local, cambios de firewall/DNS/rutas, servicios o permisos.
- Modificación de SELinux, subuid/subgid, almacenamiento o configuración de contenedores.
- KVM/libvirt/bootc, máquinas virtuales o comprobaciones que los activen: se retoman antes de M5.
- Cambios de identidad de firma, raíces de confianza, políticas, CI de publicación o permisos de GitHub.
- Subir evidencia cruda a issues, PRs, commits o artefactos públicos.

## Entrega y aceptación de esta primera fase
Guardar evidencia privada fuera del repositorio versionado, en una ubicación local acordada. Si la sesión no dispone de una ubicación privada, no crear un volcado masivo: informar el límite y conservar únicamente resultados revisados y mínimos.
Cada comprobación debe distinguir: observado, no disponible, falló o no verificado. No reemplazar fallos por resultados esperados.

El resumen público permitido, tras revisar y redactar los datos, contiene solo: edición/versión de Fedora, arquitectura, versiones de herramientas, estado SELinux, señales de cgroups/namespaces, suficiencia aproximada de almacenamiento y bloqueos genéricos. Excluir nombres de usuario/host, IP/MAC, rutas personales, UUID, registros/imágenes privados, tokens y salidas completas. La guía no autoriza publicar automáticamente el informe del host.

Matriz mínima de entrega:

| Área | Evidencia esperada | Límite que debe quedar explícito |
|---|---|---|
| Host y Atomic | os-release, kernel, contexto e indicador OSTree | No confundir ejecutor con host |
| Herramientas | Disponible/ausente y versiones consultadas | No instalar para completar el informe |
| Rootless | Usuario no root, rangos propios, helpers, namespaces | No probado funcionalmente |
| SELinux/cgroups | Estado y controladores visibles | Delegación y ejecución no probadas |
| Almacenamiento | Capacidad aproximada y tipo de FS | Driver y ruta efectiva del runtime no verificados |
| Red | No verificada en esta fase | Sin pull, registro ni conectividad funcional |
| Distrobox | Nombre propuesto trustforge-dev | Existencia/creación y compatibilidad pendientes |

## Plan concreto requerido antes de la fase B
Presentar imagen base Fedora soportada con referencia y digest verificables, mecanismo para obtener y validar ese digest, versiones propuestas y compatibilidad con Python 3.13 (aún propuesta), ubicación de HOME/cachés y uso del Podman del host frente a anidamiento. No inventar digest ni pins.
Explicar la integración con HOME, accesos y efectos sobre archivos, espacio/red necesarios, y qué paquetes se instalarían dentro del contenedor.
Indicar consultas previas para detectar colisiones con `trustforge-dev`, sin borrar ni reutilizar un entorno existente a ciegas.
Proponer pruebas funcionales rootless, red y registro local, comandos exactos de creación y limpieza limitada a recursos nuevos e identificados, y criterios para detenerse.
Solicitar aprobación de ese plan antes de cualquier pull, creación, inicio, instalación o modificación. Distrobox comparte recursos con el host; no es una frontera de seguridad.

TF-003 solo podrá completarse después de la fase B aprobada, validación real de reproducibilidad y revisión de la PR. Esta fase A entrega un diagnóstico parcial y un plan, no un entorno listo.

## Fuentes oficiales consultadas
- [Podman: opciones, modo rootless y almacenamiento](https://docs.podman.io/en/latest/markdown/podman.1.html)
- [Tutorial rootless del proyecto Podman](https://github.com/podman-container-tools/podman/blob/main/docs/tutorials/rootless_tutorial.md)
- [Distrobox: integración con el host y consideraciones de seguridad](https://distrobox.it/)

Las fuentes explican capacidades y límites; no prueban que este host cumpla los prerrequisitos. Revalidar compatibilidad y versiones durante TF-003.
