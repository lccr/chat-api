# 8. Limitación de tasa en la aplicación

Fecha: 2026-07-23

## Estado

Aceptada

## Contexto

El assessment propone como punto extra "un mecanismo simple de limitación de
tasa". La ubicación natural de este control es la infraestructura que precede a
la aplicación, no la aplicación misma.

## Decisión

Implementar limitación de tasa por IP con `slowapi`, aplicada a los endpoints
de `/api` mediante decorador, desactivada por defecto y configurable con
`APP_RATE_LIMIT`. La excepción de la librería se traduce a un
`RateLimitExceededError` de dominio para responder con el envelope uniforme.

## Consecuencias

- Es defensa en profundidad, no el control principal. En producción, el límite
  debería aplicarse en el API gateway o el balanceador: allí las peticiones
  abusivas se rechazan sin consumir conexiones ni workers de la aplicación.
- El contador vive en memoria del proceso, de modo que con varias instancias el
  límite efectivo se multiplica por el número de instancias. Un límite global
  requeriría almacenamiento compartido (por ejemplo Redis) o, mejor, delegar el
  control a la infraestructura.
- La identificación por IP es imprecisa tras un proxy o balanceador, donde
  todas las peticiones llegan con la dirección del intermediario; sería
  necesario interpretar `X-Forwarded-For`. Es otro motivo por el que el control
  pertenece a esa capa.
- Ambas capas pueden coexistir sin redundancia si el límite de infraestructura
  es más restrictivo que el de la aplicación: el gateway actúa primero y el de
  la aplicación queda como red de seguridad ante accesos que lo eludan.
- La traducción de la excepción de `slowapi` mantiene el contrato de error del
  proyecto: ninguna librería externa impone su formato de respuesta.
- El rechazo con `429` se verificó manualmente; la suite cubre el
  comportamiento con el limitador desactivado. Cubrirlo automáticamente
  requeriría hacer inyectable la construcción del limitador,
  pospuesto por producto funcionando pronto.