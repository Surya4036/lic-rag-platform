# GCS Bucket for Raw PDF Brochures
resource "google_storage_bucket" "raw_pdfs" {
  name                     = "lic-rag-raw-pdfs-${var.environment}"
  location                 = var.region
  force_destroy            = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      num_newer_versions = 3
    }
  }
}

# GCS Bucket for Parsed Markdown Archives
resource "google_storage_bucket" "parsed_md" {
  name                     = "lic-rag-parsed-md-${var.environment}"
  location                 = var.region
  force_destroy            = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}
