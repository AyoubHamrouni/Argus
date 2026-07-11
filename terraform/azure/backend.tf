terraform {
  backend "azurerm" {
    resource_group_name  = "ai-soc-terraform"
    storage_account_name = "aisocterraform"
    container_name       = "tfstate"
    key                  = "azure/terraform.tfstate"
  }
}
