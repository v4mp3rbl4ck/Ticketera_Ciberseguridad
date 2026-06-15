# Seguridad base

Controles incluidos:

- Autenticación JWT.
- Contraseñas con hash bcrypt.
- Usuarios inactivos no pueden iniciar sesión.
- Eliminación lógica de usuarios.
- Auditoría de acciones críticas.
- Separación de notas internas y públicas.
- Adjuntos descargados por endpoint autenticado.
- Bloqueo de extensiones peligrosas.
- Límite de tamaño de archivos.
- Configuración sensible por `.env`.

Extensiones bloqueadas por defecto:

```text
.exe, .bat, .cmd, .ps1, .sh, .php, .jsp, .asp, .aspx, .js, .html, .htm, .svg, .msi, .dll, .scr, .jar, .vbs, .wsf
```

Recomendaciones para producción:

- HTTPS obligatorio.
- Cambiar credenciales iniciales.
- Deshabilitar exposición pública del puerto 8000.
- Restringir acceso administrativo por red/VPN si aplica.
- Monitorear espacio en disco por evidencias.
- Revisar logs periódicamente.
