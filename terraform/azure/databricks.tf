# Azure Databricks Workspace
resource "azurerm_databricks_workspace" "databricks_ws" {
  name                = "dbw-aromabank-analytics"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "premium"

  custom_parameters {
    no_public_ip        = true
    virtual_network_id  = null
  }

  tags = {
    Component = "Databricks-DeltaLake"
  }
}
