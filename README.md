# FHIR-INFRAESTRUCTURA

## Estructura del Proyecto

```
.
├── bootstrap/              # Infraestructura inicial (ejecutar solo una vez)
│   └── main.tf            # Bucket S3 y rol IAM para GitHub Actions
├── environments/
│   ├── dev/               # Configuración ambiente desarrollo
│   │   └── main.tf
│   └── prod/              # Configuración ambiente producción
│       └── main.tf
└── modules/
    └── infrastructure/    # Módulo reutilizable de infraestructura
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

## Configuración Inicial (Una sola vez)

```bash
# 1. Crear recursos compartidos (bucket S3 y rol IAM)
cd bootstrap
terraform init
terraform apply

# 2. Copiar el ARN del rol y agregarlo como secreto en GitHub
terraform output github_actions_role_arn
```

## Despliegue por Ambiente

### Desarrollo (rama dev)
```bash
cd environments/dev
terraform init
terraform plan
terraform apply
```

### Producción (rama main)
```bash
cd environments/prod
terraform init
terraform plan
terraform apply
```

## CI/CD

- Push a `dev` → despliega ambiente dev automáticamente
- Push a `main` → despliega ambiente prod automáticamente

## Separación de Ambientes

- Estados separados: `dev/terraform.tfstate` y `prod/terraform.tfstate`
- Recursos con prefijo: `dev-recurso` vs `recurso`
- Configuraciones independientes por directorio
