terraform {
  backend "gcs" {
    bucket = "argus-terraform-state"
    prefix = "gcp"
  }
}
