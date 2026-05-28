output "backend_url" {
  description = "URL do Cloud Run backend"
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  description = "URL do Cloud Run frontend (dashboard)"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "freelancer_secret_id" {
  description = "ID do secret para adicionar o token Freelancer"
  value       = google_secret_manager_secret.freelancer_token.secret_id
}

output "artifact_registry" {
  description = "Host do Artifact Registry para docker push"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/opportunityai"
}

output "wif_provider" {
  description = "Valor para o secret WIF_PROVIDER no GitHub Actions"
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "cicd_service_account" {
  description = "Valor para o secret WIF_SERVICE_ACCOUNT no GitHub Actions"
  value       = google_service_account.cicd_sa.email
}

output "tf_state_bucket" {
  description = "Bucket GCS para estado do Terraform"
  value       = google_storage_bucket.tf_state.name
}
