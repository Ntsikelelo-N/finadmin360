variable "resource_group_name" {
  description = "Name of the Azure Resource Group"
  type        = string
  default     = "finadmin360-rg"
}

variable "location" {
  description = "Azure region — southafricanorth is Johannesburg"
  type        = string
  default     = "southafricanorth"
}

variable "project_name" {
  description = "Short project name used as prefix for all resources"
  type        = string
  default     = "finadmin360"
}

variable "synapse_admin_user" {
  description = "Synapse SQL administrator username"
  type        = string
  default     = "finadmin360admin"
}

variable "synapse_admin_password" {
  description = "Synapse SQL administrator password — store in Key Vault after creation"
  type        = string
  sensitive   = true
}
