output "cloud_run_url" {
  description = "URL of the deployed Cloud Run backend service"
  value       = module.cloud_run.service_url
}

output "model_bucket_name" {
  description = "GCS bucket name where model weights are stored"
  value       = module.gcs.bucket_name
}
