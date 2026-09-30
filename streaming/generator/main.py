"""
CLI Entrypoint for the Financial Big Data Stream Generator.
Provides parametric controls: --velocity, --timeout, --max-events, --mode, --output-file.
"""
import argparse
import json
import sys
import time
from pathlib import Path

from streaming.generator.config import StreamConfig
from streaming.generator.engine import StreamEngine


def parse_args():
    parser = argparse.ArgumentParser(
        description="AromaBank: Big Data Real-Time Financial Transaction Stream Generator"
    )
    parser.add_argument(
        "--velocity",
        type=float,
        default=5.0,
        help="Rate of events per second (e.g. 1.0 = 1 txn/sec, 50.0 = 50 txn/sec). Default: 5.0",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Timeout in seconds to run before halting. Default: 5.0s. Use 0 for infinite.",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=None,
        help="Maximum total events to emit before stopping. Overrides or combines with timeout.",
    )
    parser.add_argument(
        "--mode",
        choices=["dry-run", "stdout", "file", "kafka"],
        default="dry-run",
        help="Destination mode: dry-run (summarize), stdout, file (JSONL), or kafka. Default: dry-run",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Path to output file when --mode file is specified.",
    )
    parser.add_argument(
        "--kafka-bootstrap",
        type=str,
        default="localhost:9092",
        help="Kafka bootstrap broker address. Default: localhost:9092",
    )
    parser.add_argument(
        "--kafka-topic",
        type=str,
        default="bank.transactions.raw",
        help="Kafka target topic for raw financial transactions. Default: bank.transactions.raw",
    )
    parser.add_argument(
        "--kafka-cdc-topic",
        type=str,
        default="oracle.bank.cdc.events",
        help="#CDC Kafka topic for Debezium CDC envelopes. Default: oracle.bank.cdc.events",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="PRNG seed for reproducible generation.",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=0.1,
        help="Customer scale factor aligned with AromaData (e.g. 0.1=~300 customers, 1.0=~3000 customers).",
    )
    parser.add_argument(
        "--fraud-rate",
        type=float,
        default=0.05,
        help="Proportion of transactions to inject synthetic fraud patterns into (0.0 to 1.0). Default: 0.05",
    )
    parser.add_argument(
        "--aml-rate",
        type=float,
        default=0.02,
        help="Proportion of transactions to inject AML patterns into (0.0 to 1.0). Default: 0.02",
    )
    return parser.parse_args()


def run_stream():
    args = parse_args()
    timeout = None if args.timeout == 0 else args.timeout

    config = StreamConfig(
        velocity=args.velocity,
        timeout=timeout,
        max_events=args.max_events,
        mode=args.mode,
        kafka_bootstrap=args.kafka_bootstrap,
        kafka_topic=args.kafka_topic,
        kafka_cdc_topic=args.kafka_cdc_topic,
        output_file=args.output_file,
        seed=args.seed,
        scale=args.scale,
        fraud_injection_rate=args.fraud_rate,
        aml_injection_rate=args.aml_rate,
    )

    print("=" * 72)
    print("💳 AromaBank: Financial Real-Time Stream Generator")
    print(f"   ► Velocity: {config.velocity} events/sec")
    print(f"   ► Timeout:  {config.timeout if config.timeout else 'Infinite'} seconds")
    print(f"   ► Max Events: {config.max_events if config.max_events else 'Unlimited'}")
    print(f"   ► Mode:     {config.mode}")
    print(f"   ► Scale:    {config.scale} (Seed: {config.seed})")
    print(f"   ► Fraud / AML injection: {config.fraud_injection_rate*100}% / {config.aml_injection_rate*100}%")
    print("=" * 72)

    engine = StreamEngine(config)
    print(f"✔ Initialized banking accounts pool: {len(engine.accounts)} accounts mapped to AromaData customers.")

    kafka_producer = None
    if config.mode == "kafka":
        try:
            from kafka import KafkaProducer
            kafka_producer = KafkaProducer(
                bootstrap_servers=config.kafka_bootstrap,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                retries=3,
            )
            print(f"✔ Connected to Kafka broker: {config.kafka_bootstrap}")
        except Exception as e:
            print(f"❌ Failed to connect to Kafka ({e}). Falling back to dry-run mode.")
            config.mode = "dry-run"

    file_handle = None
    if config.mode == "file":
        out_path = config.output_file or Path("data/raw/bank_stream.jsonl")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        file_handle = open(out_path, "w", encoding="utf-8")
        print(f"✔ Streaming directly to file: {out_path}")

    start_time = time.time()
    total_emitted = 0
    fraud_count = 0
    aml_count = 0
    total_volume_pln = 0.0

    try:
        for item in engine.stream_generator():
            total_emitted += 1
            raw = item["raw_transaction"]
            total_volume_pln += raw["amount_pln"]
            if raw["is_synthetic_fraud"]:
                fraud_count += 1
            if raw["aml_flag"]:
                aml_count += 1

            if config.mode == "dry-run":
                anomaly_tag = ""
                if raw["is_synthetic_fraud"]:
                    anomaly_tag = f" ⚠️ [FRAUD: {raw['fraud_pattern']}]"
                elif raw["aml_flag"]:
                    anomaly_tag = f" 🔍 [AML: {raw['aml_pattern']}]"

                print(
                    f"[{raw['timestamp_utc']}] {raw['transaction_id']} | "
                    f"Acc: {raw['account_id']} -> Cust#{raw['customer_id']:04d} | "
                    f"{raw['transaction_type']:<15} | "
                    f"{raw['amount_original']:>9.2f} {raw['currency_original']} "
                    f"({raw['amount_pln']:>9.2f} PLN) | "
                    f"City: {raw['city']:<10}{anomaly_tag}"
                )

            elif config.mode == "stdout":
                print(json.dumps(item))

            elif config.mode == "file" and file_handle:
                file_handle.write(json.dumps(item) + "\n")
                file_handle.flush()

            elif config.mode == "kafka" and kafka_producer:
                # Emit raw transaction to banking stream topic
                kafka_producer.send(
                    config.kafka_topic,
                    key=raw["account_id"],
                    value=raw,
                )
                # #CDC: Emit Debezium change event envelope to Oracle CDC topic
                if "cdc_envelope" in item:
                    kafka_producer.send(
                        config.kafka_cdc_topic,
                        key=raw["transaction_id"],
                        value=item["cdc_envelope"],
                    )

    except KeyboardInterrupt:
        print("\nStreaming interrupted by user.")
    finally:
        if file_handle:
            file_handle.close()
        if kafka_producer:
            kafka_producer.flush()
            kafka_producer.close()

    elapsed = time.time() - start_time
    effective_rate = total_emitted / max(0.001, elapsed)

    print("-" * 72)
    print("📊 Stream Generation Summary:")
    print(f"   ► Total Events Emitted: {total_emitted}")
    print(f"   ► Elapsed Time:         {elapsed:.2f} seconds")
    print(f"   ► Effective Velocity:   {effective_rate:.2f} events/sec")
    print(f"   ► Total Transacted PLN: {total_volume_pln:,.2f} PLN")
    print(f"   ► Synthetic Fraud Hits: {fraud_count} ({(fraud_count/max(1, total_emitted))*100:.1f}%)")
    print(f"   ► Synthetic AML Hits:   {aml_count} ({(aml_count/max(1, total_emitted))*100:.1f}%)")
    print("✨ Stream generation completed.")


if __name__ == "__main__":
    run_stream()
