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
  default     = "us-docker.pkg.dev/cloudrun/container/hello:latest"
}

variable "frontend_image" {
  description = "Frontend container image URI (preenchido pelo CI/CD)"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello:latest"
}
