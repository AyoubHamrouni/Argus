terraform {
  backend "s3" {
    bucket         = "ai-soc-terraform-state"
    key            = "aws/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "terraform-lock"
  }
}
