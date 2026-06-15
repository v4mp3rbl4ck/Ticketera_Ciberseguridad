# Changelog

## v1.0.0.25 - Validación final / Corrección de arranque hardening

- Corregido error de inicio del backend en v1.0.0.24 por modelo `TicketAttachment` sin atributo `public_id`.
- Agregado `public_id` no secuencial al modelo de adjuntos para mantener consistencia anti-IDOR.
- Mejorado `assign_missing_public_ids()` para evitar caída del backend ante upgrades parciales de modelos.
- Versión orientada a validación final, corrección de bugs y preparación de producción sin nuevas funcionalidades grandes.

## v1.0.0.24 - Hardening avanzado OWASP/CWE

- Se agregaron identificadores públicos no secuenciales para usuarios, tickets, comentarios y adjuntos.
- Se mantiene el ID interno solo para relaciones de base de datos y se expone `public_id` en la API/UI.
- Se reforzaron controles anti-IDOR/BOLA en tickets, usuarios y adjuntos.
- Se agregó servicio centralizado de autorización por objeto.
- Se auditan accesos denegados y descargas de evidencias.
- Se agregaron hashes SHA-256 a evidencias nuevas.
- Se agregó validación liviana de contenido/MIME para archivos adjuntos y bloqueo de contenido activo.
- Se reforzaron cabeceras HTTP de seguridad: CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy.
- Se bloquearon campos inesperados en schemas críticos para reducir mass assignment.
- Se agregó documentación/checklist de validaciones OWASP/CWE para preparación de v1.0.0.25.


## v1.0.0.23 - Hardening de seguridad

- Agrega política configurable de contraseñas mediante variables de entorno.
- Aplica validación de contraseña fuerte en creación de usuarios, restablecimiento administrativo y cambio de contraseña desde perfil.
- Agrega rate limit en login por IP + usuario para reducir fuerza bruta contra cuentas locales.
- Mejora el mensaje de error de login para mostrar bloqueos temporales y respuestas del backend.
- Registra en auditoría la descarga de evidencias/adjuntos.
- Refuerza la documentación de variables de seguridad en `.env.example`.

## v1.0.0.22 - Reportería avanzada

- Agrega módulo lateral **Reportes** para administrador, supervisor y analista.
- Agrega filtros por rango de fechas, área técnica, área corporativa, severidad, estado y analista asignado.
- Agrega endpoint `/api/v1/reports/summary` con KPIs y distribuciones para previsualizar reportes.
- Mejora exportación PDF, Excel y CSV respetando filtros aplicados y zona horaria del sistema.
- Excel avanzado incluye hojas de resumen ejecutivo, distribuciones y tickets.
- PDF ejecutivo incluye filtros, KPIs, distribuciones, top áreas, top casos de uso y muestra de tickets.


## v1.0.0.21 - Configuración horaria Chile y SLA consistente

- Se agregó `APP_TIMEZONE=America/Santiago` como zona horaria oficial configurable.
- Docker Compose ahora aplica `TZ`/`PGTZ` para backend y PostgreSQL.
- El cálculo de SLA en horario laboral usa la zona horaria configurada, manteniendo almacenamiento UTC en la base de datos.
- Las fechas ingresadas desde `datetime-local` se interpretan como hora local de Chile y se guardan de forma consistente.
- El frontend ahora formatea fechas en la zona horaria configurada y evita desfases visuales.
- Se actualizó el formulario Nuevo Ticket para usar la hora actual de Chile por defecto.

# Changelog

## v1.0.0.24 - Hardening avanzado OWASP/CWE

- Se agregaron identificadores públicos no secuenciales para usuarios, tickets, comentarios y adjuntos.
- Se mantiene el ID interno solo para relaciones de base de datos y se expone `public_id` en la API/UI.
- Se reforzaron controles anti-IDOR/BOLA en tickets, usuarios y adjuntos.
- Se agregó servicio centralizado de autorización por objeto.
- Se auditan accesos denegados y descargas de evidencias.
- Se agregaron hashes SHA-256 a evidencias nuevas.
- Se agregó validación liviana de contenido/MIME para archivos adjuntos y bloqueo de contenido activo.
- Se reforzaron cabeceras HTTP de seguridad: CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy.
- Se bloquearon campos inesperados en schemas críticos para reducir mass assignment.
- Se agregó documentación/checklist de validaciones OWASP/CWE para preparación de v1.0.0.25.


## v1.0.0.20 - Indicadores de tiempo del ticket

- Agrega cálculo visual de vida del ticket desde creación hasta cierre/resolución o tiempo actual.
- Agrega cálculo visual de SLA transcurrido descontando pausas registradas.
- Agrega tarjetas de tiempo en el detalle del ticket.
- Agrega columna "Tiempo del ticket" en la bandeja de tickets.
- Agrega edad/SLA transcurrido en tarjetas Kanban.
- Agrega utilitario frontend reutilizable para duración y medición temporal.

## v1.0.0.19 - SLA avanzado

- Se agregó cálculo de SLA en tiempo real sin requerir nuevas columnas de base de datos.
- Se agregaron estados de SLA: activo, 75%, 90%, pausado, vencido, cumplido y vencido al cierre.
- Se agregó control de primera respuesta con vencimiento independiente.
- Se agregaron KPIs SLA al dashboard: cumplimiento, 75%, 90%, pausados y primera respuesta vencida.
- El detalle del ticket ahora muestra barra de progreso SLA, tiempo restante, política aplicada y tiempo pausado.
- El Kanban ahora muestra el estado SLA dentro de cada tarjeta.
- Las notificaciones internas generan alertas por 75%, 90%, vencimiento y primera respuesta vencida.

## v1.0.0.18 - Corrección visual de notificaciones

- Se corrige el panel de notificaciones para que no quede detrás ni mezclado con tarjetas del dashboard.
- Se eleva el `z-index` de la barra superior, la campana y el panel desplegable.
- Se ajusta la altura máxima del panel de notificaciones según el viewport.
- Se agrega ajuste responsive para pantallas pequeñas.

## v1.0.0.17 - Notificaciones internas

- Se agregó endpoint `/api/v1/notifications` para listar notificaciones del usuario autenticado.
- Se agregó contador de no leídas.
- Se agregó marcado individual y masivo como leído.
- Se agregó campana de notificaciones en la barra superior.
- Se enlazan notificaciones de ticket con el detalle del ticket.
- Se agregan alertas internas para SLA vencido y próximo a vencer.
- Se agregó el módulo `notifications` al sistema de roles/permisos.


## v1.0.0.16

- Nuevo módulo Kanban operativo.
- Vista por columnas para Nuevo, Asignado, En Progreso, En Espera, Resuelto y Cerrado.
- Filtros por búsqueda, severidad, área técnica, área corporativa, asignado y SLA vencido.
- Acciones rápidas para abrir detalle y avanzar el estado del ticket.
- Módulo `kanban` agregado a la matriz de roles/permisos.


## v1.0.0.15

- Corrige falla de arranque del backend por `sqlalchemy.exc.MultipleResultsFound` al detectar catálogo seeded en bases existentes.
- Cambia la verificación del marcador de categorías a una consulta de existencia con `LIMIT 1`.
- Evita tener que ejecutar `docker compose down -v` para recuperar el servicio cuando ya existen datos.


## v1.0.0.14

### Agregado
- Validaciones frontend para campos obligatorios en creación de tickets.
- Validación backend de preguntas requeridas según matriz por área, severidad y caso de uso.
- Vista de detalle de ticket con progreso por estado, SLA, resumen ejecutivo y gestión operacional.
- Filtros de auditoría por usuario, acción, entidad, ID y rango de fechas.

### Mejorado
- Permisos de tickets más estrictos para roles personalizados.
- Motivo requerido al pasar tickets a En Espera, Resuelto o Cerrado desde la interfaz.


## v1.0.0.13

### Corregido
- Corrección de CSS para modo oscuro en el formulario Nuevo Ticket.
- El bloque "Información requerida según matriz" ya no queda con fondo blanco en modo oscuro.
- Se reemplazaron gradientes hardcodeados `#fff` / `#f8fafc` por variables de tema.
- Se normalizaron colores de campos, textos y bordes para `input`, `textarea` y `select` en tema oscuro.


## v1.0.0.12

- Se cambia el build del frontend de `node:22-alpine` a `node:20-alpine` LTS para evitar errores de npm durante `npm ci`.
- Se agrega `frontend/.npmrc` con registry público de npm y timeouts/reintentos.
- Se corrige `package-lock.json` para no depender de un registry interno del entorno de generación.
- Se mantiene cache de dependencias con BuildKit para acelerar builds posteriores.
- Se documenta el flujo recomendado de Docker sin `--no-cache`.

## v1.0.0.11

- Optimización inicial del build Docker con cache de npm/pip.
