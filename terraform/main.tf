# Azure Cost Optimization for Billing Records - Terraform Template

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "billing_rg" {
  name     = "billing-records-rg"
  location = "East US"
}

resource "azurerm_storage_account" "billing_storage" {
  name                     = "billingarchivestorage"
  resource_group_name      = azurerm_resource_group.billing_rg.name
  location                 = azurerm_resource_group.billing_rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "archive_container" {
  name                  = "billing-archive"
  storage_account_name  = azurerm_storage_account.billing_storage.name
  container_access_type = "private"
}

resource "azurerm_cosmosdb_account" "billing_cosmos" {
  name                = "billingcosmosdb"
  location            = azurerm_resource_group.billing_rg.location
  resource_group_name = azurerm_resource_group.billing_rg.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = azurerm_resource_group.billing_rg.location
    failover_priority = 0
  }
}

resource "azurerm_cosmosdb_sql_database" "billing_db" {
  name                = "billing-db"
  resource_group_name = azurerm_resource_group.billing_rg.name
  account_name        = azurerm_cosmosdb_account.billing_cosmos.name
}

resource "azurerm_cosmosdb_sql_container" "billing_container" {
  name                = "records"
  resource_group_name = azurerm_resource_group.billing_rg.name
  account_name        = azurerm_cosmosdb_account.billing_cosmos.name
  database_name       = azurerm_cosmosdb_sql_database.billing_db.name
  partition_key_path  = "/partitionKey"
}

resource "azurerm_storage_account" "function_storage" {
  name                     = "functionarchivestore"
  resource_group_name      = azurerm_resource_group.billing_rg.name
  location                 = azurerm_resource_group.billing_rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_function_app" "archive_function" {
  name                       = "archive-function-app"
  location                   = azurerm_resource_group.billing_rg.location
  resource_group_name        = azurerm_resource_group.billing_rg.name
  app_service_plan_id        = azurerm_app_service_plan.function_plan.id
  storage_account_name       = azurerm_storage_account.function_storage.name
  storage_account_access_key = azurerm_storage_account.function_storage.primary_access_key
  version                    = "~4"
  os_type                    = "linux"
  runtime_stack              = "python"
  site_config {
    application_stack {
      python_version = "3.9"
    }
  }
}

resource "azurerm_app_service_plan" "function_plan" {
  name                = "archive-function-plan"
  location            = azurerm_resource_group.billing_rg.location
  resource_group_name = azurerm_resource_group.billing_rg.name
  kind                = "FunctionApp"
  reserved            = true
  sku {
    tier = "Dynamic"
    size = "Y1"
  }
}
