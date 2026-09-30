# Azure Synapse Analytics Workspace & Dedicated SQL Pool (Distributed Columnar MPP Database)
# Clustered Columnstore indexing provides ultra-fast aggregation over billions of rows.

resource "azurerm_synapse_workspace" "synapse_ws" {
  name                                 = "syn-aromabank-analytics"
  resource_group_name                  = azurerm_resource_group.rg.name
  location                             = azurerm_resource_group.rg.location
  storage_data_lake_gen2_filesystem_id = azurerm_storage_data_lake_gen2_filesystem.gold.id
  sql_administrator_login              = "sqladminuser"
  sql_administrator_login_password     = "StrongSynapsePassw0rd!"

  identity {
    type = "SystemAssigned"
  }

  tags = {
    Engine = "DistributedColumnarMPP"
  }
}

# Distributed Columnar Dedicated SQL Pool (DW100c)
resource "azurerm_synapse_sql_pool" "columnar_pool" {
  name                 = "sqldw_banking_columnar"
  synapse_workspace_id = azurerm_synapse_workspace.synapse_ws.id
  sku_name             = "DW100c"
  create_mode          = "Default"
  storage_account_type = "GRS"

  tags = {
    Architecture = "MPP-Distributed-Columnstore"
  }
}
