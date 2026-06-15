# Ticketera Ciberseguridad y Networking - v1.0.0.20

Versión casi productiva de la plataforma de gestión de tickets para Ciberseguridad y Networking.

## Incluye

- Frontend React compilado y servido con Nginx.
- Backend FastAPI.
- PostgreSQL 16.
- Roles y permisos por módulo.
- Usuarios, SLA, casos de uso, preguntas requeridas, áreas corporativas y auditoría.
- Tickets con comentarios, notas internas y evidencias por comentario.
- Descarga segura de adjuntos mediante API autenticada.
- Dashboard con filtros por rango de fechas.
- Exportación de reportes en PDF, Excel y CSV.
- SMTP configurable para notificaciones.
- Scripts de backup y restore.
- Estructura base para Alembic.
- Variables centralizadas en `.env`.




## Cambios destacados v1.0.0.20

### v1.0.0.20 - Indicadores de tiempo del ticket

- Se agrega indicador de vida total del ticket desde creación hasta resolución/cierre.
- Se agrega indicador de SLA transcurrido, descontando tiempo pausado registrado.
- El detalle del ticket muestra tarjetas de tiempo operativo, SLA transcurrido y fin de medición.
- La bandeja de tickets muestra columna "Tiempo del ticket".
- El Kanban muestra tiempo transcurrido y SLA transcurrido por tarjeta.
- Los indicadores se actualizan automáticamente cada minuto en tickets abiertos.


- SLA avanzado con cálculo de consumo en tiempo real.
- Indicadores de SLA 75%, 90%, pausado, vencido y cumplido.
- Control de primera respuesta con vencimiento independiente.
- Dashboard con KPIs de SLA avanzado.
- Detalle de ticket con barra de progreso SLA, política aplicada y tiempo restante.
- Kanban con indicador visual de estado SLA por tarjeta.
- Notificaciones internas para SLA 75%, 90%, vencido y primera respuesta vencida.

## Cambios destacados v1.0.0.18

- Corrección visual del panel de notificaciones en modo claro/oscuro.
- La campana y su panel ahora quedan por encima de dashboards, tarjetas KPI y módulos de contenido.
- Se ajustó el `z-index` de la barra superior y del panel de notificaciones.
- Se limitó la altura del panel según el alto de la pantalla para evitar que se mezcle visualmente con el contenido inferior.


## v1.0.0.25 - Validación final y corrección de hardening

Esta versión corrige el arranque del backend después del hardening avanzado, especialmente el identificador público seguro de adjuntos (`TicketAttachment.public_id`).

## v1.0.0.24 - Hardening avanzado OWASP/CWE

Esta versión refuerza la plataforma con controles defensivos orientados a una ticketera de ciberseguridad:

- Identificadores públicos no secuenciales para usuarios, tickets, comentarios y adjuntos.
- Compatibilidad temporal con identificadores antiguos, pero el frontend usa referencias públicas.
- Validación anti-IDOR/BOLA en tickets, usuarios y adjuntos.
- Servicio centralizado de autorización por objeto.
- Auditoría de accesos denegados, descargas de evidencias, cambios de perfil y autenticación.
- Hash SHA-256 para evidencias nuevas.
- Validación de extensiones, tamaño, nombre seguro y detección básica de contenido activo en evidencias.
- Cabeceras HTTP de seguridad configurables por `.env`.
- Schemas críticos con bloqueo de campos inesperados para mitigar mass assignment.
- Checklist OWASP/CWE agregado en `docs/HARDENING_OWASP_CWE.md`.

## Cambios destacados v1.0.0.17

- Se agregó centro de notificaciones internas con campana en la barra superior.
- Se agregaron notificaciones por ticket asignado, comentario, cambio de estado, resuelto, cerrado y SLA.
- Se agregó contador de notificaciones no leídas.
- Se agregó marcado individual y masivo como leído.
- Las notificaciones de tickets permiten abrir directamente el detalle asociado.
- Se agregó el módulo `notifications` al sistema de roles y permisos.

## Cambios destacados v1.0.0.15

- Validación visual y backend de campos obligatorios en Nuevo Ticket.
- Validación obligatoria de preguntas requeridas por matriz antes de crear el ticket.
- Permisos de tickets más estrictos para roles personalizados.
- Detalle de ticket más profesional con línea de progreso, bloque de SLA y gestión operacional con motivo.
- Auditoría con filtros por usuario, acción, entidad, ID y rango de fechas.

## Inicio rápido

1. Copia el archivo de variables:

```bash
cp .env.example .env
```

2. Edita `.env` y cambia al menos:

```env
SECRET_KEY=CAMBIAR_POR_UN_SECRETO_LARGO_ALEATORIO
POSTGRES_PASSWORD=CAMBIAR_PASSWORD_POSTGRES
DATABASE_URL=postgresql+psycopg2://ticketera:CAMBIAR_PASSWORD_POSTGRES@postgres:5432/ticketera
```

3. Levanta la plataforma:

```bash
docker compose up --build -d
```

4. Accede a:

```text
http://localhost:8080
```

API directa:

```text
http://localhost:8000/docs
```

## Usuarios iniciales

| Rol | Usuario | Contraseña |
|---|---|---|
| Administrador | admin@ticketera.cl | Admin123! |
| Analista Ciberseguridad | analyst.cyber@ticketera.cl | Analyst123! |
| Analista Networking | analyst.net@ticketera.cl | Analyst123! |
| Solicitante | user@ticketera.cl | User123! |

Cambia estas contraseñas después del primer inicio.

## Modo desarrollo

```bash
docker compose -f docker-compose.dev.yml up --build
```

Frontend dev:

```text
http://localhost:5173
```

Backend:

```text
http://localhost:8000
```

## Backups

Generar backup:

```bash
./scripts/backup.sh
```

Restaurar backup:

```bash
./scripts/restore.sh ./backups/ticketera-backup-YYYYMMDD-HHMMSS.tar.gz
```

## Reportes

Desde el dashboard, usuarios administradores, supervisores y analistas pueden exportar:

- PDF.
- Excel.
- CSV.

Los reportes respetan el rango de fechas seleccionado.

## Seguridad aplicada en v10

- PostgreSQL como base de datos productiva.
- Descarga autenticada de adjuntos.
- Validación de extensiones permitidas y bloqueadas.
- Límite de tamaño de archivos por `.env`.
- SMTP no bloqueante: si falla, el ticket sigue funcionando.
- Usuarios eliminados con eliminación lógica.
- Auditoría de acciones críticas.
- Configuración sensible separada en `.env`.
- Reverse proxy Nginx para frontend y API.

## Siguiente paso recomendado

Para producción real:

1. Usar dominio real y HTTPS con Nginx, Traefik o proxy corporativo.
2. Configurar SMTP corporativo.
3. Cambiar contraseñas iniciales.
4. Revisar roles y permisos finales.
5. Programar backups automáticos con cron.
6. Configurar monitoreo de contenedores y disco.



## Versión v1.0.0.15

### Hotfix de arranque con bases existentes

- Corrige el error `MultipleResultsFound` durante el `seed` de categorías.
- Permite actualizar desde versiones anteriores sin borrar el volumen de PostgreSQL.
- El catálogo dinámico ahora valida existencia del marcador con `LIMIT 1` en lugar de esperar una única fila.
- Recomendado para instalaciones que ya tenían categorías cargadas en la base.

## Versión v1.0.0.14

Estabilización operativa, validaciones y permisos.

- Se agregaron validaciones visuales y backend para Nuevo Ticket.
- Las preguntas requeridas por matriz ahora son obligatorias antes de crear el ticket.
- Se endurecieron permisos para roles personalizados en tickets.
- Se mejoró el detalle del ticket con progreso, SLA, resumen ejecutivo y gestión con motivo.
- La auditoría permite filtrar por usuario, acción, entidad, ID y rango de fechas.

## Versión v1.0.0.13

Corrección visual del modo oscuro en el formulario Nuevo Ticket.

- Se corrigió el bloque "Información requerida según matriz" para que use variables de tema.
- Se eliminaron fondos claros hardcodeados en secciones dinámicas y tarjetas administrativas.
- Se agregaron estilos específicos para inputs, textarea y select en modo oscuro.
- Se mantiene consistencia visual entre el formulario, dashboards y módulos administrativos.

## Versión v1.0.0.12

Esta versión optimiza el build Docker para reducir el tiempo en la etapa del frontend:

```text
[frontend build] RUN npm install
```

Cambios aplicados:

- Reemplazo de `npm install` por `npm ci`.
- Etapa `deps` separada para cachear dependencias.
- Cache mount de BuildKit para npm.
- Mejora de `.dockerignore` del frontend.
- Cache mount de pip para backend.
- Scripts `scripts/rebuild-fast.sh` y `scripts/rebuild-clean.sh`.

Comando recomendado:

```bash
./scripts/rebuild-fast.sh
```

Evita usar `--no-cache` salvo que sea necesario, porque hace que Docker descargue dependencias nuevamente.


## Build recomendado desde v1.0.0.12

Para ejecución normal o actualización sin borrar datos:

```bash
sudo docker compose down
sudo docker compose up --build -d
```

Evita usar `--no-cache` en cada despliegue porque fuerza la instalación completa de dependencias del frontend y backend.

Si `npm ci` falla con `Exit handler never called`, esta versión ya usa Node 20 LTS y registry público de npm para evitar ese problema.


## v1.0.0.17 - Notificaciones internas

Esta versión agrega un centro interno de notificaciones con campana en la barra superior.

Incluye:

- Notificaciones por ticket asignado.
- Notificaciones por nuevo comentario.
- Notificaciones por cambio de estado.
- Notificaciones por ticket resuelto o cerrado.
- Alertas internas de SLA próximo a vencer o vencido al consultar la campana.
- Marcar notificación individual como leída.
- Marcar todas como leídas.
- Acceso directo al detalle del ticket desde la notificación.


## v1.0.0.23 - Horario oficial del sistema

La plataforma usa por defecto la zona horaria de Chile continental:

```env
APP_TIMEZONE=America/Santiago
```

Esta variable controla:

- Hora por defecto del formulario Nuevo Ticket.
- Cálculo de SLA en horario laboral.
- Visualización de fechas en frontend.
- Zona horaria del backend y PostgreSQL en Docker.

El sistema conserva los timestamps de base de datos en UTC para evitar inconsistencias, pero calcula y muestra la operación según `APP_TIMEZONE`.


## Hardening de seguridad v1.0.0.23

Esta versión agrega controles de seguridad configurables para operación casi productiva:

- Política de contraseña fuerte.
- Rate limit en login.
- Mensajes de bloqueo temporal por intentos fallidos.
- Auditoría de descargas de evidencias.

Variables nuevas en `.env`:

```env
PASSWORD_MIN_LENGTH=10
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBER=true
PASSWORD_REQUIRE_SPECIAL=true
LOGIN_RATE_LIMIT_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW_SECONDS=300
```
# Ticketera_Ciberseguridad
# Ticketera_Ciberseguridad
# Ticketera_Ciberseguridad
