output "vpc_id" {
  description = "AWS VPC ID"
  value       = module.networking.vpc_id
}

output "subnet_ids" {
  description = "AWS Subnet IDs"
  value       = module.networking.subnet_ids
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.kubernetes.cluster_endpoint
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.kubernetes.cluster_name
}

output "database_host" {
  description = "RDS database host"
  value       = module.database.host
}

output "database_port" {
  description = "RDS database port"
  value       = module.database.port
}

output "kubeconfig_command" {
  description = "Command to configure kubectl"
  value       = module.kubernetes.kubeconfig_command
}
