# 1. Framework y arquitectura por capas

Fecha: 2026-07-22

## Estado

Aceptada

## Contexto

El assessment permite usar Flask o FastAPI y pide arquitectura limpia,
inyección de dependencias, principios SOLID, validación de peticiones, manejo
de errores robusto y una suite de pruebas. Antes de escribir código hay que
elegir un framework y una estructura general.

## Decisión

Usar **FastAPI** con una estructura por capas — api / services / repositories
/ schemas / core — donde las dependencias apuntan solo hacia adentro: la capa
api conoce a los servicios, los servicios conocen la abstracción del
repositorio, y el dominio (servicios, pipeline, modelos) nunca importa el
framework web.

## Consecuencias

- Pydantic aporta validación declarativa de peticiones y contratos tipados;
  los requisitos de esquema del assessment se mapean directamente a la
  definición de los modelos.
- La inyección de dependencias de FastAPI permite un cableado por
  constructor y sustituciones triviales en pruebas, sin librería de
  contenedor adicional.
- La documentación OpenAPI se genera desde la misma fuente de verdad que la
  validación, así que la documentación no puede desincronizarse del
  comportamiento.
- La base async-native mantiene idiomática la funcionalidad opcional de
  WebSocket.
- Como el dominio nunca importa FastAPI, los mismos servicios, pipeline y
  repositorio podrían rehospedarse bajo Flask reescribiendo solo la capa api
  — la base de la implementación espejo planeada.