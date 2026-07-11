output "vpc_id" {
  description = "GCP VPC ID"
  value       = module.networking.vpc_id
}

output "subnet_ids" {
  description = "GCP Subnet IDs"
  value       = module.networking.subnet_ids
}

output "gke_cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = module.kubernetes.cluster_endpoint
}

output "gke_cluster_name" {
  description = "GKE cluster name"
  value       = module.kubernetes.cluster_name
}

output "database_host" {
  description = "Cloud SQL IP address"
  value       = module.database.host
}

output "database_port" {
  description = "Cloud SQL port"
  value       = module.database.port
}

output "kubeconfig_command" {
  description = "Command to configure kubectl"
  value       = module.kubernetes.kubeconfig_command
}
