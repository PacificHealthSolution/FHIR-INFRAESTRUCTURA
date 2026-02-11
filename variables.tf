variable "environment" {
  description = "Environment name (dev or prod)"
  type        = string
  default     = "dev"
}

locals {
  name_prefix = var.environment == "prod" ? "" : "${var.environment}-"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "github_org" {
  description = "GitHub organization or username"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}

variable "github_branch" {
  description = "GitHub branch allowed to deploy"
  type        = string
  default     = "terraform"
}
