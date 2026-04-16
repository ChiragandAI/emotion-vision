terraform {
  required_version = ">= 1.6"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Terraform state stored in GCS so the whole team shares the same state
  # This bucket must be created manually before running terraform init
  backend "gcs" {
    bucket = "emotion-vision-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "artifact_registry" {
  source = "./modules/artifact-registry"
  region = var.region
}

module "gcs" {
  source     = "./modules/gcs"
  project_id = var.project_id
  region     = var.region
}

module "secret_manager" {
  source         = "./modules/secret-manager"
  project_id     = var.project_id
  inference_mode = var.inference_mode
}

module "cloud_run" {
  source                 = "./modules/cloud-run"
  project_id             = var.project_id
  region                 = var.region
  image_tag              = var.image_tag
  model_bucket_name      = module.gcs.bucket_name
  environment            = var.environment
  inference_mode_version = module.secret_manager.inference_mode_version
}
