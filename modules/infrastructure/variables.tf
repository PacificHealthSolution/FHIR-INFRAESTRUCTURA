variable "environment" {
  description = "Environment name (dev or prod)"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

locals {
  name_prefix = var.environment == "prod" ? "" : "${var.environment}-"
}
