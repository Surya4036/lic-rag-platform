output "raw_pdf_bucket" {
  description = "GCS bucket name for raw PDFs"
  value       = google_storage_bucket.raw_pdfs.name
}

output "parsed_md_bucket" {
  description = "GCS bucket name for parsed Markdown"
  value       = google_storage_bucket.parsed_md.name
}
