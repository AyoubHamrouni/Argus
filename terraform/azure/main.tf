locals {
  common_tags = merge(var.tags, {
    Project     = "Argus"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Cloud       = "Azure"
  })
}

module "networking" {
  source         = "../modules/networking"
  cloud_provider = "azure"
  environment    = var.environment
  vpc_cidr       = var.vpc_cidr
  tags           = local.common_tags
}

module "database" {
  source                  = "../modules/database"
  cloud_provider          = "azure"
  environment             = var.environment
  vpc_id                  = module.networking.vpc_id
  subnet_ids              = module.networking.subnet_ids
  db_password             = var.db_password
  db_instance_class       = var.db_instance_class
  db_allocated_storage    = var.db_allocated_storage
  azure_resource_group_name = module.networking.resource_group_name
  tags                    = local.common_tags
}

module "kubernetes" {
  source                  = "../modules/kubernetes"
  cloud_provider          = "azure"
  environment             = var.environment
  vpc_id                  = module.networking.vpc_id
  subnet_ids              = module.networking.subnet_ids
  node_count              = var.node_count
  node_type               = var.aks_node_type
  azure_resource_group_name = module.networking.resource_group_name
  tags                    = local.common_tags
}
