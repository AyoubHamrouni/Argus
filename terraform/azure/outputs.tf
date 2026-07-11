output "vpc_id" {
  description = "Azure VNet ID"
  value       = module.networking.vpc_id
}

output "subnet_ids" {
  description = "Azure Subnet IDs"
  value       = module.networking.subnet_ids
}

output "aks_cluster_endpoint" {
  description = "AKS cluster endpoint"
  value       = module.kubernetes.cluster_endpoint
}

output "aks_cluster_name" {
  description = "AKS cluster name"
  value       = module.kubernetes.cluster_name
}

output "database_host" {
  description = "PostgreSQL server FQDN"
  value       = module.database.host
}

output "database_port" {
  description = "PostgreSQL port"
  value       = module.database.port
}

output "kubeconfig_command" {
  description = "Command to configure kubectl"
  value       = module.kubernetes.kubeconfig_command
}
