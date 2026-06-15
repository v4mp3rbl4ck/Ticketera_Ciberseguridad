# Backup y restore

## Backup manual

```bash
./scripts/backup.sh
```

Genera un archivo `.tar.gz` en `backups/` con:

- Dump SQL de PostgreSQL.
- Evidencias almacenadas en `/app/uploads`.

## Restore

```bash
./scripts/restore.sh ./backups/ticketera-backup-YYYYMMDD-HHMMSS.tar.gz
```

## Automatización sugerida

Agregar a cron del servidor:

```text
0 2 * * * cd /opt/ticketera && ./scripts/backup.sh
```

También se recomienda copiar backups a almacenamiento externo.
