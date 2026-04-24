variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "service_name" {
  description = "Cloud Run service name to monitor"
  type        = string
  default     = "emotion-vision-backend"
}

variable "service_host" {
  description = "Hostname of the Cloud Run service (no scheme, no path) for the uptime check, e.g. emotion-vision-backend-xxxxx.a.run.app"
  type        = string
}

variable "alert_email" {
  description = "Email address to receive monitoring alerts"
  type        = string
}

variable "latency_threshold_ms" {
  description = "p95 request latency threshold in milliseconds"
  type        = number
  default     = 800
}

variable "error_rate_threshold" {
  description = "Fractional error rate threshold (0.01 = 1%)"
  type        = number
  default     = 0.01
}

variable "enable_uptime_check" {
  description = "Whether to create a public uptime check against the service host."
  type        = bool
  default     = false
}
