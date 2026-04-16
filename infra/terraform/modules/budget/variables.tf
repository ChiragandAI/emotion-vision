variable "project_id" {
  description = "GCP project ID the budget scopes to"
  type        = string
}

variable "billing_account_id" {
  description = "Billing account ID without the 'billingAccounts/' prefix, e.g. 01BC1C-0D5977-F3C59C"
  type        = string
}

variable "monthly_budget_amount" {
  description = "Monthly budget cap in the billing account's native currency"
  type        = number
  default     = 2000
}

variable "currency_code" {
  description = "Currency code matching the billing account (e.g. INR, USD)"
  type        = string
  default     = "INR"
}

variable "notification_channel_ids" {
  description = "Cloud Monitoring notification channel IDs to notify on budget threshold breaches"
  type        = list(string)
}
