# Data source para obtener información del datastore de HealthLake
data "aws_healthlake_fhir_datastore" "main" {
  datastore_id = var.datastore_id
}

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

# Política para acceso a HealthLake
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
        Resource = data.aws_healthlake_fhir_datastore.main.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Archivos ZIP para las Lambdas
data "archive_file" "patient_lambda" {
  type        = "zip"
  source_file = "${path.module}/lambda_functions/patient/handler.py"
  output_path = "${path.module}/lambda_functions/patient.zip"
}

data "archive_file" "professional_lambda" {
  type        = "zip"
  source_file = "${path.module}/lambda_functions/professional/handler.py"
  output_path = "${path.module}/lambda_functions/professional.zip"
}

data "archive_file" "organization_lambda" {
  type        = "zip"
  source_file = "${path.module}/lambda_functions/organization/handler.py"
  output_path = "${path.module}/lambda_functions/organization.zip"
}

data "archive_file" "location_lambda" {
  type        = "zip"
  source_file = "${path.module}/lambda_functions/location/handler.py"
  output_path = "${path.module}/lambda_functions/location.zip"
}

# Lambda Functions
resource "aws_lambda_function" "patient" {
  filename         = data.archive_file.patient_lambda.output_path
  function_name    = "${local.name_prefix}Lambda-Patient-Handler-Terraform"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handler.lambda_handler"
  source_code_hash = data.archive_file.patient_lambda.output_base64sha256
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

resource "aws_lambda_function" "professional" {
  filename         = data.archive_file.professional_lambda.output_path
  function_name    = "${local.name_prefix}Lambda-Professional-Handler-Terraform"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handler.lambda_handler"
  source_code_hash = data.archive_file.professional_lambda.output_base64sha256
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

resource "aws_lambda_function" "organization" {
  filename         = data.archive_file.organization_lambda.output_path
  function_name    = "${local.name_prefix}Lambda-Organization-Handler-Terraform"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handler.lambda_handler"
  source_code_hash = data.archive_file.organization_lambda.output_base64sha256
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

resource "aws_lambda_function" "location" {
  filename         = data.archive_file.location_lambda.output_path
  function_name    = "${local.name_prefix}Lambda-Location-Handler-Terraform"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handler.lambda_handler"
  source_code_hash = data.archive_file.location_lambda.output_base64sha256
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

# API Gateway REST API
resource "aws_api_gateway_rest_api" "fhir_api" {
  name        = "${local.name_prefix}fhir-api"
  description = "FHIR API Gateway for HealthLake"
}

# Recursos y métodos para Patient
resource "aws_api_gateway_resource" "patient" {
  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  parent_id   = aws_api_gateway_rest_api.fhir_api.root_resource_id
  path_part   = "${local.route_prefix}patient"
}

resource "aws_api_gateway_method" "patient_any" {
  rest_api_id   = aws_api_gateway_rest_api.fhir_api.id
  resource_id   = aws_api_gateway_resource.patient.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "patient_lambda" {
  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  resource_id = aws_api_gateway_resource.patient.id
  http_method = aws_api_gateway_method.patient_any.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.patient.invoke_arn
}

resource "aws_api_gateway_method" "patient_options" {
  rest_api_id   = aws_api_gateway_rest_api.fhir_api.id
  resource_id   = aws_api_gateway_resource.patient.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "patient_options" {
  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  resource_id = aws_api_gateway_resource.patient.id
  http_method = aws_api_gateway_method.patient_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "patient_options" {
  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  resource_id = aws_api_gateway_resource.patient.id
  http_method = aws_api_gateway_method.patient_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "patient_options" {
  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  resource_id = aws_api_gateway_resource.patient.id
  http_method = aws_api_gateway_method.patient_options.http_method
  status_code = aws_api_gateway_method_response.patient_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# Permisos para API Gateway invocar Lambdas
resource "aws_lambda_permission" "patient_api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.patient.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.fhir_api.execution_arn}/*/*"
}

# Recursos y métodos para Professional
resource "aws_api_gateway_resource" "professional" {
  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  parent_id   = aws_api_gateway_rest_api.fhir_api.root_resource_id
  path_part   = "${local.route_prefix}professional"
}

resource "aws_api_gateway_method" "professional_any" {
  rest_api_id   = aws_api_gateway_rest_api.fhir_api.id
  resource_id   = aws_api_gateway_resource.professional.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "professional_lambda" {
  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  resource_id = aws_api_gateway_resource.professional.id
  http_method = aws_api_gateway_method.professional_any.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.professional.invoke_arn
}

resource "aws_lambda_permission" "professional_api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.professional.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.fhir_api.execution_arn}/*/*"
}

# Recursos y métodos para Organization
resource "aws_api_gateway_resource" "organization" {
  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  parent_id   = aws_api_gateway_rest_api.fhir_api.root_resource_id
  path_part   = "${local.route_prefix}organization"
}

resource "aws_api_gateway_method" "organization_any" {
  rest_api_id   = aws_api_gateway_rest_api.fhir_api.id
  resource_id   = aws_api_gateway_resource.organization.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "organization_lambda" {
  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  resource_id = aws_api_gateway_resource.organization.id
  http_method = aws_api_gateway_method.organization_any.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.organization.invoke_arn
}

resource "aws_lambda_permission" "organization_api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.organization.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.fhir_api.execution_arn}/*/*"
}

# Recursos y métodos para Location
resource "aws_api_gateway_resource" "location" {
  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  parent_id   = aws_api_gateway_rest_api.fhir_api.root_resource_id
  path_part   = "${local.route_prefix}location"
}

resource "aws_api_gateway_method" "location_any" {
  rest_api_id   = aws_api_gateway_rest_api.fhir_api.id
  resource_id   = aws_api_gateway_resource.location.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "location_lambda" {
  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  resource_id = aws_api_gateway_resource.location.id
  http_method = aws_api_gateway_method.location_any.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.location.invoke_arn
}

resource "aws_lambda_permission" "location_api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.location.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.fhir_api.execution_arn}/*/*"
}

# Deployment
resource "aws_api_gateway_deployment" "fhir_api" {
  depends_on = [
    aws_api_gateway_integration.patient_lambda,
    aws_api_gateway_integration.professional_lambda,
    aws_api_gateway_integration.organization_lambda,
    aws_api_gateway_integration.location_lambda
  ]

  rest_api_id = aws_api_gateway_rest_api.fhir_api.id
  stage_name  = var.environment
}
