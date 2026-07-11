output "connection_string" {
  description = "Database connection string"
  sensitive   = true
  value = (
    var.cloud_provider == "aws" ? "postgresql://${var.db_user}:${var.db_password}@${aws_db_instance.main[0].endpoint}/${var.db_name}" :
    var.cloud_provider == "azure" ? "postgresql://${var.db_user}:${var.db_password}@${azurerm_postgresql_flexible_server.main[0].fqdn}/${var.db_name}?sslmode=require" :
    var.cloud_provider == "gcp" ? "postgresql://${var.db_user}:${var.db_password}@/${var.db_name}?host=/cloudsql/${google_sql_database_instance.main[0].connection_name}" :
    null
  )
}

output "host" {
  description = "Database host"
  value = (
    var.cloud_provider == "aws" ? aws_db_instance.main[0].address :
    var.cloud_provider == "azure" ? azurerm_postgresql_flexible_server.main[0].fqdn :
    var.cloud_provider == "gcp" ? google_sql_database_instance.main[0].first_ip_address :
    null
  )
}

output "port" {
  description = "Database port"
  value       = 5432
}

output "db_name" {
  description = "Database name"
  value       = var.db_name
}
