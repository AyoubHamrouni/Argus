locals {
  name_prefix = "argus-${var.environment}"
}

# =============================================================================
# AWS EKS
# =============================================================================
resource "aws_iam_role" "eks_cluster" {
  count = var.cloud_provider == "aws" ? 1 : 0
  name  = "${local.name_prefix}-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  count      = var.cloud_provider == "aws" ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster[0].name
}

resource "aws_eks_cluster" "main" {
  count    = var.cloud_provider == "aws" ? 1 : 0
  name     = "${local.name_prefix}-eks"
  role_arn = aws_iam_role.eks_cluster[0].arn
  version  = "1.28"

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_private_access = true
    endpoint_public_access  = true
  }

  depends_on = [aws_iam_role_policy_attachment.eks_cluster_policy[0]]

  tags = merge(var.tags, {
    Name        = "${local.name_prefix}-eks"
    Environment = var.environment
  })
}

resource "aws_iam_role" "eks_nodes" {
  count = var.cloud_provider == "aws" ? 1 : 0
  name  = "${local.name_prefix}-eks-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  count      = var.cloud_provider == "aws" ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodes[0].name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  count      = var.cloud_provider == "aws" ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_nodes[0].name
}

resource "aws_iam_role_policy_attachment" "eks_ecr_policy" {
  count      = var.cloud_provider == "aws" ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_nodes[0].name
}

resource "aws_eks_node_group" "main" {
  count           = var.cloud_provider == "aws" ? 1 : 0
  cluster_name    = aws_eks_cluster.main[0].name
  node_group_name = "${local.name_prefix}-nodes"
  node_role_arn   = aws_iam_role.eks_nodes[0].arn
  subnet_ids      = var.subnet_ids
  instance_types  = [var.node_type]

  scaling_config {
    desired_size = var.node_count
    max_size     = var.node_count + 2
    min_size     = 1
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy[0],
    aws_iam_role_policy_attachment.eks_cni_policy[0],
    aws_iam_role_policy_attachment.eks_ecr_policy[0],
  ]

  tags = merge(var.tags, {
    Name        = "${local.name_prefix}-eks-nodes"
    Environment = var.environment
  })
}

# =============================================================================
# Azure AKS
# =============================================================================
resource "azurerm_resource_group" "kubernetes" {
  count    = var.cloud_provider == "azure" ? 1 : 0
  name     = "${local.name_prefix}-kubernetes-rg"
  location = "East US"

  tags = var.tags
}

resource "azurerm_kubernetes_cluster" "main" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${local.name_prefix}-aks"
  location            = azurerm_resource_group.kubernetes[0].location
  resource_group_name = azurerm_resource_group.kubernetes[0].name
  dns_prefix          = "${local.name_prefix}-aks"
  kubernetes_version  = "1.28"

  default_node_pool {
    name                = "default"
    node_count          = var.node_count
    vm_size             = var.node_type
    vnet_subnet_id      = var.subnet_ids[0]
    enable_auto_scaling = true
    min_count           = 1
    max_count           = var.node_count + 2
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin = "azure"
    network_policy = "calico"
  }

  tags = merge(var.tags, {
    Name        = "${local.name_prefix}-aks"
    Environment = var.environment
  })
}

# =============================================================================
# GCP GKE
# =============================================================================
resource "google_container_cluster" "main" {
  count              = var.cloud_provider == "gcp" ? 1 : 0
  name               = "${local.name_prefix}-gke"
  location           = var.gcp_region
  min_master_version = "1.28"

  network    = var.vpc_id
  subnetwork = var.subnet_ids[0]

  remove_default_node_pool = true
  initial_node_count       = 1

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  resource_labels = merge(var.tags, {
    environment = var.environment
  })
}

resource "google_container_node_pool" "main" {
  count      = var.cloud_provider == "gcp" ? 1 : 0
  name       = "${local.name_prefix}-node-pool"
  cluster    = google_container_cluster.main[0].name
  location   = var.gcp_region
  node_count = var.node_count

  node_config {
    machine_type = var.node_type
    disk_size_gb = 50
    disk_type    = "pd-ssd"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]

    labels = merge(var.tags, {
      environment = var.environment
    })
  }

  autoscaling {
    min_node_count = 1
    max_node_count = var.node_count + 2
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}
