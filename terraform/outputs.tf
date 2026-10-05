output "raw_pdf_bucket" {
  description = "GCS bucket name for raw PDFs"
  value       = google_storage_bucket.raw_pdfs.name
}

output "parsed_md_bucket" {
  description = "GCS bucket name for parsed Markdown"
  value       = google_storage_bucket.parsed_md.name
}

output "database_public_ip" {
  description = "Public IP address of Cloud SQL instance"
  value       = google_sql_database_instance.postgres.public_ip_address
}

output "database_name" {
  description = "Database name"
  value       = google_sql_database.database.name
}

output "cloud_run_api_uri" {
  description = "Cloud Run RAG API service URI"
  value       = google_cloud_run_v2_service.rag_api.uri
}
