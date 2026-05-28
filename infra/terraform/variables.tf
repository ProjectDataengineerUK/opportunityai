variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "github_repo" {
  description = "GitHub repo no formato owner/repo (ex: joao/opportunityai)"
  type        = string
}

variable "backend_image" {
  description = "Backend container image URI (preenchido pelo CI/CD)"
  type        = string
  default     = "us-central1-docker.pkg.dev/PROJECT_ID/opportunityai/backend:latest"
}

variable "frontend_image" {
  description = "Frontend container image URI (preenchido pelo CI/CD)"
  type        = string
  default     = "us-central1-docker.pkg.dev/PROJECT_ID/opportunityai/frontend:latest"
}
