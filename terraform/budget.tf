# GCP Billing Budget Alert (Cap under ₹26,000 / ~$300 USD)
resource "google_billing_budget" "budget_alert" {
  count           = var.billing_account_id != "" ? 1 : 0
  billing_account = var.billing_account_id
  display_name    = "LIC RAG Production Budget Alert (Cap ₹26,000)"

  budget_filter {
    projects = ["projects/${var.project_id}"]
  }

  amount {
    specified_amount {
      currency_code = "INR"
      units         = "26000"
    }
  }

  threshold_rules {
    threshold_percent = 0.5 # 50% (₹13,000)
  }

  threshold_rules {
    threshold_percent = 0.8 # 80% (₹20,800)
  }

  threshold_rules {
    threshold_percent = 1.0 # 100% (₹26,000)
    spend_basis       = "CURRENT_SPEND"
  }

  all_updates_rule {
    monitoring_notification_channels = []
    disable_default_iam_recipients   = false
  }
}
