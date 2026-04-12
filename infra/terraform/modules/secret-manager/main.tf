resource "google_secret_manager_secret" "inference_mode" {
  secret_id = "INFERENCE_MODE"

  replication {
    auto {}
  }
}
