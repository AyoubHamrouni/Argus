locals {
  name_prefix = "ai-soc-${var.environment}"
}

# =============================================================================
# AWS Networking
# =============================================================================
resource "aws_vpc" "main" {
  count                = var.cloud_provider == "aws" ? 1 : 0
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.tags, {
    Name        = "${local.name_prefix}-vpc"
    Environment = var.environment
  })
}

resource "aws_internet_gateway" "main" {
  count  = var.cloud_provider == "aws" ? 1 : 0
  vpc_id = aws_vpc.main[0].id

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-igw"
  })
}

resource "aws_subnet" "public" {
  count                   = var.cloud_provider == "aws" ? 2 : 0
  vpc_id                  = aws_vpc.main[0].id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available[0].names[count.index]
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-public-${count.index + 1}"
    Tier = "public"
  })
}

resource "aws_subnet" "private" {
  count             = var.cloud_provider == "aws" ? 2 : 0
  vpc_id            = aws_vpc.main[0].id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = data.aws_availability_zones.available[0].names[count.index]

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-private-${count.index + 1}"
    Tier = "private"
  })
}

resource "aws_eip" "nat" {
  count  = var.cloud_provider == "aws" ? 1 : 0
  domain = "vpc"

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-nat-eip"
  })
}

resource "aws_nat_gateway" "main" {
  count         = var.cloud_provider == "aws" ? 1 : 0
  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-nat"
  })
}

resource "aws_route_table" "public" {
  count  = var.cloud_provider == "aws" ? 1 : 0
  vpc_id = aws_vpc.main[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main[0].id
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-public-rt"
  })
}

resource "aws_route_table" "private" {
  count  = var.cloud_provider == "aws" ? 1 : 0
  vpc_id = aws_vpc.main[0].id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[0].id
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-private-rt"
  })
}

resource "aws_route_table_association" "public" {
  count          = var.cloud_provider == "aws" ? 2 : 0
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}

resource "aws_route_table_association" "private" {
  count          = var.cloud_provider == "aws" ? 2 : 0
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[0].id
}

data "aws_availability_zones" "available" {
  count = var.cloud_provider == "aws" ? 1 : 0
  state = "available"
}

# =============================================================================
# Azure Networking
# =============================================================================
resource "azurerm_resource_group" "networking" {
  count    = var.cloud_provider == "azure" ? 1 : 0
  name     = "${local.name_prefix}-networking-rg"
  location = "East US"

  tags = var.tags
}

resource "azurerm_virtual_network" "main" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${local.name_prefix}-vnet"
  address_space       = [var.vpc_cidr]
  location            = azurerm_resource_group.networking[0].location
  resource_group_name = azurerm_resource_group.networking[0].name

  tags = var.tags
}

resource "azurerm_subnet" "public" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${local.name_prefix}-public-subnet"
  resource_group_name = azurerm_resource_group.networking[0].name
  virtual_network_name = azurerm_virtual_network.main[0].name
  address_prefixes    = [cidrsubnet(var.vpc_cidr, 8, 0)]
}

resource "azurerm_subnet" "app" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${local.name_prefix}-app-subnet"
  resource_group_name = azurerm_resource_group.networking[0].name
  virtual_network_name = azurerm_virtual_network.main[0].name
  address_prefixes    = [cidrsubnet(var.vpc_cidr, 8, 1)]
}

resource "azurerm_subnet" "data" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${local.name_prefix}-data-subnet"
  resource_group_name = azurerm_resource_group.networking[0].name
  virtual_network_name = azurerm_virtual_network.main[0].name
  address_prefixes    = [cidrsubnet(var.vpc_cidr, 8, 2)]
}

resource "azurerm_network_security_group" "main" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${local.name_prefix}-nsg"
  location            = azurerm_resource_group.networking[0].location
  resource_group_name = azurerm_resource_group.networking[0].name

  security_rule {
    name                       = "AllowSSH"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = var.tags
}

resource "azurerm_public_ip" "main" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${local.name_prefix}-pip"
  location            = azurerm_resource_group.networking[0].location
  resource_group_name = azurerm_resource_group.networking[0].name
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = var.tags
}

resource "azurerm_route_table" "main" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${local.name_prefix}-rt"
  location            = azurerm_resource_group.networking[0].location
  resource_group_name = azurerm_resource_group.networking[0].name

  route {
    name           = "default"
    address_prefix = "0.0.0.0/0"
    next_hop_type  = "Internet"
  }

  tags = var.tags
}

# =============================================================================
# GCP Networking
# =============================================================================
resource "google_compute_network" "main" {
  count                   = var.cloud_provider == "gcp" ? 1 : 0
  name                    = "${local.name_prefix}-vpc"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "public" {
  count         = var.cloud_provider == "gcp" ? 1 : 0
  name          = "${local.name_prefix}-public-subnet"
  ip_cidr_range = cidrsubnet(var.vpc_cidr, 8, 0)
  region        = var.gcp_region
  network       = google_compute_network.main[0].id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.1.0.0/16"
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.2.0.0/20"
  }
}

resource "google_compute_subnetwork" "app" {
  count         = var.cloud_provider == "gcp" ? 1 : 0
  name          = "${local.name_prefix}-app-subnet"
  ip_cidr_range = cidrsubnet(var.vpc_cidr, 8, 1)
  region        = var.gcp_region
  network       = google_compute_network.main[0].id
}

resource "google_compute_subnetwork" "data" {
  count         = var.cloud_provider == "gcp" ? 1 : 0
  name          = "${local.name_prefix}-data-subnet"
  ip_cidr_range = cidrsubnet(var.vpc_cidr, 8, 2)
  region        = var.gcp_region
  network       = google_compute_network.main[0].id
}

resource "google_compute_firewall" "allow_http" {
  count   = var.cloud_provider == "gcp" ? 1 : 0
  name    = "${local.name_prefix}-allow-http"
  network = google_compute_network.main[0].id

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["web-server"]
}

resource "google_compute_firewall" "allow_ssh" {
  count   = var.cloud_provider == "gcp" ? 1 : 0
  name    = "${local.name_prefix}-allow-ssh"
  network = google_compute_network.main[0].id

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["ssh-access"]
}

resource "google_compute_router" "main" {
  count   = var.cloud_provider == "gcp" ? 1 : 0
  name    = "${local.name_prefix}-router"
  region  = var.gcp_region
  network = google_compute_network.main[0].id
}

resource "google_compute_router_nat" "main" {
  count                              = var.cloud_provider == "gcp" ? 1 : 0
  name                               = "${local.name_prefix}-nat"
  router                             = google_compute_router.main[0].name
  region                             = var.gcp_region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}
