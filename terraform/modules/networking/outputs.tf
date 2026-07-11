output "vpc_id" {
  description = "The ID of the VPC/VNet"
  value = (
    var.cloud_provider == "aws" ? aws_vpc.main[0].id :
    var.cloud_provider == "azure" ? azurerm_virtual_network.main[0].id :
    var.cloud_provider == "gcp" ? google_compute_network.main[0].id :
    null
  )
}

output "subnet_ids" {
  description = "List of subnet IDs"
  value = (
    var.cloud_provider == "aws" ? concat(aws_subnet.public[*].id, aws_subnet.private[*].id) :
    var.cloud_provider == "azure" ? [
      azurerm_subnet.public[0].id,
      azurerm_subnet.app[0].id,
      azurerm_subnet.data[0].id
    ] :
    var.cloud_provider == "gcp" ? [
      google_compute_subnetwork.public[0].id,
      google_compute_subnetwork.app[0].id,
      google_compute_subnetwork.data[0].id
    ] :
    []
  )
}

output "vpc_cidr" {
  description = "The CIDR block of the VPC"
  value       = var.vpc_cidr
}

output "resource_group_name" {
  description = "Azure Resource Group name (Azure only)"
  value       = var.cloud_provider == "azure" ? azurerm_resource_group.networking[0].name : null
}
