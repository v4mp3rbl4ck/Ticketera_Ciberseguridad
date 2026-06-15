# Hardening OWASP/CWE - Ticketera Ciberseguridad y Networking v1.0.0.24 / v1.0.0.25

## Objetivo

Reforzar la plataforma contra vulnerabilidades web/API comunes antes de la fase final `v1.0.0.25`, especialmente IDOR/BOLA, exposición de archivos, mass assignment, fuga de datos por API y errores básicos de configuración.

## Controles implementados

### 1. Referencias públicas no secuenciales

- `users.public_id`
- `tickets.public_id`
- `ticket_comments.public_id`
- `ticket_attachments.public_id`

El ID numérico se mantiene solo como llave interna de base de datos. La API y el frontend usan referencias no secuenciales como `usr_*`, `tkt_*`, `com_*` y `att_*`.

Riesgos cubiertos:

- OWASP API1: Broken Object Level Authorization.
- CWE-639: Authorization Bypass Through User-Controlled Key.
- Enumeración de objetos internos.

### 2. Autorización centralizada por objeto

Archivo:

```text
backend/app/services/authorization_service.py
```

Funciones principales:

```text
can_view_ticket()
can_manage_ticket()
can_download_attachment()
can_view_user()
can_edit_user()
require_view_ticket()
require_manage_ticket()
resolve_user_ref()
```

Cada endpoint sensible debe validar autorización de objeto, no solo rol general.

### 3. Respuestas anti-enumeración

Cuando un usuario intenta acceder a un objeto que no existe o no le pertenece, el backend responde de forma genérica con `404`, evitando confirmar si el recurso existe.

Ejemplos:

```text
/tickets/tkt_xxx
/tickets/tkt_xxx/attachments/att_xxx/download
/admin/users/usr_xxx
```

### 4. Auditoría reforzada

Se agregaron eventos como:

```text
login_success
login_failed
profile_update
password_change
ticket_access_denied
ticket_manage_denied
attachment_access_denied
attachment_internal_access_denied
user_access_denied
attachment_download
```

### 5. Evidencias / adjuntos seguros

Controles aplicados:

- Tamaño máximo por archivo.
- Lista de extensiones permitidas.
- Lista de extensiones bloqueadas.
- Sanitización de nombre original.
- Nombre físico aleatorio en disco.
- Hash SHA-256 de evidencias nuevas.
- Detección básica de MIME por firma de archivo.
- Bloqueo de contenido activo como HTML, SVG, script o PHP embebido.
- Descarga mediante endpoint autenticado con validación de ticket/comentario.
- Auditoría de descargas.

### 6. Mass assignment / propiedad de objeto

Schemas críticos usan:

```python
model_config = {"extra": "forbid"}
```

Esto reduce el riesgo de que un cliente modifique campos no esperados como `role`, `is_admin`, `created_by_id`, `is_deleted` o `assigned_to_id` fuera del endpoint autorizado.

### 7. Cabeceras HTTP de seguridad

La aplicación agrega:

```text
Content-Security-Policy
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy
Cross-Origin-Resource-Policy
Strict-Transport-Security si FORCE_HTTPS=true
```

Variables `.env`:

```env
ENABLE_CSP=true
FORCE_HTTPS=false
SECURITY_STRICT_STARTUP=false
AUDIT_DENIED_ACCESS=true
```

## Validaciones para v1.0.0.25

### IDOR / BOLA

- Solicitante A no puede abrir tickets de solicitante B.
- Solicitante A no puede descargar adjuntos de tickets de B.
- Solicitante no puede descargar adjuntos de notas internas.
- Analista solo ve tickets permitidos por área/asignación según rol.
- Cambiar el `tkt_*` en la URL no debe exponer datos.
- Cambiar el `att_*` en la URL no debe descargar archivos ajenos.

### Usuarios y roles

- Usuario normal no puede consultar `/admin/users`.
- Usuario normal no puede actualizar otro usuario.
- Usuario normal no puede cambiar su rol vía API.
- Administrador no puede eliminar su propia cuenta.
- No se permite eliminar el último administrador activo.

### Mass assignment

Intentar enviar campos extra debe fallar:

```json
{
  "full_name": "Test",
  "role": "admin",
  "is_admin": true
}
```

### Evidencias

- Bloquear `.exe`, `.sh`, `.ps1`, `.html`, `.svg`, `.php`, `.js`.
- Bloquear HTML/SVG aunque se suba con extensión `.txt` si se detecta como contenido activo.
- Descargar evidencia requiere token válido.
- Descargas quedan en auditoría.

### Cabeceras

Validar con `curl -I`:

```bash
curl -I http://localhost:8080
curl -I http://localhost:8000/health
```

Debe observarse al menos:

```text
X-Content-Type-Options
X-Frame-Options
Referrer-Policy
Permissions-Policy
Content-Security-Policy
```
