# Argus Terraform Infrastructure

Multi-cloud Terraform modules for deploying the Argus platform across AWS, Azure, and GCP.

## Structure

```
terraform/
├── modules/
│   ├── networking/    # VPC/VNet, subnets, NAT, routing
│   ├── database/      # PostgreSQL (RDS/Cloud SQL/Azure DB)
│   └── kubernetes/    # EKS/AKS/GKE clusters
├── aws/               # AWS deployment
├── azure/             # Azure deployment
└── gcp/               # GCP deployment
```

## Quick Start

### AWS

```bash
cd terraform/aws
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

### Azure

```bash
cd terraform/azure
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

### GCP

```bash
cd terraform/gcp
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

## Prerequisites

- Terraform >= 1.0
- Provider credentials configured:
  - **AWS**: `aws configure` or environment variables
  - **Azure**: `az login` or service principal
  - **GCP**: `gcloud auth application-default login`

## Backend Configuration

Each cloud provider uses its native state backend:

| Provider | Backend | State Key |
|----------|---------|-----------|
| AWS | S3 + DynamoDB | `aws/terraform.tfstate` |
| Azure | Blob Storage | `azure/terraform.tfstate` |
| GCP | GCS Bucket | `gcp/terraform.tfstate` |

Update `backend.tf` in each cloud directory with your bucket/container names.

## Resources Created

### Networking
- VPC/VNet with public and private subnets
- Internet Gateway / NAT Gateway
- Route tables and associations
- Security groups / NSGs / Firewall rules

### Database
- PostgreSQL 15 (managed)
- Automated backups (7-day retention)
- Encryption at rest
- Production: multi-AZ/geo-redundant with deletion protection

### Kubernetes
- Managed Kubernetes cluster (EKS/AKS/GKE)
- Auto-scaling node pools
- Private networking enabled

## Environment Differences

| Setting | Dev | Staging | Prod |
|---------|-----|---------|------|
| DB Multi-AZ | No | No | Yes |
| DB Deletion Protection | No | No | Yes |
| Node Count | 3 | 3 | 5 |
| DB Backup Retention | 7 days | 7 days | 7 days |

## Security Notes

- Never commit `terraform.tfvars` files
- Use environment variables or secret managers for passwords
- Enable remote state encryption
- Use IAM roles/service principals instead of static credentials
