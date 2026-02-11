output "environment" {
  description = "Current environment"
  value       = var.environment
}

output "api_gateway_url" {
  description = "API Gateway URL"
  value       = aws_api_gateway_deployment.fhir_api.invoke_url
}

output "lambda_functions" {
  description = "Lambda function names"
  value = {
    patient      = aws_lambda_function.patient.function_name
    professional = aws_lambda_function.professional.function_name
    organization = aws_lambda_function.organization.function_name
    location     = aws_lambda_function.location.function_name
  }
}

output "datastore_arn" {
  description = "HealthLake Datastore ARN"
  value       = data.aws_healthlake_fhir_datastore.main.arn
}
