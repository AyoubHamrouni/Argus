variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "azure_region" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

variable "vpc_cidr" {
  description = "VNet CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "aks_node_type" {
  description = "AKS node VM size"
  type        = string
  default     = "Standard_D2s_v3"
}

variable "node_count" {
  description = "Number of AKS nodes"
  type        = number
  default     = 3
}

variable "db_instance_class" {
  description = "PostgreSQL SKU name"
  type        = string
  default     = "B_Gen5_1"
}

variable "db_allocated_storage" {
  description = "PostgreSQL storage in MB"
  type        = number
  default     = 51200
}

variable "db_password" {
  description = "Database admin password"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
