variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "gke_node_type" {
  description = "GKE node machine type"
  type        = string
  default     = "e2-medium"
}

variable "node_count" {
  description = "Number of GKE nodes"
  type        = number
  default     = 3
}

variable "db_instance_class" {
  description = "Cloud SQL tier"
  type        = string
  default     = "db-f1-micro"
}

variable "db_allocated_storage" {
  description = "Cloud SQL storage in GB"
  type        = number
  default     = 50
}

variable "db_password" {
  description = "Database admin password"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Additional labels"
  type        = map(string)
  default     = {}
}
