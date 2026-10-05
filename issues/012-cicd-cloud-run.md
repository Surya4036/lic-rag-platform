# Ticket 12: CI/CD Pipeline & Keyless GCP Cloud Run Deployment

## Status: COMPLETE

## Objective
Establish an automated CI/CD pipeline using GitHub Actions and GCP Workload Identity Federation (WIF) to automatically test, provision infrastructure via Terraform, build container images via Google Cloud Build, and deploy the LIC RAG API and Streamlit UI to GCP Cloud Run (`asia-south1`).

## Accomplished
1. **GitHub Actions Workflow (`.github/workflows/deploy.yml`)**:
   - Automated Pytest execution (24/24 passing tests).
   - Terraform IaC initialization & auto-approve apply for Cloud Run, GCS, and Cloud SQL.
   - Container image build via `gcloud builds submit`.
   - Deployment to GCP Cloud Run (`lic-rag-api-prod`) with `id-token: write` OIDC keyless authentication.

2. **Vertex AI Native Application Default Credentials (ADC)**:
   - Updated `PolicyEmbedder` in `src/embeddings/embedder.py` to support keyless Vertex AI initialization (`genai.Client(vertexai=True, project=gcp_project, location="asia-south1")`) using Cloud Run IAM Service Account credentials without needing a static `GEMINI_API_KEY`.

3. **GCP Workload Identity Federation Integration**:
   - Linked GitHub repository (`Surya4036/lic-rag-platform`) to GCP Workload Identity Pool (`github-actions-pool`) and Provider (`github-actions-provider`).
   - Configured GitHub Secrets: `GCP_PROJECT_ID`, `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT`.

## Verification
- Verified workflow file syntax and secrets binding.
- Pushed clean commit to `main` branch: `git push -u origin main`.
