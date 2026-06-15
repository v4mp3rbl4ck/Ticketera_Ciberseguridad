# syntax=docker/dockerfile:1.7

# v1.0.0.17
# Se baja de Node 22 a Node 20 LTS para evitar errores intermitentes de npm
# como "Exit handler never called" durante npm ci.
FROM node:20-alpine AS deps
WORKDIR /app

# Copiamos solo manifiestos para que Docker pueda cachear dependencias.
COPY .npmrc package.json package-lock.json ./

# npm ci usa package-lock y es reproducible.
# El cache mount acelera builds posteriores sin forzar --no-cache.
RUN --mount=type=cache,id=ticketera-frontend-npm,target=/root/.npm \
    npm ci --prefer-offline --no-audit --fund=false --loglevel=warn

FROM node:20-alpine AS build
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG VITE_API_URL=/api/v1
ARG VITE_APP_TIMEZONE=America/Santiago
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_APP_TIMEZONE=$VITE_APP_TIMEZONE

RUN npm run build

FROM nginx:1.27-alpine AS production
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -qO- http://localhost/health || exit 1
CMD ["nginx", "-g", "daemon off;"]
