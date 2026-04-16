resource "google_secret_manager_secret" "inference_mode" {
  secret_id = "INFERENCE_MODE"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "inference_mode" {
  secret      = google_secret_manager_secret.inference_mode.id
  secret_data = var.inference_mode
}

output "inference_mode_version" {
  value = google_secret_manager_secret_version.inference_mode.name
}
