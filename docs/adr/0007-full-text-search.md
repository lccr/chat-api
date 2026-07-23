# 7. Búsqueda de texto completo con FTS5

Fecha: 2026-07-22

## Estado

Aceptada

## Contexto

El assessment propone como punto extra "funcionalidad de búsqueda de mensajes",
sobre una base de datos SQLite. Una búsqueda con `LIKE '%término%'` recorre
toda la tabla, no entiende de palabras y no puede ordenar por relevancia.

## Decisión

Usar **FTS5**, el motor de búsqueda de texto completo integrado en SQLite,
mediante una tabla virtual en modo *external content* sincronizada con
`messages` a través de un trigger de inserción. Los resultados se ordenan por
`rank`, la puntuación de relevancia BM25 que provee FTS5.

## Consecuencias

- No se añade ninguna dependencia externa: la capacidad ya está en el motor
  que el assessment exige. Un motor de búsqueda dedicado (Elasticsearch,
  OpenSearch) sería desproporcionado para este alcance.
- El modo *external content* (`content='messages'`) evita duplicar el texto:
  el índice guarda solo la estructura de búsqueda y lee el contenido de la
  tabla original.
- La sincronización es responsabilidad de la base de datos, no del código de
  aplicación: el trigger se dispara con cada inserción, de modo que ningún
  repositorio puede olvidar actualizar el índice.
- Solo existe trigger de `INSERT`. El dominio no contempla edición ni borrado
  de mensajes, así que triggers para esas operaciones serían código muerto; si
  esos casos de uso aparecieran, habría que añadirlos.
- La consulta del usuario se entrecomilla y se trata como frase literal. Esto
  impide que la sintaxis de consulta de FTS5 (`AND`, `OR`, `*`, `-`) rompa la
  búsqueda con entrada arbitraria, a cambio de no exponer esos operadores.
- La ruta `/search` se declara antes que `/{session_id}` en el router, ya que
  FastAPI resuelve las rutas en orden y la paramétrica capturaría la literal.
- Migrar a otro motor de base de datos requeriría reimplementar la búsqueda:
  FTS5 es específico de SQLite. El punto de desacople del repositorio contiene
  ese cambio en una sola implementación.