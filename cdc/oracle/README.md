# #CDC: Oracle Change Data Capture (CDC) with Debezium & Kafka

This guide explains how Change Data Capture (CDC) functions for the **AromaBank** core banking system using Oracle 23c Free, Debezium, and Apache Kafka.

---

## 🏗️ How Oracle CDC Works

Traditional batch ETL queries tables using timestamps (e.g. `WHERE updated_at > last_sync`), which places load on the transactional database and misses intermediate states (e.g. INSERT followed by rapid UPDATE).

With **Change Data Capture**:
1. Every transactional operation (INSERT, UPDATE, DELETE) is written to Oracle **Redo Log** files.
2. Oracle **LogMiner** parses these binary redo logs into structured relational changes without impacting database transaction latency.
3. **Debezium Oracle Connector** connects to Oracle via LogMiner and continuously reads changes.
4. Debezium converts each row change into a **Debezium Envelope JSON** event and streams it into Kafka topic `oracle_cdc.BANK.TRANSACTIONS`.
5. Downstream engines (Apache Flink, Spark, Databricks Delta Lake) consume these change events in real time.

---

## 📋 Required Configurations & Scripts (Tagged with `#CDC`)

### 1. Enable ARCHIVELOG and Supplemental Logging (`#CDC`)
File: `cdc/oracle/01_setup_archivelog.sql`
- **ARCHIVELOG Mode**: Ensures Oracle does not overwrite redo logs before Debezium can read them.
- **Supplemental Logging**: Forces Oracle to write the primary key and changed columns into the redo log so that the consumer knows what was updated/deleted.

### 2. Debezium Common User Privileges (`#CDC`)
File: `cdc/oracle/02_create_cdc_user.sql`
- Creates common user `c##dbzuser` with `LOGMINING` and `SELECT ON V_$LOGMNR_*` permissions.

### 3. Business Table DDL with Supplemental Logging (`#CDC`)
File: `cdc/oracle/03_create_tables.sql`
- Creates `BANK.CUSTOMERS`, `BANK.BANK_ACCOUNTS`, and `BANK.TRANSACTIONS`.
- Executes `ALTER TABLE ... ADD SUPPLEMENTAL LOG DATA (ALL) COLUMNS;` to ensure complete row states are captured.

### 4. Debezium Connector Configuration (`#CDC`)
File: `cdc/oracle/debezium_oracle_connector.json`
- Configures connection to Oracle Free container (`FREEPDB1`), registers `BANK` schema whitelist, and outputs to Kafka.

---

## 🚀 How to Run Locally

### Option A: Using Minikube
```bash
# 1. Start Minikube (low memory profile)
minikube start --driver=docker --memory=4096 --cpus=2

# 2. Deploy Kafka, Oracle Free, Debezium, and Flink
kubectl apply -f k8s/01-kafka-kraft.yaml
kubectl apply -f k8s/02-oracle-free.yaml
kubectl apply -f k8s/03-debezium-connect.yaml
kubectl apply -f k8s/04-flink-cluster.yaml
```

### Option B: Using Docker Compose
```bash
# Start the entire local stream stack
docker compose -f docker-compose.stream.yml up -d

# Register the Debezium Oracle Connector
curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" \
  http://localhost:8083/connectors/ -d @cdc/oracle/debezium_oracle_connector.json
```

---

## 🔍 Testing CDC Live with the Generator

To generate stream data in dry-run mode (no external servers needed):
```bash
./venv/bin/python -m streaming.generator.main --velocity 10 --timeout 3 --mode dry-run
```

To stream into Kafka with CDC envelopes:
```bash
./venv/bin/python -m streaming.generator.main --velocity 50 --timeout 10 --mode kafka --kafka-bootstrap localhost:9092
```
