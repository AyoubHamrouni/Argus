locals {
  common_tags = merge(var.tags, {
    Project     = "Argus"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Cloud       = "GCP"
  })
}

module "networking" {
  source         = "../modules/networking"
  cloud_provider = "gcp"
  environment    = var.environment
  vpc_cidr       = var.vpc_cidr
  tags           = local.common_tags

  # GCP-specific variables
  gcp_region = var.gcp_region
}

module "database" {
  source               = "../modules/database"
  cloud_provider       = "gcp"
  environment          = var.environment
  vpc_id               = module.networking.vpc_id
  subnet_ids           = module.networking.subnet_ids
  db_password          = var.db_password
  db_instance_class    = var.db_instance_class
  db_allocated_storage = var.db_allocated_storage
  gcp_region           = var.gcp_region
  tags                 = local.common_tags
}

module "kubernetes" {
  source         = "../modules/kubernetes"
  cloud_provider = "gcp"
  environment    = var.environment
  vpc_id         = module.networking.vpc_id
  subnet_ids     = module.networking.subnet_ids
  node_count     = var.node_count
  node_type      = var.gke_node_type
  gcp_region     = var.gcp_region
  tags           = local.common_tags
}
