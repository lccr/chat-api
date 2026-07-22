# 4. Persistencia con SQLite tras un punto de desacople del repositorio

Fecha: 2026-07-22

## Estado

Aceptada

## Contexto

El assessment exige SQLite por simplicidad y facilidad de arranque. El sistema
también debería ser desplegable, y un despliegue de producción tendría
necesidades de persistencia distintas (concurrencia, durabilidad, evolución
del esquema).

## Decisión

Usar SQLite a través de SQLAlchemy 2.0, tras un punto de desacople `MessageRepository`
del ADR-0002. Crear el esquema al arranque con `Base.metadata.create_all`.
Persistir todos los datetimes mediante un tipo `UTCDateTime` propio.

## Consecuencias

- El esquema usa una clave primaria surrogate entera (`id`) distinta del
  identificador de negocio (`message_id`), que se impone como único. Esto
  desacopla el esquema físico de un valor controlado por el cliente y mantiene
  eficientes los joins y los índices.
- `create_all` es suficiente para este alcance pero no gestiona *cambios* de
  esquema: un sistema de producción usaría migraciones versionadas y
  reversibles (por ejemplo, Alembic). Las migraciones quedan deliberadamente
  fuera de alcance aquí.
- SQLite almacena los datetimes sin zona horaria y los devuelve naive. El tipo
  `UTCDateTime` normaliza al escribir y re-adjunta UTC al leer, de modo que la
  información de zona horaria sobrevive el ida y vuelta y todos los endpoints
  serializan las marcas de tiempo de forma consistente.
- SQLite es de un solo escritor y basado en archivo, lo que restringe el
  despliegue en la nube: los destinos serverless con sistemas de archivos
  efímeros o múltiples instancias no son adecuados sin un volumen compartido y
  persistente. Como la persistencia vive tras un punto de desacople del repositorio,
  migrar a una base de datos gestionada (Cloud SQL, RDS o un Postgres
  serverless) afecta solo el composition root y la cadena de conexión, no el
  dominio.