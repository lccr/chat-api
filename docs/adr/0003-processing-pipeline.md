# 3. Pipeline de procesamiento extensible con censura de contenido

Fecha: 2026-07-22

## Estado

Aceptada

## Contexto

El assessment requiere un pipeline de procesamiento que valide el mensaje,
filtre contenido inapropiado y agregue metadatos (conteo de palabras, conteo
de caracteres, marca de tiempo de procesamiento). El diseño debe facilitar
agregar pasos de procesamiento más adelante sin desestabilizar los existentes.

## Decisión

Modelar el pipeline como una lista ordenada de **pasos** independientes, cada
uno conforme a un Protocol `ProcessingStep` y que transforma un
`ProcessingResult` compartido y mutable. Agregar comportamiento significa
añadir un paso, nunca editar uno existente (Open/Closed).

Para el contenido inapropiado, el filtro **censura** las palabras prohibidas
reemplazándolas por asteriscos de igual longitud, y almacena el mensaje
censurado. No rechaza el mensaje.

## Consecuencias

- La validación de formato no es un paso del pipeline: ocurre antes, de forma
  declarativa, en los esquemas Pydantic, en la frontera de la API. El pipeline
  solo realiza procesamiento a nivel de negocio (censura, enriquecimiento).
- El orden de los pasos es significativo e intencional: el filtro corre antes
  que el enriquecedor, de modo que los metadatos describan el contenido
  almacenado (censurado).
- El emparejamiento por límites de palabra (`\b`) evita censurar subcadenas de
  palabras más grandes (el "Scunthorpe problem"); las palabras prohibidas se
  escapan como regex para que los metacaracteres se traten de forma literal.
- La censura mantiene cada paso como un transformador puro, coherente con el
  enriquecedor. Se consideró una política de rechazo ante violación; no se
  implementó como una opción de configuración porque el pipeline ya es
  extensible por diseño — una política de rechazo sería un paso alternativo, no
  una rama condicional. Elegir un único comportamiento documentado evita
  duplicar la superficie de pruebas y documentación para una necesidad que el
  assessment no plantea.