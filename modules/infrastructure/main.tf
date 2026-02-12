# Construir ARN del datastore manualmente
locals {
  datastore_arn = "arn:aws:healthlake:${var.region}:${data.aws_caller_identity.current.account_id}:datastore/fhir/${var.datastore_id}"
}

data "aws_caller_identity" "current" {}

# Rol IAM para las Lambdas
resource "aws_iam_role" "lambda_role" {
  name = "${local.name_prefix}lambda-healthlake-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Política para acceso a HealthLake y permisos para invocar lambdas
resource "aws_iam_role_policy" "lambda_healthlake_policy" {
  name = "${local.name_prefix}lambda-healthlake-access"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "healthlake:ReadResource",
          "healthlake:CreateResource",
          "healthlake:UpdateResource",
          "healthlake:DeleteResource",
          "healthlake:SearchWithGet",
          "healthlake:SearchWithPost",
          "healthlake:GetCapabilities"
        ]
        Resource = local.datastore_arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          "arn:aws:lambda:${var.region}:${data.aws_caller_identity.current.account_id}:function:${local.name_prefix}create_resource",
          "arn:aws:lambda:${var.region}:${data.aws_caller_identity.current.account_id}:function:${local.name_prefix}modify_resource"
        ]
      }
    ]
  })
}

# Archivos ZIP para las Lambdas
data "archive_file" "mapper_fhir" {
  type        = "zip"
  source_file = "${path.module}/lambda_functions/mapper_fhir/handler.py"
  output_path = "${path.module}/lambda_functions/mapper_fhir.zip"
}

data "archive_file" "create_resource" {
  type        = "zip"
  source_file = "${path.module}/lambda_functions/create_resource/handler.py"
  output_path = "${path.module}/lambda_functions/create_resource.zip"
}

data "archive_file" "modify_resource" {
  type        = "zip"
  source_file = "${path.module}/lambda_functions/modify_resource/handler.py"
  output_path = "${path.module}/lambda_functions/modify_resource.zip"
}

# Lambda Functions
resource "aws_lambda_function" "mapper_fhir" {
  filename         = data.archive_file.mapper_fhir.output_path
  function_name    = "${local.name_prefix}mapper-fhir"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handler.lambda_handler"
  source_code_hash = data.archive_file.mapper_fhir.output_base64sha256
  runtime         = "python3.12"
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      DATASTORE_ID           = var.datastore_id
      REGION                 = var.region
      CREATE_RESOURCE_LAMBDA = aws_lambda_function.create_resource.function_name
      MODIFY_RESOURCE_LAMBDA = aws_lambda_function.modify_resource.function_name
    }
  }
}

resource "aws_lambda_function" "create_resource" {
  filename         = data.archive_file.create_resource.output_path
  function_name    = "${local.name_prefix}create_resource"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handler.lambda_handler"
  source_code_hash = data.archive_file.create_resource.output_base64sha256
  runtime         = "python3.12"
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      DATASTORE_ID = var.datastore_id
      REGION       = var.region
    }
  }
}

resource "aws_lambda_function" "modify_resource" {
  filename         = data.archive_file.modify_resource.output_path
  function_name    = "${local.name_prefix}modify_resource"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handler.lambda_handler"
  source_code_hash = data.archive_file.modify_resource.output_base64sha256
  runtime         = "python3.12"
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      DATASTORE_ID = var.datastore_id
      REGION       = var.region
    }
  }
}

# Permisos para mapper-fhir invocar otras lambdas
resource "aws_lambda_permission" "mapper_invoke_create" {
  statement_id  = "AllowMapperInvokeCreate"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.create_resource.function_name
  principal     = "lambda.amazonaws.com"
  source_arn    = aws_lambda_function.mapper_fhir.arn
}

resource "aws_lambda_permission" "mapper_invoke_modify" {
  statement_id  = "AllowMapperInvokeModify"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.modify_resource.function_name
  principal     = "lambda.amazonaws.com"
  source_arn    = aws_lambda_function.mapper_fhir.arn
}

# API Gateway REST API
resource "aws_api_gateway_rest_api" "fhir_api" {
  name        = "${local.name_prefix}fhir-api"
  description = "FHIR API Gateway for HealthLake"
}

# Recurso y métodos para mapper-fhir
resource "aws_api_gateway_resource" "mapper_fhir" {
  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  parent_id   = aws_api_gateway_rest_api.fhir_api.root_resource_id
  path_part   = "${local.route_prefix}mapper-fhir"
}

resource "aws_api_gateway_method" "mapper_fhir_any" {
  rest_api_id   = aws_api_gateway_rest_api.fhir_api.id
  resource_id   = aws_api_gateway_resource.mapper_fhir.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "mapper_fhir_lambda" {
  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  resource_id = aws_api_gateway_resource.mapper_fhir.id
  http_method = aws_api_gateway_method.mapper_fhir_any.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.mapper_fhir.invoke_arn
}

resource "aws_api_gateway_method" "mapper_fhir_options" {
  rest_api_id   = aws_api_gateway_rest_api.fhir_api.id
  resource_id   = aws_api_gateway_resource.mapper_fhir.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "mapper_fhir_options" {
  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  resource_id = aws_api_gateway_resource.mapper_fhir.id
  http_method = aws_api_gateway_method.mapper_fhir_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "mapper_fhir_options" {
  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  resource_id = aws_api_gateway_resource.mapper_fhir.id
  http_method = aws_api_gateway_method.mapper_fhir_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "mapper_fhir_options" {
  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  resource_id = aws_api_gateway_resource.mapper_fhir.id
  http_method = aws_api_gateway_method.mapper_fhir_options.http_method
  status_code = aws_api_gateway_method_response.mapper_fhir_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# Permiso para API Gateway invocar mapper-fhir
resource "aws_lambda_permission" "mapper_fhir_api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.mapper_fhir.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.fhir_api.execution_arn}/*/*"
}

# Deployment
resource "aws_api_gateway_deployment" "fhir_api" {
  depends_on = [
    aws_api_gateway_integration.mapper_fhir_lambda
  ]

  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  stage_name  = var.environment
}
