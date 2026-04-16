variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region to deploy resources into"
  type        = string
  default     = "us-central1"
}

variable "image_tag" {
  description = "Docker image tag to deploy to Cloud Run (e.g. sha-abc1234)"
  type        = string
}

variable "inference_mode" {
  description = "Inference mode (mock|local|provider). Production must be 'local' or 'provider'."
  type        = string
  default     = "local"

  validation {
    condition     = contains(["mock", "local", "provider"], var.inference_mode)
    error_message = "inference_mode must be one of: mock, local, provider."
  }
}

variable "environment" {
  description = "Deployment environment (production|staging|dev). Backend refuses to boot with mock mode in production."
  type        = string
  default     = "production"
}

variable "alert_email" {
  description = "Email address to receive Cloud Monitoring alerts (uptime, error rate, latency)"
  type        = string
  default     = "official.chiragdahiya@gmail.com"
}
