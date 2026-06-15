# Optimización de build Docker - v1.0.0.12

Esta versión optimiza el tiempo de construcción del frontend y backend.

## Cambios principales

- El frontend usa `npm ci` en vez de `npm install`.
- Se separó la instalación de dependencias en una etapa `deps`.
- Se agregó cache mount de BuildKit para `/root/.npm`.
- Se mejoró `.dockerignore` para no enviar archivos innecesarios al contexto de build.
- El backend usa cache mount de pip para acelerar reinstalaciones.
- Se agregaron scripts de reconstrucción rápida.

## Comando recomendado para reconstrucción diaria

```bash
./scripts/rebuild-fast.sh
```

O manualmente:

```bash
DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker compose build frontend backend
docker compose up -d
```

## Evitar `--no-cache`

No uses `--no-cache` salvo que realmente necesites reconstruir todo desde cero. Ese flag fuerza a Docker a ignorar capas anteriores y hace que `npm ci` vuelva a descargar dependencias.

## Si cambias `package.json` o `package-lock.json`

La etapa de dependencias se reconstruirá, lo cual es normal. Si solo cambias código React, Docker reutilizará la capa de dependencias.

## Advertencia con SECRET_KEY y símbolos `$`

Si tu `.env` tiene una clave con `$`, Docker Compose puede interpretar lo que sigue como variable de entorno y mostrar advertencias como:

```text
The "lknk3krjRQ" variable is not set. Defaulting to a blank string.
```

Soluciones:

1. Usa un secreto hexadecimal sin `$`:

```bash
openssl rand -hex 32
```

2. O escapa cada `$` como `$$` dentro del `.env`.

Ejemplo:

```env
SECRET_KEY=abc$$lknk3krjRQxyz
```


## Corrección v1.0.0.12: npm ci lento o error `Exit handler never called`

Si el build queda mucho tiempo en:

```bash
[frontend deps 4/4] RUN npm ci
```

o falla con:

```bash
npm error Exit handler never called!
```

la causa más común es una combinación inestable de Node 22 + npm 10.9.x o una caché/lockfile apuntando a un registry incorrecto.

En v1.0.0.12 se aplicaron estos cambios:

- Frontend usa `node:20-alpine` LTS.
- Se agregó `frontend/.npmrc` con `registry=https://registry.npmjs.org/`.
- Se mantiene `npm ci`, pero usando caché BuildKit.
- Se corrigió `package-lock.json` para usar el registry público de npm.

Comando recomendado:

```bash
sudo docker compose down
sudo docker compose up --build -d
```

No uses `--no-cache` salvo que quieras reconstruir absolutamente todo desde cero.
