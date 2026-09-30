"""
Configuration module for the Big Data financial transaction stream generator.
Allows full parametric control over velocity (events/sec), timeout (duration),
destination (Kafka, stdout, dry-run, file), and anomaly injection rates.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict


@dataclass
class StreamConfig:
    # Rate and duration controls
    velocity: float = 5.0           # Events per second (supports float e.g. 0.5 for slow, 100 for high speed)
    timeout: Optional[float] = 10.0 # Timeout in seconds after which generation halts (None = run forever)
    max_events: Optional[int] = None # Maximum total events to produce before halting

    # Destination and modes
    mode: str = "dry-run"           # "dry-run", "stdout", "file", "kafka"
    kafka_bootstrap: str = "localhost:9092"
    kafka_topic: str = "bank.transactions.raw"
    kafka_cdc_topic: str = "oracle.bank.cdc.events"
    output_file: Optional[Path] = None

    # Determinism and linkages
    seed: int = 42
    scale: float = 0.1              # Base scale aligned with AromaData generator
    customer_seed_path: Path = Path("seeds/base_data.yaml")

    # Financial and Anomaly Rates
    fraud_injection_rate: float = 0.05  # 5% of txns trigger synthetic fraud patterns
    aml_injection_rate: float = 0.02    # 2% of txns trigger AML structuring/layering patterns
    include_cdc_envelopes: bool = True  # Also emit CDC change-event format for Oracle/Postgres

    # Currency weights
    currency_weights: Dict[str, float] = field(default_factory=lambda: {
        "PLN": 0.85,
        "EUR": 0.08,
        "USD": 0.04,
        "GBP": 0.02,
        "CHF": 0.01,
    })
