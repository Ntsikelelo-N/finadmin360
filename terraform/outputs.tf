output "storage_account_name" {
  value       = azurerm_storage_account.adls.name
  description = "Add this as AZURE_STORAGE_ACCOUNT in your .env file"
}

output "key_vault_url" {
  value       = azurerm_key_vault.kv.vault_uri
  description = "Add this as KEY_VAULT_URL in your .env file"
}

output "synapse_serverless_endpoint" {
  value       = azurerm_synapse_workspace.syn.connectivity_endpoints["sqlOnDemand"]
  description = "Add this as SYNAPSE_SERVER in your .env file"
}

output "aml_workspace_name" {
  value       = azurerm_machine_learning_workspace.aml.name
  description = "Add this as AML_WORKSPACE in your .env file"
}

output "aml_storage_account_name" {
  value       = azurerm_storage_account.aml_storage.name
  description = "Dedicated storage account for Azure ML artifacts (no HNS)"
}
