# 6. Autenticación simple por clave de API

Fecha: 2026-07-22

## Estado

Aceptada

## Contexto

El assessment propone como punto extra "un mecanismo de autenticación simple".
La API no tiene modelo de usuarios, roles ni sesiones, y el alcance no plantea
autorización diferenciada entre clientes.

## Decisión

Autenticación por **clave de API** en la cabecera `X-API-Key`, verificada
contra un valor de configuración. La dependencia se aplica a nivel de router,
de modo que todas las rutas bajo `/api` quedan protegidas y `/health` no.

La autenticación es opt-in: con `APP_API_KEY` vacía queda desactivada.

## Consecuencias

- Se descartaron JWT y OAuth por desproporcionados para el alcance: no hay
  usuarios ni sesiones que representar, y añadirían emisión, expiración y
  renovación de tokens sin aportar a lo que se evalúa.
- La comparación de la clave usa `secrets.compare_digest`, en tiempo
  constante, para no filtrar información mediante ataques de temporización.
- Aplicar la dependencia al router y no a cada endpoint hace que las rutas
  nuevas nazcan protegidas por defecto; olvidar el decorador dejaría de ser
  una vía de exposición silenciosa.
- `/health` queda deliberadamente sin autenticación: los `HEALTHCHECK` de
  contenedor y los probes de orquestadores no envían credenciales.
- El modelo es de clave única compartida: identifica que el llamante conoce el
  secreto, pero no *quién* es. No hay usuarios ni roles, y por tanto tampoco
  autorización (403). Un sistema real con múltiples clientes requeriría
  identidades y permisos diferenciados.
- El nuevo `UnauthorizedError` (401) se integró añadiendo una subclase de
  `DomainError`, sin modificar los manejadores de excepciones (ver ADR-0005).