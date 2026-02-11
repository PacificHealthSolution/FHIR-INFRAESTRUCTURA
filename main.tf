terraform {
  required_version = ">= 1.0"
  
  backend "s3" {
    bucket  = "fhir-terraform-state-920373013005"
    key     = "dev/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}
