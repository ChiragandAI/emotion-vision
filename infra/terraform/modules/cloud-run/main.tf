resource "google_cloud_run_v2_service" "backend" {
  name     = "emotion-vision-backend"
  location = var.region

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/emotion-vision/backend:${var.image_tag}"

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }

      env {
        name = "INFERENCE_MODE"
        value_source {
          secret_key_ref {
            secret  = "INFERENCE_MODE"
            version = "latest"
          }
        }
      }

      env {
        name  = "MODEL_BUCKET"
        value = var.model_bucket_name
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "public_access" {
  name     = google_cloud_run_v2_service.backend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
