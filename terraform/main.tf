terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "azurerm" {
  features {}
}

# Random suffix ensures globally unique resource names
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# ── Resource Group ────────────────────────────────────────────────
# A Resource Group is a logical container for all related Azure resources.
# Deleting the Resource Group deletes everything inside it — useful for cleanup.
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
  tags     = { project = var.project_name, environment = "learning" }
}

# ── Azure Data Lake Storage Gen2 ─────────────────────────────────
# ADLS Gen2 is where all data lives: raw files, cleaned files, model artifacts.
# enable_hierarchical_namespace = true is what makes it Gen2 (folder-like structure).
resource "azurerm_storage_account" "adls" {
  name                     = "${var.project_name}sa${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"  # Locally Redundant Storage — cheapest option
  account_kind             = "StorageV2"
  is_hns_enabled           = true   # This enables the Gen2 hierarchical namespace
  min_tls_version          = "TLS1_2"
  tags                     = { project = var.project_name }
}

# Create Bronze, Silver, and Gold containers (zones)
resource "azurerm_storage_data_lake_gen2_filesystem" "bronze" {
  name               = "bronze"
  storage_account_id = azurerm_storage_account.adls.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "silver" {
  name               = "silver"
  storage_account_id = azurerm_storage_account.adls.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "gold" {
  name               = "gold"
  storage_account_id = azurerm_storage_account.adls.id
}

# ── Azure Data Factory ────────────────────────────────────────────
resource "azurerm_data_factory" "adf" {
  name                = "${var.project_name}-adf"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  tags                = { project = var.project_name }
}

# ── Azure Key Vault ───────────────────────────────────────────────
# Key Vault stores secrets (passwords, connection strings) securely.
# Your Python code fetches secrets from Key Vault at runtime.
# No credentials are ever hardcoded.
resource "azurerm_key_vault" "kv" {
  name                = "${var.project_name}-kv-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"
  tags                = { project = var.project_name }
}

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault_access_policy" "current_user" {
  key_vault_id = azurerm_key_vault.kv.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id
  secret_permissions = ["Get", "List", "Set", "Delete", "Purge"]
}

# ── Synapse Analytics Workspace ───────────────────────────────────
resource "azurerm_synapse_workspace" "syn" {
  name                                 = "${var.project_name}-syn"
  resource_group_name                  = azurerm_resource_group.rg.name
  location                             = azurerm_resource_group.rg.location
  storage_data_lake_gen2_filesystem_id = azurerm_storage_data_lake_gen2_filesystem.gold.id
  sql_administrator_login              = var.synapse_admin_user
  sql_administrator_login_password     = var.synapse_admin_password
  tags                                 = { project = var.project_name }
  identity {
    type = "SystemAssigned"
  }
}

# Allow your local machine's IP to query Synapse
resource "azurerm_synapse_firewall_rule" "allow_all_dev" {
  name                 = "AllowAllForDev"
  synapse_workspace_id = azurerm_synapse_workspace.syn.id
  start_ip_address     = "0.0.0.0"
  end_ip_address       = "255.255.255.255"
}

# Separate storage account for Azure ML — HNS must be DISABLED for AML
# The ADLS Gen2 account (finadmin360sae2d7rg) has HNS enabled for the data lake
# and cannot be shared with AML. This account is for AML artifacts only.
resource "azurerm_storage_account" "aml_storage" {
  name                     = "${var.project_name}aml${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = false   # HNS must be OFF for Azure ML
  min_tls_version          = "TLS1_2"
  tags                     = { project = var.project_name }
}

# ── Azure Machine Learning ────────────────────────────────────────
resource "azurerm_machine_learning_workspace" "aml" {
  name                    = "${var.project_name}-aml"
  resource_group_name     = azurerm_resource_group.rg.name
  location                = azurerm_resource_group.rg.location
  application_insights_id = azurerm_application_insights.aml_insights.id
  key_vault_id            = azurerm_key_vault.kv.id
  storage_account_id      = azurerm_storage_account.aml_storage.id   # ← changed
  tags                    = { project = var.project_name }

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_application_insights" "aml_insights" {
  name                = "${var.project_name}-insights"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  application_type    = "web"

  lifecycle {
    # Azure auto-attaches a managed Log Analytics workspace to Application Insights.
    # That workspace lives in a system-managed resource group with a deny assignment
    # that blocks all external modifications. Ignore it completely.
    ignore_changes = [workspace_id, tags]
  }
}
