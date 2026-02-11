variable "environment" {
  description = "Environment name (dev or prod)"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "datastore_id" {
  description = "HealthLake Datastore ID"
  type        = string
  default     = "87993ad99cdd565d723feaadaf1ac912"
}

locals {
  name_prefix = var.environment == "prod" ? "" : "${var.environment}-"
  route_prefix = var.environment == "prod" ? "" : "${var.environment}-"
}
