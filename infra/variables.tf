variable "aws_region" {
  description = "Región de AWS donde se despliega el servicio"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nombre base para los recursos"
  type        = string
  default     = "chat-api"
}

variable "image_tag" {
  description = "Etiqueta de la imagen a desplegar"
  type        = string
  default     = "latest"
}

variable "banned_words" {
  description = "Palabras a censurar, separadas por comas"
  type        = string
  default     = "badword,offensive"
}

variable "rate_limit" {
  description = "Límite de peticiones por cliente en la aplicación"
  type        = string
  default     = "120/minute"
}

variable "cpu" {
  description = "vCPU asignadas al servicio"
  type        = string
  default     = "0.25 vCPU"
}

variable "memory" {
  description = "Memoria asignada al servicio"
  type        = string
  default     = "0.5 GB"
}