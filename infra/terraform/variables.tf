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

variable "billing_account_id" {
  description = "GCP billing account ID without prefix, e.g. 01BC1C-0D5977-F3C59C"
  type        = string
  default     = "01BC1C-0D5977-F3C59C"
}

variable "monthly_budget_amount" {
  description = "Monthly budget cap in the billing account's native currency. Email alerts fire at 50%, 90%, and 100% of this value."
  type        = number
  default     = 2000
}

variable "currency_code" {
  description = "Currency code for the budget. Must match the billing account's currency (INR for this account)."
  type        = string
  default     = "INR"
}
