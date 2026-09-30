# Azure Event Hubs with Kafka-compatible API endpoint
resource "azurerm_eventhub_namespace" "kafka_eventhubs" {
  name                = "evh-aromabank-kafka"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "Standard"
  capacity            = 2
  auto_inflate_enabled= true
  maximum_throughput_units = 10

  tags = {
    Component = "Ingestion"
    Protocol  = "Kafka"
  }
}

# 1. Topic: bank.transactions.raw (high throughput ingestion)
resource "azurerm_eventhub" "topic_transactions_raw" {
  name                = "bank.transactions.raw"
  namespace_name      = azurerm_eventhub_namespace.kafka_eventhubs.name
  resource_group_name = azurerm_resource_group.rg.name
  partition_count     = 8
  message_retention   = 7
}

# 2. Topic: bank.fraud.alerts (real-time Flink CEP alerts)
resource "azurerm_eventhub" "topic_fraud_alerts" {
  name                = "bank.fraud.alerts"
  namespace_name      = azurerm_eventhub_namespace.kafka_eventhubs.name
  resource_group_name = azurerm_resource_group.rg.name
  partition_count     = 4
  message_retention   = 14
}

# 3. #CDC: Topic: oracle.bank.cdc.events (Debezium Change Data Capture stream)
resource "azurerm_eventhub" "topic_oracle_cdc" {
  name                = "oracle.bank.cdc.events"
  namespace_name      = azurerm_eventhub_namespace.kafka_eventhubs.name
  resource_group_name = azurerm_resource_group.rg.name
  partition_count     = 4
  message_retention   = 14
}
