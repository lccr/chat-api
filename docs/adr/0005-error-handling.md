# 5. Envelope de error uniforme con traducción de excepciones de dominio

Fecha: 2026-07-22

## Estado

Aceptada

## Contexto

El assessment requiere un manejo de errores robusto y amigable para el
usuario, con códigos de estado HTTP apropiados y una forma de respuesta de
error consistente. Los errores surgen de varias fuentes: payloads inválidos,
violaciones de reglas de negocio (id duplicado), recursos inexistentes,
errores de enrutamiento del framework (404, 405) y fallos inesperados.

## Decisión

Toda respuesta — de éxito o de error — comparte un mismo envelope de nivel
superior. Los errores se modelan como una jerarquía `DomainError` que lanza el
dominio, cada uno con un `code` estable y legible por máquina y un
`status_code` HTTP. Handlers de excepción centralizados traducen las
excepciones al envelope de error en la frontera de la API; el dominio nunca
lanza excepciones HTTP del framework.

## Consecuencias

- El dominio lanza errores agnósticos del framework (`InvalidFormatError`,
  `DuplicateMessageError`, `NotFoundError`), de modo que la lógica de negocio
  podría rehospedarse bajo otro framework reescribiendo solo los handlers.
- Cuatro handlers cubren cuatro clases de fallo: errores de dominio, errores
  de validación de peticiones, errores HTTP del framework y cualquier
  excepción no controlada. Ningún endpoint puede filtrar el cuerpo 422 por
  defecto de FastAPI, el cuerpo 404 por defecto de Starlette ni un stack trace.
- El `RequestValidationError` de FastAPI se intercepta y se reaplana dentro
  del envelope, de modo que los fallos de validación usan la misma forma que
  cualquier otro error.
- El handler de último recurso registra la excepción completa del lado del
  servidor y devuelve un mensaje genérico al cliente ("registrar todo, exponer
  nada"), evitando la divulgación de información.
- Los códigos de error son estables y distintos del estado HTTP, de modo que
  los clientes pueden ramificar según el `code` sin parsear mensajes legibles
  por humanos. Los nuevos tipos de error se agregan heredando de `DomainError`
  con un `code` y un `status_code` — cuatro líneas, sin cambios en los handlers
  (Open/Closed).