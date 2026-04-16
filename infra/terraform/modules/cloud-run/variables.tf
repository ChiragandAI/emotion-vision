variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for the Cloud Run service"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
}

variable "model_bucket_name" {
  description = "GCS bucket name where model weights are stored"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "inference_mode_version" {
  description = "Pinned secret version resource name for INFERENCE_MODE"
  type        = string
}
