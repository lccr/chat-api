# Chat API

API RESTful para procesamiento de mensajes de chat, construida con **FastAPI**,
**SQLAlchemy 2.0** y **SQLite**, siguiendo principios de arquitectura limpia.

## Requisitos

- Python 3.10+

## Puesta en marcha

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

El servicio queda disponible en `http://localhost:8000`. \
Documentación interactiva (OpenAPI): `http://localhost:8000/docs`.

## Verificación de calidad

```bash
ruff check app tests    # linting y formato
mypy app                # verificación de tipos estricta
pytest                  # suite de pruebas
pytest --cov=app        # pruebas con reporte de cobertura
```

La cobertura tiene un umbral mínimo del 85% configurado como gate; la suite
actual alcanza el 100% sobre líneas alcanzables.

## Endpoints

| Método | Ruta | Descripción |
| ------ | ---- | ----------- |
| `POST` | `/api/messages` | Crea, procesa y almacena un mensaje |
| `GET` | `/api/messages/{session_id}` | Lista los mensajes de una sesión (paginado, filtrable por remitente) |
| `GET` | `/health` | Verificación de estado del servicio |

### POST /api/messages

Cuerpo de la petición:

```json
{
  "message_id": "msg-123456",
  "session_id": "session-abcdef",
  "content": "Hola, ¿cómo puedo ayudarte hoy?",
  "timestamp": "2023-06-15T14:30:00Z",
  "sender": "system"
}
```

Respuesta (`201 Created`): el mensaje procesado, con contenido censurado si
aplica y metadatos calculados (conteo de palabras y caracteres, marca de
tiempo de procesamiento).

### GET /api/messages/{session_id}

Parámetros de consulta: `limit` (1–100, por defecto 20), `offset` (≥0, por
defecto 0), `sender` (`user` o `system`, opcional). Devuelve una página de
mensajes junto con el total, el límite y el desplazamiento aplicados.

## Formato de respuesta

Toda respuesta comparte un envelope de nivel superior:

```json
{ "status": "success", "data": { } }
```

```json
{ "status": "error", "error": { "code": "INVALID_FORMAT", "message": "...", "details": "..." } }
```

Códigos de error: `INVALID_FORMAT` (422), `DUPLICATE_MESSAGE` (409),
`NOT_FOUND` (404), `HTTP_ERROR` (404/405), `INTERNAL_ERROR` (500).

## Arquitectura

El código se organiza en capas, con las dependencias apuntando solo hacia
adentro:
app/
├── api/           # capa HTTP: rutas, cableado de dependencias, manejo de errores
├── core/          # configuración, logging, excepciones de dominio
├── schemas/       # contratos Pydantic (peticiones/respuestas)
├── services/      # casos de uso + pipeline de procesamiento
├── repositories/  # interfaces de persistencia + implementación SQLite
└── models/        # modelos ORM de SQLAlchemy

El dominio (servicios, pipeline, repositorios) no importa el framework web:
depende de abstracciones (`Protocol`) y recibe sus colaboradores por
inyección. Esto permite probar la lógica de negocio sin base de datos y
sustituir la persistencia sin tocar el dominio.

## Decisiones de diseño

Las decisiones de arquitectura están documentadas como ADRs en
[`docs/adr/`](docs/adr/):

- [ADR-0001](docs/adr/0001-framework-and-architecture.md) — Framework y arquitectura por capas
- [ADR-0002](docs/adr/0002-dependency-architecture.md) — Inversión de dependencias y composition root
- [ADR-0003](docs/adr/0003-processing-pipeline.md) — Pipeline de procesamiento y política de contenido
- [ADR-0004](docs/adr/0004-persistence.md) — Persistencia y gestión del esquema
- [ADR-0005](docs/adr/0005-error-handling.md) — Manejo de errores uniforme

## Trade-offs y trabajo futuro

- **Persistencia:** el esquema se crea al arranque con `create_all`; un sistema
  de producción usaría migraciones versionadas (Alembic). SQLite es de un solo
  escritor; escalar en la nube requeriría una base de datos gestionada, que el
  punto de desacople del repositorio permite sin cambiar el dominio.
- **Orden de mensajes:** se ordena por el `timestamp` que envía el cliente,
  vulnerable a relojes desincronizados; un sistema real usaría una marca de
  tiempo de servidor o un identificador secuencial.
- **Alcance:** el sistema es un pipeline de ingesta y consulta de mensajes, no
  un sistema de chat en tiempo real. Evolucionar hacia esto último añadiría
  entidades de sesión y participante, entrega por WebSocket y una capa de
  autorización, sin reescribir las capas actuales.