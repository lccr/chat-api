# Chat API — propuesta de infraestructura en AWS.
#
# Define un despliegue basado en contenedor: la imagen del proyecto en ECR,
# ejecutada por App Runner detrás de HTTPS gestionado, con la clave de API
# almacenada en Secrets Manager.
#
# Esta es una propuesta: no se ha aplicado. Ver README.md en este directorio.

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# --- Registro de la imagen -------------------------------------------------

resource "aws_ecr_repository" "chat_api" {
  name                 = "${var.project_name}-repo"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# --- Secreto: clave de API -------------------------------------------------

resource "aws_secretsmanager_secret" "api_key" {
  name = "${var.project_name}-api-key"
}

# --- Rol de ejecución para App Runner --------------------------------------

resource "aws_iam_role" "app_runner_access" {
  name = "${var.project_name}-apprunner-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "build.apprunner.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "app_runner_ecr" {
  role       = aws_iam_role.app_runner_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# --- Servicio --------------------------------------------------------------

resource "aws_apprunner_service" "chat_api" {
  service_name = var.project_name

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.app_runner_access.arn
    }

    image_repository {
      image_identifier      = "${aws_ecr_repository.chat_api.repository_url}:${var.image_tag}"
      image_repository_type = "ECR"

      image_configuration {
        port = "8000"

        runtime_environment_variables = {
          APP_BANNED_WORDS = var.banned_words
          APP_RATE_LIMIT   = var.rate_limit
          APP_DATABASE_URL = "sqlite:////data/chat_data.db"
        }

        runtime_environment_secrets = {
          APP_API_KEY = aws_secretsmanager_secret.api_key.arn
        }
      }
    }

    auto_deployments_enabled = false
  }

  instance_configuration {
    cpu    = var.cpu
    memory = var.memory
  }

  health_check_configuration {
    protocol = "HTTP"
    path     = "/health"
    interval = 10
    timeout  = 5
  }
}