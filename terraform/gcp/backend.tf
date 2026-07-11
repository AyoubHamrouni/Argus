terraform {
  backend "gcs" {
    bucket = "ai-soc-terraform-state"
    prefix = "gcp"
  }
}
