terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "opportunity-ai-497718-tf-state-opportunityai"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  tf_state_bucket = "${var.project_id}-tf-state-opportunityai"
  ar_host         = "${var.region}-docker.pkg.dev"
  ar_backend      = "${local.ar_host}/${var.project_id}/opportunityai/backend"
  ar_frontend     = "${local.ar_host}/${var.project_id}/opportunityai/frontend"
}

# ─── APIs ────────────────────────────────────────────────────────────────────

resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "firestore.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "aiplatform.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

# ─── Artifact Registry ───────────────────────────────────────────────────────

resource "google_artifact_registry_repository" "images" {
  repository_id = "opportunityai"
  format        = "DOCKER"
  location      = var.region
  depends_on    = [google_project_service.services]
}

# ─── GCS bucket para estado do Terraform ────────────────────────────────────

resource "google_storage_bucket" "tf_state" {
  name          = local.tf_state_bucket
  location      = var.region
  force_destroy = false

  versioning { enabled = true }

  lifecycle_rule {
    condition { num_newer_versions = 5 }
    action { type = "Delete" }
  }
}

# ─── Firestore ───────────────────────────────────────────────────────────────

resource "google_firestore_database" "default" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
  depends_on  = [google_project_service.services]
}


# ─── Secrets ─────────────────────────────────────────────────────────────────

resource "google_secret_manager_secret" "freelancer_token" {
  secret_id  = "freelancer-token"
  depends_on = [google_project_service.services]
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "freelancer_client_id" {
  secret_id  = "freelancer-client-id"
  depends_on = [google_project_service.services]
  replication {
    auto {}
  }
}


# ─── Service Account — Backend ───────────────────────────────────────────────

resource "google_service_account" "backend_sa" {
  account_id   = "opportunityai-backend"
  display_name = "OpportunityAI Backend"
}

resource "google_project_iam_member" "backend_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "backend_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_freelancer_token" {
  secret_id = google_secret_manager_secret.freelancer_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_freelancer_client_id" {
  secret_id = google_secret_manager_secret.freelancer_client_id.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}

# ─── Workload Identity Federation — GitHub Actions ───────────────────────────

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
  depends_on                = [google_project_service.services]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }

  attribute_condition = "attribute.repository == '${var.github_repo}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# ─── Service Account — CI/CD ─────────────────────────────────────────────────

resource "google_service_account" "cicd_sa" {
  account_id   = "opportunityai-cicd"
  display_name = "OpportunityAI CI/CD"
}

locals {
  cicd_roles = [
    "roles/run.admin",
    "roles/artifactregistry.writer",
    "roles/storage.admin",
    "roles/secretmanager.viewer",
    "roles/secretmanager.secretAccessor",
    "roles/iam.serviceAccountUser",
    "roles/datastore.owner",
    "roles/serviceusage.serviceUsageAdmin",
    "roles/iam.securityAdmin",
    "roles/iam.workloadIdentityPoolAdmin",
  ]
}

resource "google_project_iam_member" "cicd_roles" {
  for_each = toset(local.cicd_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.cicd_sa.email}"
}

resource "google_service_account_iam_member" "cicd_wif_binding" {
  service_account_id = google_service_account.cicd_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}

# ─── Cloud Run — Backend ─────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "backend" {
  name       = "opportunityai-backend"
  location   = var.region
  depends_on = [
    google_project_service.services,
  ]

  lifecycle {
    ignore_changes = [template[0].containers[0].image]
  }

  template {
    service_account = google_service_account.backend_sa.email

    containers {
      image = var.backend_image

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCP_LOCATION"
        value = var.region
      }
      env {
        name = "FREELANCER_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.freelancer_token.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "FREELANCER_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.freelancer_client_id.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }
  }
}

resource "google_cloud_run_service_iam_member" "backend_public" {
  location = google_cloud_run_v2_service.backend.location
  service  = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ─── Cloud Run — Frontend ─────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "frontend" {
  name       = "opportunityai-frontend"
  location   = var.region
  depends_on = [google_cloud_run_v2_service.backend]

  lifecycle {
    ignore_changes = [template[0].containers[0].image]
  }

  template {
    containers {
      image = var.frontend_image

      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = google_cloud_run_v2_service.backend.uri
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
  }
}

resource "google_cloud_run_service_iam_member" "frontend_public" {
  location = google_cloud_run_v2_service.frontend.location
  service  = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
