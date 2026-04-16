resource "google_billing_budget" "project_cap" {
  billing_account = var.billing_account_id
  display_name    = "Emotion Vision monthly cap"

  budget_filter {
    projects        = ["projects/${var.project_id}"]
    calendar_period = "MONTH"
  }

  amount {
    specified_amount {
      currency_code = var.currency_code
      units         = tostring(var.monthly_budget_amount)
    }
  }

  threshold_rules {
    threshold_percent = 0.5
    spend_basis       = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 0.9
    spend_basis       = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "CURRENT_SPEND"
  }

  # Default IAM recipients (billing admins on the billing account) receive
  # email alerts automatically. Attaching monitoring_notification_channels
  # requires Pub/Sub wiring per GCP; skipped here for simplicity.
}
