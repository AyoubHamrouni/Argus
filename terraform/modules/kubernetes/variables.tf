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

variable "node_count" {
  description = "Number of nodes in the node pool"
  type        = number
  default     = 3
}

variable "node_type" {
  description = "Node instance type"
  type        = string
  default     = "t3.medium"
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
