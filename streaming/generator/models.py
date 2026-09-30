"""
Domain models for financial transactions, accounts, fraud alerts, and CDC envelopes.
#CDC - All models support JSON serialization and Debezium-compliant CDC envelope wrapping.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    TRANSFER = "TRANSFER"
    CARD_PAYMENT = "CARD_PAYMENT"
    BLIK = "BLIK"
    ATM_WITHDRAWAL = "ATM_WITHDRAWAL"
    SALARY_CREDIT = "SALARY_CREDIT"
    LOAN_REPAYMENT = "LOAN_REPAYMENT"
    FX_CONVERSION = "FX_CONVERSION"


class Channel(str, Enum):
    MOBILE_APP = "MOBILE_APP"
    INTERNET_BANKING = "INTERNET_BANKING"
    POS = "POS"
    ATM = "ATM"
    BLIK_ONLINE = "BLIK_ONLINE"
    BRANCH = "BRANCH"
    API_GATEWAY = "API_GATEWAY"


class TransactionStatus(str, Enum):
    SETTLED = "SETTLED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"
    BLOCKED_FRAUD = "BLOCKED_FRAUD"


class BankAccount(BaseModel):
    account_id: str
    customer_id: int          # Links directly to AromaData customers.id
    iban: str                 # Polish format e.g. PL61109010140000071219812874
    account_type: str         # CHECKING, SAVINGS, BUSINESS
    currency: str = "PLN"
    balance_pln: float
    credit_limit_pln: float = 0.0
    status: str = "ACTIVE"
    opened_date: str


class FinancialTransaction(BaseModel):
    """
    Core event model for high-throughput streaming pipelines.
    Wide schema designed for real-time Flink CEP and Spark/Databricks Delta Lake analytics.
    """
    transaction_id: str
    account_id: str
    counterparty_account_id: Optional[str] = None
    customer_id: int                            # Links to AromaData customer
    ecommerce_order_id: Optional[str] = None     # Links to AromaData order (when applicable)
    
    transaction_type: TransactionType
    channel: Channel
    status: TransactionStatus = TransactionStatus.SETTLED

    # Multi-currency & FX
    amount_original: float
    currency_original: str
    amount_pln: float
    fx_rate: float = 1.0

    # Merchant & Enrichment
    merchant_category_code: Optional[str] = None # e.g. 5912 (Cosmetics/Pharmacies), 5411 (Groceries)
    merchant_name: Optional[str] = None
    
    # Geo / Location
    city: str
    country: str = "PL"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Operational & Auditing
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    latency_ms: int = 15
    timestamp_utc: str

    # Fraud & AML indicators (Synthetic ground-truth for ML & Flink CEP)
    is_synthetic_fraud: bool = False
    fraud_pattern: Optional[str] = None          # VELOCITY, GEO_IMPOSSIBLE, AMOUNT_SPIKE
    aml_flag: bool = False
    aml_pattern: Optional[str] = None            # STRUCTURING, SMURFING, ROUND_TRIPPING
    risk_score: float = 0.05                     # Baseline low risk score 0.0 - 1.0


class FraudAlert(BaseModel):
    alert_id: str
    transaction_id: str
    account_id: str
    customer_id: int
    rule_name: str
    confidence: float
    recommended_action: str                      # BLOCK, REVIEW, STEP_UP_SMS
    triggered_at_utc: str


#CDC - Debezium-standard Change Data Capture Envelope representation
class DebeziumSourceInfo(BaseModel):
    version: str = "2.5.0.Final"
    connector: str = "oracle"                    # #CDC: Oracle LogMiner connector identifier
    name: str = "oracle_core_banking"
    ts_ms: int
    snapshot: str = "false"
    db: str = "FREEPDB1"                         # #CDC: Pluggable database name in Oracle Free 23c
    schema_name: str = "BANK"
    table: str = "TRANSACTIONS"
    txId: Optional[str] = "0x0001"
    scn: Optional[str] = "1049281"               # #CDC: System Change Number (SCN) from Oracle redo logs


class DebeziumCdcEnvelope(BaseModel):
    """
    #CDC: Represents an exact Debezium Kafka message envelope capturing row-level changes
    from Oracle redo logs or PostgreSQL WAL.
    op codes: 'c' = create (INSERT), 'u' = update, 'd' = delete, 'r' = read (snapshot)
    """
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    source: DebeziumSourceInfo
    op: str = "c"                                # #CDC: 'c' = INSERT, 'u' = UPDATE, 'd' = DELETE
    ts_ms: int
