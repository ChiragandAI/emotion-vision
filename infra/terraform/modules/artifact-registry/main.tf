resource "google_artifact_registry_repository" "backend" {
  repository_id = "emotion-vision"
  format        = "DOCKER"
  location      = var.region
  description   = "Docker images for the Emotion Vision backend"
}
