## Decision: Terraform IaC Structure

**Selected Approach**: Modular Terraform Structure with GCS Backend.

### Layout
```
terraform/
├── provider.tf          # GCP Provider configuration & GCS backend definition
├── variables.tf         # Input variable definitions (project_id, region, env)
├── terraform.tfvars.example # Example environment variables
├── gcs.tf               # Cloud Storage buckets (raw PDFs, parsed markdown)
├── db.tf                # Cloud SQL PostgreSQL + pgvector instance & database
├── cloud_run.tf         # Cloud Run services (ingestion worker, API service)
├── budget.tf            # Billing budget alert (Max ₹26,000 / ~$300 USD threshold)
└── outputs.tf           # Output resource URIs, bucket names, DB connection strings
```

### Rationale
- **Maintainability**: Keeps database, storage, compute, and budget alerts decoupled.
- **State Safety**: GCS backend ensures remote state locking and persistence across developer environments.
- **Budget Control**: Dedicated `budget.tf` enforces our strict ₹26,000 budget cap with email notifications at 50%, 80%, and 100% threshold consumption.
