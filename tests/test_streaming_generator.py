"""
Unit tests for AromaBank Big Data streaming generator.
Validates velocity, timeout cutoff, max_events, AromaData customer linking,
and Debezium CDC envelope structure.
"""
import time
from streaming.generator.config import StreamConfig
from streaming.generator.engine import StreamEngine
from streaming.generator.models import TransactionType


def test_stream_velocity_and_timeout():
    # Test small, fast parameters: velocity 20 events/sec, timeout 1.0 second
    config = StreamConfig(
        velocity=20.0,
        timeout=1.0,
        max_events=None,
        seed=123,
    )
    engine = StreamEngine(config)

    start = time.time()
    events = list(engine.stream_generator())
    elapsed = time.time() - start

    assert 0.9 <= elapsed <= 1.5, f"Elapsed time {elapsed} out of expected range"
    # At 20/sec for ~1 sec, expect around 15-25 events
    assert 15 <= len(events) <= 25, f"Expected 15-25 events, got {len(events)}"


def test_stream_max_events_cutoff():
    # Test strict max_events cutoff
    config = StreamConfig(
        velocity=100.0,
        timeout=10.0,
        max_events=12,
        seed=42,
    )
    engine = StreamEngine(config)
    events = list(engine.stream_generator())

    assert len(events) == 12
    # Validate payload structure
    first_item = events[0]
    assert "raw_transaction" in first_item
    assert "cdc_envelope" in first_item


def test_aromadata_customer_and_order_linking():
    config = StreamConfig(
        velocity=50.0,
        max_events=30,
        scale=0.1,
        seed=42,
    )
    engine = StreamEngine(config)
    events = list(engine.stream_generator())

    customer_ids = set()
    found_ecommerce_link = False

    for item in events:
        txn = item["raw_transaction"]
        assert txn["customer_id"] > 0
        customer_ids.add(txn["customer_id"])
        if txn.get("ecommerce_order_id"):
            found_ecommerce_link = True
            assert txn["ecommerce_order_id"].startswith("ORD-2024-")
            assert txn["merchant_name"] == "AromaData E-Shop (Olejki Eteryczne)"
            assert txn["channel"] == "BLIK_ONLINE"

    assert len(customer_ids) > 1, "Should link to multiple diverse customer accounts"
    assert found_ecommerce_link, "Expected at least one AromaData e-commerce transaction link"


def test_cdc_envelope_compliance():
    # #CDC: Verifies Debezium LogMiner schema fields
    config = StreamConfig(
        velocity=50.0,
        max_events=5,
        include_cdc_envelopes=True,
    )
    engine = StreamEngine(config)
    events = list(engine.stream_generator())

    for item in events:
        cdc = item["cdc_envelope"]
        assert cdc["op"] == "c" # INSERT
        assert cdc["before"] is None
        assert cdc["after"] is not None
        assert "transaction_id" in cdc["after"]
        assert cdc["source"]["connector"] == "oracle"
        assert cdc["source"]["db"] == "FREEPDB1"
        assert cdc["source"]["schema_name"] == "BANK"
        assert cdc["source"]["table"] == "TRANSACTIONS"


def test_fraud_and_aml_injection():
    # Test high rate to guarantee anomaly generation in small batch
    config = StreamConfig(
        velocity=100.0,
        max_events=100,
        fraud_injection_rate=0.40,
        aml_injection_rate=0.20,
        seed=999,
    )
    engine = StreamEngine(config)
    events = list(engine.stream_generator())

    frauds = [e for e in events if e["raw_transaction"]["is_synthetic_fraud"]]
    amls = [e for e in events if e["raw_transaction"]["aml_flag"]]

    assert len(frauds) > 0, "Should generate synthetic fraud events"
    assert len(amls) > 0, "Should generate synthetic AML events"

    for f in frauds:
        raw = f["raw_transaction"]
        assert raw["fraud_pattern"] in ["VELOCITY", "GEO_IMPOSSIBLE", "AMOUNT_SPIKE"]
        assert raw["risk_score"] >= 0.70

    for a in amls:
        raw = a["raw_transaction"]
        assert raw["aml_pattern"] in ["STRUCTURING", "ROUND_TRIPPING"]
        if raw["aml_pattern"] == "STRUCTURING":
            # Just under Polish 15,000 PLN threshold
            assert 14000.0 <= raw["amount_pln"] <= 15000.0
