# Arquitectura

## Backend

El backend está separado en:

- `core`: configuración, seguridad y base de datos.
- `models`: entidades SQLAlchemy.
- `schemas`: contratos Pydantic de entrada/salida.
- `api/routes`: endpoints REST.
- `services`: lógica de negocio reutilizable.

## Frontend

El frontend está separado en:

- `api`: cliente HTTP.
- `contexts`: autenticación y estado global.
- `components`: componentes reutilizables.
- `pages`: pantallas principales.
- `styles`: CSS separado por propósito.

## Seguridad

- JWT para sesión.
- Password hashing con bcrypt.
- RBAC básico.
- Auditoría append-only con hash encadenado.
- Notas internas separadas de comentarios públicos.
- TLP por ticket.


## Catálogo dinámico de solicitudes

La matriz de solicitudes se centraliza en `backend/app/services/ticket_catalog_service.py`.

El catálogo define, por cada área y severidad:

- Canal permitido.
- Modo SLA.
- Descripción operacional.
- Casos de uso permitidos.
- Preguntas obligatorias del checklist.

El frontend consulta `/api/v1/tickets/checklist?area=...&severity=...` para obtener la información que debe mostrar al solicitante.

El campo `severity` funciona como categoría principal y el campo `category` almacena el caso de uso específico seleccionado.


## Catálogo dinámico v4

La tabla `categories` actúa como catálogo de casos de uso. Cada caso queda asociado a:

- Área técnica: Ciberseguridad o Networking.
- Severidad principal: Crítica/SOS, Alta, Media o Baja.
- Nombre del caso de uso.
- Estado activo/inactivo.

El endpoint `/tickets/checklist` obtiene los casos de uso desde base de datos, por lo que los cambios realizados desde administración se reflejan en la creación de tickets sin modificar código.

## Áreas corporativas solicitantes

El campo `project_area` del ticket representa el área corporativa que solicita el caso. La lista se expone desde `/admin/corporate-areas` y se usa en el formulario para estandarizar métricas, especialmente el Top 10 de áreas solicitantes.

## Panel administrativo modular v5

La administración se divide en módulos independientes expuestos en el panel lateral izquierdo del frontend:

- `Usuarios`: creación y mantenimiento de cuentas y roles.
- `Casos de Uso`: mantenimiento del catálogo dinámico por área técnica y severidad.
- `SLA`: configuración de primera respuesta, resolución, horario laboral y pausa.
- `Áreas Corporativas`: catálogo administrable de áreas solicitantes.
- `Auditoría`: visor de eventos inmutables con hash encadenado.

A nivel backend, las áreas corporativas se persistieron en la tabla `corporate_areas`. El formulario de creación de tickets consume solo áreas activas desde `/api/v1/admin/corporate-areas`.
