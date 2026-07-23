# Propuesta de infraestructura

Definición en Terraform de un despliegue del servicio en AWS. **Es una
propuesta**: la definición está validada sintácticamente (`terraform validate`)
pero no se ha aplicado a una cuenta real.

## Arquitectura propuesta

```
Cliente
   │  HTTPS
   ▼
CloudFront + AWS WAF          ← límite de tasa y filtrado de tráfico
   │
   ▼
AWS App Runner                ← ejecuta la imagen del contenedor
   │
   ├── Amazon ECR             ← registro de la imagen
   └── AWS Secrets Manager    ← clave de API
```

| Componente | Servicio | Función |
| ---------- | -------- | ------- |
| Registro de imágenes | Amazon ECR | Almacena la imagen construida desde el `Dockerfile` del proyecto |
| Ejecución | AWS App Runner | Ejecuta el contenedor con HTTPS y escalado gestionados |
| Secretos | AWS Secrets Manager | Provee `APP_API_KEY` al contenedor sin exponerla en la definición |
| Borde | CloudFront + WAF | Limitación de tasa y filtrado antes de llegar a la aplicación |

## Por qué AWS

La aplicación se empaqueta como contenedor y se configura por variables de
entorno, de modo que no está atada a ningún proveedor: los tres grandes ofrecen
un servicio equivalente de contenedor gestionado (Google Cloud Run, Azure
Container Apps). La elección responde a criterios prácticos más que técnicos:

- **Experiencia previa** con la plataforma, lo que reduce el riesgo de errores
  de configuración y acelera la resolución de incidentes.
- **Catálogo completo para este caso**: App Runner para el modelo de contenedor,
  Lambda + API Gateway si se optara por serverless, y RDS o Aurora Serverless
  para la migración de persistencia — sin cambiar de proveedor al evolucionar.

El acoplamiento a AWS se limita a esta definición de infraestructura. Migrar a
otro proveedor implicaría reescribir los recursos de Terraform, no la
aplicación: la imagen y su configuración son las mismas.

## Por qué App Runner

App Runner ejecuta directamente la imagen del proyecto, sin adaptadores ni
cambios en el código. Gestiona HTTPS, escalado y despliegue, y usa el endpoint
`/health` existente como verificación de estado.

La alternativa serverless sería **Lambda + API Gateway**, que escala a cero y
reduce el costo en reposo, pero requiere un adaptador ASGI (Mangum) y su
sistema de archivos efímero es incompatible con SQLite. App Runner mantiene el
artefacto y el modelo de ejecución idénticos a los verificados en local.

## Limitación de tasa en dos capas

La limitación principal corresponde al borde (WAF), donde el tráfico abusivo se
rechaza antes de consumir recursos de la aplicación y el conteo es global. El
límite de la aplicación (`APP_RATE_LIMIT`) se configura más permisivo y actúa
como red de seguridad. Ver [ADR-0008](../docs/adr/0008-rate-limiting.md).

## Persistencia

La definición conserva SQLite para mantener la paridad con lo entregado, con la
limitación conocida: el almacenamiento del contenedor es efímero y una única
instancia puede escribir. Un despliegue con datos reales debería sustituirla por
**Amazon RDS (PostgreSQL)** o **Aurora Serverless v2**, cambiando únicamente
`APP_DATABASE_URL` y la implementación del repositorio — el dominio no se ve
afectado (ver [ADR-0004](../docs/adr/0004-persistence.md)).

Esa migración también resolvería el escalado: con la base fuera del contenedor,
el servicio puede correr varias instancias.

## Aplicar la propuesta

```bash
cd infra
terraform init
terraform plan -var="image_tag=v1.0.0"
terraform apply -var="image_tag=v1.0.0"
```

Antes de aplicar, la imagen debe estar publicada en el repositorio ECR que crea
esta definición, y el valor de la clave de API cargado en el secreto.