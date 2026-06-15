# Instalación en pre-producción / producción

## Requisitos

- Docker Engine.
- Docker Compose Plugin.
- 2 GB RAM mínimo recomendado.
- 10 GB de disco mínimo para pruebas.
- Dominio o IP del servidor.

## Instalación

```bash
cp .env.example .env
```

Edita `.env` y cambia `SECRET_KEY`, `POSTGRES_PASSWORD` y `DATABASE_URL`.

Levanta servicios:

```bash
docker compose up --build -d
```

Verifica salud:

```bash
docker ps
```

URLs:

- Frontend: `http://localhost:8080`
- API: `http://localhost:8000/docs`

## Producción con dominio

Recomendado:

- Publicar solo el puerto 80/443 del proxy corporativo.
- No exponer `8000` a internet.
- Usar HTTPS.
- Restringir acceso a `/docs` si se requiere.
