output "environment" {
  description = "Current environment"
  value       = var.environment
}

output "api_gateway_url" {
  description = "API Gateway URL"
  value       = "https://${aws_api_gateway_rest_api.fhir_api.id}.execute-api.${var.region}.amazonaws.com/${aws_api_gateway_stage.fhir_api.stage_name}/"
}

output "lambda_functions" {
  description = "Lambda function names"
  value = {
    mapper_fhir     = aws_lambda_function.mapper_fhir.function_name
    create_resource = aws_lambda_function.create_resource.function_name
    modify_resource = aws_lambda_function.modify_resource.function_name
  }
}

output "datastore_arn" {
  description = "HealthLake Datastore ARN"
  value       = local.datastore_arn
}
