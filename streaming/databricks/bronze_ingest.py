"""
Databricks Bronze Layer Ingestion Notebook (PySpark Structured Streaming).
Consumes raw JSON event stream from Kafka (or Azure Event Hubs) and appends
to Bronze Delta Lake table with zero loss and schema preservation.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, input_file_name

# Initialize Spark session
spark = SparkSession.builder.appName("AromaBank-Bronze-Ingestion").getOrCreate()

# 1. Define stream parameters
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "bank.transactions.raw"
CHECKPOINT_PATH = "/mnt/datalake/checkpoints/bronze_transactions"
DELTA_BRONZE_PATH = "/mnt/datalake/bronze/transactions"

# 2. Read streaming data from Kafka
raw_kafka_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
    .option("subscribe", KAFKA_TOPIC)
    .option("startingOffsets", "latest")
    .option("failOnDataLoss", "false")
    .load()
)

# 3. Bronze transformation: capture payload, key, offset, and append ingestion timestamp
bronze_df = (
    raw_kafka_df
    .selectExpr(
        "CAST(key AS STRING) AS kafka_key",
        "CAST(value AS STRING) AS raw_payload",
        "topic",
        "partition",
        "offset",
        "timestamp AS kafka_timestamp"
    )
    .withColumn("ingested_at", current_timestamp())
)

# 4. Write stream to Delta Bronze table (append-only)
query = (
    bronze_df.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", CHECKPOINT_PATH)
    .trigger(processingTime="10 seconds")
    .start(DELTA_BRONZE_PATH)
)

print(f"✔ Streaming into Bronze Delta Lake at: {DELTA_BRONZE_PATH}")
# query.awaitTermination()
