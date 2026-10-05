output "raw_pdf_bucket" {
  description = "GCS bucket name for raw PDFs"
  value       = google_storage_bucket.raw_pdfs.name
}

output "parsed_md_bucket" {
  description = "GCS bucket name for parsed Markdown"
  value       = google_storage_bucket.parsed_md.name
}

output "db_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "db_public_ip" {
  description = "Cloud SQL public IP address"
  value       = google_sql_database_instance.postgres.first_ip_address
}

output "db_user" {
  description = "Database admin user"
  value       = google_sql_user.users.name
}

output "db_password" {
  description = "Database admin password"
  value       = random_password.db_password.result
  sensitive   = true
}

