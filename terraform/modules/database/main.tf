locals {
  name_prefix = "ai-soc-${var.environment}"
  is_prod     = var.environment == "prod"
}

# =============================================================================
# AWS RDS PostgreSQL
# =============================================================================
resource "aws_db_subnet_group" "main" {
  count      = var.cloud_provider == "aws" ? 1 : 0
  name       = "${local.name_prefix}-db-subnet"
  subnet_ids = var.subnet_ids

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-db-subnet-group"
  })
}

resource "aws_security_group" "database" {
  count       = var.cloud_provider == "aws" ? 1 : 0
  name        = "${local.name_prefix}-database-sg"
  description = "Security group for RDS database"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = []
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-database-sg"
  })
}

resource "aws_db_instance" "main" {
  count                  = var.cloud_provider == "aws" ? 1 : 0
  identifier             = "${local.name_prefix}-postgres"
  engine                 = "postgres"
  engine_version         = "15.4"
  instance_class         = var.db_instance_class
  allocated_storage      = var.db_allocated_storage
  max_allocated_storage  = local.is_prod ? var.db_allocated_storage * 2 : null
  db_name                = var.db_name
  username               = var.db_user
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.main[0].name
  vpc_security_group_ids = [aws_security_group.database[0].id]
  skip_final_snapshot    = !local.is_prod
  final_snapshot_identifier = local.is_prod ? "${local.name_prefix}-final-snapshot" : null
  deletion_protection    = local.is_prod
  multi_az               = local.is_prod
  storage_encrypted      = true

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  tags = merge(var.tags, {
    Name        = "${local.name_prefix}-postgres"
    Environment = var.environment
  })
}

# =============================================================================
# Azure Database for PostgreSQL
# =============================================================================
resource "azurerm_resource_group" "database" {
  count    = var.cloud_provider == "azure" ? 1 : 0
  name     = "${local.name_prefix}-database-rg"
  location = "East US"

  tags = var.tags
}

resource "azurerm_postgresql_flexible_server" "main" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${local.name_prefix}-postgres"
  resource_group_name = azurerm_resource_group.database[0].name
  location            = azurerm_resource_group.database[0].location
  administrator_login    = var.db_user
  administrator_password = var.db_password
  sku_name            = local.is_prod ? "GP_Gen5_2" : "B_Gen5_1"
  storage_mb          = var.db_allocated_storage * 1024
  version             = "15"

  backup_retention_days        = 7
  geo_redundant_backup_enabled = local.is_prod
  zone                         = "1"

  tags = merge(var.tags, {
    Name        = "${local.name_prefix}-postgres"
    Environment = var.environment
  })
}

resource "azurerm_postgresql_flexible_server_database" "main" {
  count     = var.cloud_provider == "azure" ? 1 : 0
  name      = var.db_name
  server_id = azurerm_postgresql_flexible_server.main[0].id
  charset   = "utf8"
  collation = "en_US.utf8"
}

# =============================================================================
# GCP Cloud SQL PostgreSQL
# =============================================================================
resource "google_sql_database_instance" "main" {
  count              = var.cloud_provider == "gcp" ? 1 : 0
  name               = "${local.name_prefix}-postgres"
  database_version   = "POSTGRES_15"
  region             = var.gcp_region

  settings {
    tier              = local.is_prod ? "db-custom-2-4096" : "db-f1-micro"
    availability_type = local.is_prod ? "REGIONAL" : "ZONAL"
    disk_size         = var.db_allocated_storage
    disk_type         = "PD_SSD"

    backup_configuration {
      enabled          = true
      start_time       = "03:00"
      point_in_time_recovery_enabled = true
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.vpc_id
    }

    maintenance_window {
      day  = 1
      hour = 4
    }
  }

  deletion_protection = local.is_prod
}

resource "google_sql_database" "main" {
  count    = var.cloud_provider == "gcp" ? 1 : 0
  name     = var.db_name
  instance = google_sql_database_instance.main[0].name
}

resource "google_sql_user" "main" {
  count    = var.cloud_provider == "gcp" ? 1 : 0
  name     = var.db_user
  instance = google_sql_database_instance.main[0].name
  password = var.db_password
}
