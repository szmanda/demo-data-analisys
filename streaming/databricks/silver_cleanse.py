"""
Databricks Silver Layer Cleansing & Enrichment Notebook (Delta Lake).
Parses raw JSON, validates types, deduplicates events, and enriches
with AromaData static customer demographics and orders.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    IntegerType, BooleanType, LongType
)

spark = SparkSession.builder.appName("AromaBank-Silver-Cleanse").getOrCreate()

DELTA_BRONZE_PATH = "/mnt/datalake/bronze/transactions"
DELTA_SILVER_PATH = "/mnt/datalake/silver/transactions"
CHECKPOINT_SILVER_PATH = "/mnt/datalake/checkpoints/silver_transactions"

# 1. Define explicit transaction schema matching generator
transaction_schema = StructType([
    StructField("transaction_id", StringType(), False),
    StructField("account_id", StringType(), False),
    StructField("counterparty_account_id", StringType(), True),
    StructField("customer_id", IntegerType(), False),
    StructField("ecommerce_order_id", StringType(), True),
    StructField("transaction_type", StringType(), False),
    StructField("channel", StringType(), False),
    StructField("status", StringType(), False),
    StructField("amount_original", DoubleType(), False),
    StructField("currency_original", StringType(), False),
    StructField("amount_pln", DoubleType(), False),
    StructField("fx_rate", DoubleType(), False),
    StructField("merchant_category_code", StringType(), True),
    StructField("merchant_name", StringType(), True),
    StructField("city", StringType(), False),
    StructField("country", StringType(), False),
    StructField("device_id", StringType(), True),
    StructField("ip_address", StringType(), True),
    StructField("latency_ms", IntegerType(), True),
    StructField("timestamp_utc", StringType(), False),
    StructField("is_synthetic_fraud", BooleanType(), False),
    StructField("fraud_pattern", StringType(), True),
    StructField("aml_flag", BooleanType(), False),
    StructField("aml_pattern", StringType(), True),
    StructField("risk_score", DoubleType(), False),
])

# 2. Read streaming Bronze Delta table
bronze_stream = spark.readStream.format("delta").load(DELTA_BRONZE_PATH)

# 3. Parse JSON payload and project clean typed columns
silver_stream = (
    bronze_stream
    .select(from_json(col("raw_payload"), transaction_schema).alias("data"), col("ingested_at"))
    .select("data.*", "ingested_at")
    .filter(col("transaction_id").isNotNull() & (col("amount_pln") > 0))
    .withColumn("event_timestamp", to_timestamp(col("timestamp_utc")))
    .dropDuplicates(["transaction_id"])
)

# 4. Stream into Silver Delta table
query = (
    silver_stream.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", CHECKPOINT_SILVER_PATH)
    .trigger(processingTime="15 seconds")
    .start(DELTA_SILVER_PATH)
)

print(f"✔ Streaming into Silver Delta Lake at: {DELTA_SILVER_PATH}")
