# AromaBank: End-to-End Big Data Streaming Architecture

## 1. High-Level Architecture Diagram

```
                 +-------------------------------------------------------------+
                 |                     DATA GENERATION LAYER                   |
                 |                                                             |
                 |   +-----------------------+     +-----------------------+   |
                 |   |  AromaData Generator  |     |  Oracle 23c Free DB   |   |
                 |   |  (Customers & Orders) |     |  (Core Banking OLTP)  |   |
                 |   +-----------+-----------+     +-----------+-----------+   |
                 +---------------|-----------------------------|---------------+
                                 |                             |
                                 |                             | #CDC: LogMiner
                                 |                             v
                                 |                +-------------------------+
                                 |                |    Debezium Connect     |
                                 |                |   (Captures Redo Logs)  |
                                 |                +------------+------------+
                                 |                             |
                                 +--------------+--------------+
                                                |
                                                v
                 +-------------------------------------------------------------+
                 |              INGESTION LAYER (Apache Kafka / KRaft)         |
                 |                                                             |
                 |   Topics:                                                   |
                 |   • bank.transactions.raw       (High-velocity txns)        |
                 |   • oracle.bank.cdc.events      (#CDC change envelopes)     |
                 |   • bank.fraud.alerts           (Flink alert output)        |
                 +-----------------------+-------------------------------------+
                                         |
                        +----------------+----------------+
                        |                                 |
                        v                                 v
   +---------------------------------------+  +---------------------------------------+
   |      Apache Flink (Java 17)           |  |     Apache Spark / Databricks         |
   |      Sub-Second CEP Stream Engine     |  |     Micro-Batch Analytics (Delta)     |
   |                                       |  |                                       |
   |  • Stateful KeyedProcessFunction      |  |  • Bronze Layer: Raw JSON ingestion   |
   |  • Sliding window velocity bursts     |  |  • Silver Layer: Schema & dedupe      |
   |  • Amount anomaly & outlier detection |  |  • Gold Layer: Hourly KPIs & AML     |
   |  • Outputs to bank.fraud.alerts       |  |  • Customer 360: AromaData join       |
   +-------------------+-------------------+  +-------------------+-------------------+
                       |                                          |
                       +--------------------+---------------------+
                                            |
                                            v
                 +-------------------------------------------------------------+
                 |            DISTRIBUTED COLUMNAR SERVING & BI                |
                 |                                                             |
                 |   +-----------------------+     +-----------------------+   |
                 |   |  Azure Synapse SQL    |     |  Oracle ADW           |   |
                 |   |  (Columnstore MPP)    |     |  (In-Memory Columnar) |   |
                 |   +-----------+-----------+     +-----------+-----------+   |
                 |               |                             |               |
                 |               +--------------+--------------+               |
                 |                              v                              |
                 |                   +---------------------+                   |
                 |                   |   Apache Superset   |                   |
                 |                   |  (Dashboards & BI)  |                   |
                 |                   +---------------------+                   |
                 +-------------------------------------------------------------+
```

---

## 2. Cross-Domain Linkage (AromaData ↔ AromaBank)

| AromaData (E-Commerce) | AromaBank (Streaming Banking) | Analytical Value |
|---|---|---|
| `customers.id` | `customer_id` | Unified customer financial profile (Customer 360) |
| `orders.id` | `ecommerce_order_id` | End-to-end order-to-settlement reconciliation |
| `orders.payment_method` | `channel` (BLIK, CARD, TRANSFER) | Payment preference & drop-off analysis |
| `orders.total_amount_pln` | `amount_pln` | E-commerce GMV vs. bank account balance verification |
| Polish Cities & Geographies | Geo coordinates & City | Real-time geospatial heatmaps and impossible travel detection |

---

## 3. Technology Matrix

1. **Python**: Stream generator with parametric `--velocity` and `--timeout`, plus Databricks REST API automation client.
2. **Java (Apache Flink)**: Sub-second stateful Complex Event Processing (`KeyedProcessFunction`) detecting velocity attacks and large amount spikes.
3. **Kafka (KRaft)**: High-performance, zero-Zookeeper event bus (<300MB RAM footprint).
4. **Oracle 23c Free & Debezium (#CDC)**: Real-time Change Data Capture via Oracle LogMiner redo streams into Kafka.
5. **Apache Spark & Databricks**: Medallion architecture (Bronze raw -> Silver deduplicated -> Gold KPIs).
6. **Terraform (IaC)**: Production cloud blueprints for Azure (Event Hubs, ADLS Gen2, Databricks, Synapse Columnar) and Oracle ADW.
7. **Minikube & Docker Compose**: 100% self-hosted local deployment without extra costs.
