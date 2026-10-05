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
    threshold_percent = 0.25 # 25% (₹6,500)
  }

  threshold_rules {
    threshold_percent = 0.50 # 50% (₹13,000)
  }

  threshold_rules {
    threshold_percent = 0.75 # 75% (₹19,500)
  }

  threshold_rules {
    threshold_percent = 1.00 # 100% (₹26,000)
    spend_basis       = "CURRENT_SPEND"
  }

  all_updates_rule {
    monitoring_notification_channels = var.alert_email != "" ? [google_monitoring_notification_channel.email_alert[0].id] : []
    disable_default_iam_recipients   = false
  }
}

resource "google_monitoring_notification_channel" "email_alert" {
  count        = var.alert_email != "" ? 1 : 0
  display_name = "LIC RAG Budget Alert Email Channel"
  type         = "email"
  project      = var.project_id

  labels = {
    email_address = var.alert_email
  }
}
