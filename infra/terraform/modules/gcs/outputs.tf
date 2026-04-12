output "bucket_name" {
  description = "GCS bucket name for model weights"
  value       = google_storage_bucket.models.name
}
