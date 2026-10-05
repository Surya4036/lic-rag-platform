# Cloud Run Ingestion Worker Service
resource "google_cloud_run_v2_service" "ingestion_worker" {
  name     = "lic-rag-ingestion-${var.environment}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    containers {
      image = "gcr.io/${var.project_id}/ingestion-worker:latest"

      resources {
        limits = {
          cpu    = "1000m"
          memory = "1024Mi"
        }
      }

      env {
        name  = "RAW_PDF_BUCKET"
        value = google_storage_bucket.raw_pdfs.name
      }

      env {
        name  = "PARSED_MD_BUCKET"
        value = google_storage_bucket.parsed_md.name
      }
    }
  }
}

# Cloud Run RAG API & Chat UI Service
resource "google_cloud_run_v2_service" "rag_api" {
  name     = "lic-rag-api-${var.environment}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    containers {
      image = "gcr.io/${var.project_id}/rag-api:latest"

      resources {
        limits = {
          cpu    = "1000m"
          memory = "512Mi"
        }
      }

      env {
        name  = "DB_HOST"
        value = google_sql_database_instance.postgres.public_ip_address
      }

      env {
        name  = "DB_NAME"
        value = google_sql_database.database.name
      }
    }
  }
}
