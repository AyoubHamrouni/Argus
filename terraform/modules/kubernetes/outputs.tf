output "cluster_endpoint" {
  description = "Kubernetes cluster endpoint"
  value = (
    var.cloud_provider == "aws" ? aws_eks_cluster.main[0].endpoint :
    var.cloud_provider == "azure" ? azurerm_kubernetes_cluster.main[0].kube_config[0].host :
    var.cloud_provider == "gcp" ? "https://${google_container_cluster.main[0].endpoint}" :
    null
  )
}

output "cluster_ca_certificate" {
  description = "Cluster CA certificate (base64)"
  sensitive   = true
  value = (
    var.cloud_provider == "aws" ? aws_eks_cluster.main[0].certificate_authority[0].data :
    var.cloud_provider == "azure" ? azurerm_kubernetes_cluster.main[0].kube_config[0].cluster_ca_certificate :
    var.cloud_provider == "gcp" ? google_container_cluster.main[0].master_auth[0].cluster_ca_certificate :
    null
  )
}

output "cluster_name" {
  description = "Kubernetes cluster name"
  value = (
    var.cloud_provider == "aws" ? aws_eks_cluster.main[0].name :
    var.cloud_provider == "azure" ? azurerm_kubernetes_cluster.main[0].name :
    var.cloud_provider == "gcp" ? google_container_cluster.main[0].name :
    null
  )
}

output "kubeconfig_command" {
  description = "Command to configure kubectl"
  value = (
    var.cloud_provider == "aws" ? "aws eks update-kubeconfig --region ${var.gcp_region} --name ${aws_eks_cluster.main[0].name}" :
    var.cloud_provider == "azure" ? "az aks get-credentials --resource-group ${var.azure_resource_group_name} --name ${azurerm_kubernetes_cluster.main[0].name}" :
    var.cloud_provider == "gcp" ? "gcloud container clusters get-credentials ${google_container_cluster.main[0].name} --region ${var.gcp_region} --project ${var.project_id}" :
    null
  )
}
