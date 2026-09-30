variable "resource_group_name" {
  type        = string
  default     = "rg-aromabank-bigdata-prod"
  description = "Azure resource group name"
}

variable "location" {
  type        = string
  default     = "polandcentral"
  description = "Azure region (e.g. polandcentral, westeurope)"
}

variable "storage_account_name" {
  type        = string
  default     = "saaromabankdeltalake"
  description = "Globally unique name for ADLS Gen2 Delta Lake storage"
}
