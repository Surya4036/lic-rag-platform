variable "project_id" {
  type        = string
  description = "GCP Project ID"
  default     = "lic-rag-prod"
}

variable "region" {
  type        = string
  description = "GCP Region for resources"
  default     = "asia-south1"
}

variable "environment" {
  type        = string
  description = "Deployment environment"
  default     = "prod"
}

variable "billing_account_id" {
  type        = string
  description = "GCP Billing Account ID for budget alerts"
  default     = ""
}

variable "alert_email" {
  type        = string
  description = "Email address for budget alerts"
  default     = "surya4036@gmail.com"
}
