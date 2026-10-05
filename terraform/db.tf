# Cloud SQL PostgreSQL Instance (pgvector support)
resource "google_sql_database_instance" "postgres" {
  name             = "lic-rag-db-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = "db-f1-micro" # Lowest cost instance under free/budget tier
    availability_type = "ZONAL"

    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }

    ip_configuration {
      ipv4_enabled = true
    }
  }

  deletion_protection = false
}

# Database definition
resource "google_sql_database" "database" {
  name     = "lic_rag_db"
  instance = google_sql_database_instance.postgres.name
}

# Random password for DB user
resource "random_password" "db_password" {
  length  = 16
  special = false
}

# DB Admin User
resource "google_sql_user" "users" {
  name     = "lic_admin"
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}
