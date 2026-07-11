variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "cloud_provider" {
  description = "Cloud provider (aws, azure, gcp)"
  type        = string
}

variable "vpc_id" {
  description = "VPC/VNet ID"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs"
  type        = list(string)
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "ai_soc"
}

variable "db_user" {
  description = "Database admin user"
  type        = string
  default     = "aisoc_admin"
}

variable "db_password" {
  description = "Database admin password"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "Database instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 50
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "gcp_region" {
  description = "GCP region (only for GCP)"
  type        = string
  default     = "us-central1"
}

variable "azure_resource_group_name" {
  description = "Azure Resource Group name (only for Azure)"
  type        = string
  default     = ""
}
