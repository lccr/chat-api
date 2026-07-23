output "service_url" {
  description = "URL pública del servicio desplegado"
  value       = "https://${aws_apprunner_service.chat_api.service_url}"
}

output "ecr_repository_url" {
  description = "URL del repositorio de imágenes"
  value       = aws_ecr_repository.chat_api.repository_url
}