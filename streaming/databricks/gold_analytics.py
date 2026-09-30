"""
Databricks Gold Layer Aggregations Notebook (Delta Lake).
Produces curated analytical marts:
1. Hourly Transaction & Fraud KPIs (delta_gold_hourly_kpis)
2. Customer 360 Financial Profile linking Banking + AromaData E-Commerce (delta_gold_customer_360)
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, window, count, sum as _sum, avg,
    when, round as _round, current_timestamp
)

spark = SparkSession.builder.appName("AromaBank-Gold-Analytics").getOrCreate()

DELTA_SILVER_PATH = "/mnt/datalake/silver/transactions"
DELTA_GOLD_HOURLY_PATH = "/mnt/datalake/gold/hourly_kpis"
DELTA_GOLD_CUSTOMER_PATH = "/mnt/datalake/gold/customer_360"

# 1. Read Silver Delta Table
silver_df = spark.read.format("delta").load(DELTA_SILVER_PATH)

# 2. Mart 1: Hourly KPIs by Channel and City
hourly_kpis = (
    silver_df
    .groupBy(
        window(col("event_timestamp"), "1 hour"),
        col("channel"),
        col("city")
    )
    .agg(
        count("transaction_id").alias("total_transactions"),
        _round(_sum("amount_pln"), 2).alias("total_volume_pln"),
        _round(avg("amount_pln"), 2).alias("avg_transaction_pln"),
        _sum(when(col("is_synthetic_fraud") == True, 1).otherwise(0)).alias("fraud_detected_count"),
        _sum(when(col("aml_flag") == True, 1).otherwise(0)).alias("aml_alerts_count"),
        _round(avg("latency_ms"), 1).alias("avg_latency_ms")
    )
    .withColumn("computed_at", current_timestamp())
)

hourly_kpis.write.format("delta").mode("overwrite").save(DELTA_GOLD_HOURLY_PATH)
print(f"✔ Gold Hourly KPIs updated at: {DELTA_GOLD_HOURLY_PATH}")

# 3. Mart 2: Customer 360 Financial Profile
customer_360 = (
    silver_df
    .groupBy("customer_id")
    .agg(
        count("transaction_id").alias("banking_tx_count"),
        _round(_sum("amount_pln"), 2).alias("total_spent_pln"),
        _round(avg("amount_pln"), 2).alias("avg_ticket_pln"),
        _sum(when(col("ecommerce_order_id").isNotNull(), 1).otherwise(0)).alias("aromadata_order_count"),
        _round(avg("risk_score"), 3).alias("average_risk_score"),
        _sum(when(col("is_synthetic_fraud") == True, 1).otherwise(0)).alias("lifetime_fraud_flags")
    )
    .withColumn("computed_at", current_timestamp())
)

customer_360.write.format("delta").mode("overwrite").save(DELTA_GOLD_CUSTOMER_PATH)
print(f"✔ Gold Customer 360 profile updated at: {DELTA_GOLD_CUSTOMER_PATH}")
