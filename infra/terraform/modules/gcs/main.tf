resource "google_storage_bucket" "models" {
  name          = "${var.project_id}-emotion-vision-models"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "outputs" {
  name          = "${var.project_id}-emotion-vision-outputs"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true
}
