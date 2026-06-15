# Variables de entorno

Archivo base: `.env.example`.

Variables críticas:

| Variable | Descripción |
|---|---|
| SECRET_KEY | Firma de JWT. Debe ser largo y aleatorio. |
| DATABASE_URL | URL de conexión SQLAlchemy a PostgreSQL. |
| POSTGRES_PASSWORD | Contraseña de PostgreSQL. |
| ACCESS_TOKEN_EXPIRE_MINUTES | Duración de sesión. |
| MAX_UPLOAD_SIZE_MB | Tamaño máximo por evidencia. |
| SMTP_ENABLED | Habilita o deshabilita correo. |
| SMTP_HOST | Servidor SMTP. |
| SMTP_FROM | Remitente del sistema. |
| REPORTS_ENABLED | Habilita exportación PDF/Excel/CSV. |

Para operación real, nunca uses los valores por defecto de secretos y contraseñas.

### APP_TIMEZONE

Zona horaria oficial usada por la plataforma para cálculo de SLA y visualización de fechas.

Valor recomendado para Chile:

```env
APP_TIMEZONE=America/Santiago
```

El backend almacena fechas en UTC y convierte a esta zona para horario laboral y vistas de usuario.
