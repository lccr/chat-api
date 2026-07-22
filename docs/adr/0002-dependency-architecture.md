# 2. Inversión de dependencias mediante protocolos y un composition root

Fecha: 2026-07-22

## Estado

Aceptada

## Contexto

Las capas definidas en el ADR-0001 deben conectarse entre sí sin acoplar el
dominio a implementaciones concretas. La capa de servicios necesita un
repositorio y un pipeline de procesamiento, pero no debe depender de SQLite ni
de cómo se construyen esos colaboradores. Las pruebas deben poder sustituirlos
por dobles (fakes).

## Decisión

Depender de **abstracciones** expresadas como `typing.Protocol`, y concentrar
todas las elecciones concretas en un único **composition root**
(`app/api/deps.py`).

- `MessageRepository` y `ProcessingStep` son Protocols. Las implementaciones
  los satisfacen estructuralmente — no importan ni heredan del Protocol — y se
  verifican en el punto de inyección mediante el verificador de tipos.
- Los colaboradores se pasan por constructor (el servicio recibe su
  repositorio y sus pasos; el repositorio recibe su sesión). Nada accede a
  estado global.
- `deps.py` es el único módulo que nombra clases concretas y las construye.
  Los colaboradores de ámbito de aplicación y sin estado (pasos del pipeline,
  engine) se construyen una vez; los de ámbito de petición y con estado (la
  sesión de base de datos) se construyen por petición.

## Consecuencias

- El servicio se prueba con un repositorio falso en memoria y sin base de
  datos, lo que demuestra que el dominio está desacoplado de la persistencia.
- Cambiar SQLite por otra base de datos afecta un solo lugar — el composition
  root — no el dominio.
- La dependencia de sesión de base de datos gobierna la frontera de la unidad
  de trabajo: hace commit cuando el handler de la petición retorna con
  normalidad y rollback ante cualquier excepción, mientras que los
  repositorios solo hacen flush. Esto mantiene atómica cada petición.
- Usar Protocols en lugar de clases base abstractas hace que las
  implementaciones no carguen ninguna dependencia hacia la abstracción, a
  cambio de que la conformidad solo se verifique donde una implementación se
  inyecta realmente.