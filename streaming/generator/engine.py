"""
Stream Generator Engine for Banking Transactions and Operations.
Tightly linked with AromaData customer demographics and order payments.
Supports velocity (events/sec), timeout (seconds), and max_events termination criteria.
#CDC: Can produce raw transaction events or Debezium CDC change events.
"""
import random
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, List, Dict, Any, Optional

import yaml

from streaming.generator.config import StreamConfig
from streaming.generator.models import (
    FinancialTransaction,
    TransactionType,
    Channel,
    TransactionStatus,
    BankAccount,
    DebeziumCdcEnvelope,
    DebeziumSourceInfo,
)


# Polish Merchant Categories
MERCHANTS_BY_MCC = {
    "5912": ["AromaData E-Shop", "Apteka Słoneczna", "Super-Pharm", "Drogeria Rossmann", "Natura Eko"],
    "5411": ["Biedronka", "Lidl Polska", "Dino", "Auchan", "Żabka Nano"],
    "5812": ["Restauracja Pod Baranem", "Kawiarnia Karafka", "Pizzeria Napoli", "Green Caffe Nero"],
    "5541": ["Orlen Stacja Paliw", "BP Polska", "Shell Autostrada"],
    "4814": ["Orange Polska", "Play Abonament", "T-Mobile Doladowanie"],
    "4900": ["PGE Dystrybucja", "Tauron Energia", "PGNiG Gaz"],
    "7997": ["Zdrofit Fitness", "Gym Platinum", "Basen Miejski"],
}

# FX baseline rates relative to PLN
FX_RATES = {
    "PLN": 1.0,
    "EUR": 4.28,
    "USD": 3.96,
    "GBP": 5.12,
    "CHF": 4.45,
}

CITY_COORDINATES = {
    "Warszawa": (52.2297, 21.0122),
    "Kraków": (50.0647, 19.9450),
    "Wrocław": (51.1079, 17.0385),
    "Poznań": (52.4064, 16.9252),
    "Gdańsk": (54.3520, 18.6466),
    "Katowice": (50.2649, 19.0238),
    "Lublin": (51.2465, 22.5684),
}


class StreamEngine:
    def __init__(self, config: StreamConfig):
        self.config = config
        self.prng = random.Random(config.seed)
        self.accounts: List[BankAccount] = []
        self.cities: List[str] = list(CITY_COORDINATES.keys())
        self._init_accounts()

    def _init_accounts(self):
        """
        Creates synthetic bank accounts linked to customer IDs (1 to N based on scale).
        Matches AromaData customer scaling.
        """
        total_customers = max(20, int(3000 * self.config.scale))
        account_types = ["CHECKING", "SAVINGS", "BUSINESS"]

        for cust_id in range(1, total_customers + 1):
            # Each customer has at least 1 checking account, some have savings/business
            num_accounts = 1 if self.prng.random() > 0.3 else 2
            for acc_idx in range(num_accounts):
                acc_type = "CHECKING" if acc_idx == 0 else self.prng.choice(account_types)
                account_id = f"ACC-{cust_id:06d}-{acc_idx+1}"
                iban = f"PL{self.prng.randint(10, 99)}{self.prng.randint(1000, 9999)}{cust_id:08d}{self.prng.randint(10000000, 99999999)}"
                balance = round(self.prng.uniform(500.0, 45000.0), 2)

                self.accounts.append(
                    BankAccount(
                        account_id=account_id,
                        customer_id=cust_id,
                        iban=iban,
                        account_type=acc_type,
                        currency="PLN",
                        balance_pln=balance,
                        credit_limit_pln=1000.0 if acc_type == "CHECKING" else 0.0,
                        opened_date="2022-01-15",
                    )
                )

    def _pick_currency(self) -> str:
        r = self.prng.random()
        cumulative = 0.0
        for curr, weight in self.config.currency_weights.items():
            cumulative += weight
            if r <= cumulative:
                return curr
        return "PLN"

    def generate_single_transaction(self, event_idx: int) -> FinancialTransaction:
        """Generates a realistic transaction, potentially linked to AromaData or injecting anomalies."""
        acc = self.prng.choice(self.accounts)
        counterparty = self.prng.choice(self.accounts)
        while counterparty.account_id == acc.account_id:
            counterparty = self.prng.choice(self.accounts)

        currency = self._pick_currency()
        fx_rate = FX_RATES.get(currency, 1.0)

        # Decide anomaly injection
        is_fraud = self.prng.random() < self.config.fraud_injection_rate
        is_aml = (not is_fraud) and (self.prng.random() < self.config.aml_injection_rate)

        fraud_pattern = None
        aml_pattern = None
        risk_score = round(self.prng.uniform(0.01, 0.15), 3)

        # Transaction type and channel distribution
        roll = self.prng.random()
        ecommerce_order_id = None

        if roll < 0.35:
            # Card / POS payment
            txn_type = TransactionType.CARD_PAYMENT
            channel = Channel.POS
            mcc = self.prng.choice(list(MERCHANTS_BY_MCC.keys()))
            merchant = self.prng.choice(MERCHANTS_BY_MCC[mcc])
            amount_pln = round(self.prng.lognormvariate(3.8, 0.7), 2) # median ~45 PLN
        elif roll < 0.60:
            # BLIK online purchase (often AromaData e-commerce store purchase!)
            txn_type = TransactionType.BLIK
            channel = Channel.BLIK_ONLINE
            mcc = "5912"
            merchant = "AromaData E-Shop (Olejki Eteryczne)"
            amount_pln = round(self.prng.uniform(49.0, 320.0), 2)
            ecommerce_order_id = f"ORD-2024-{self.prng.randint(10000, 99999)}"
        elif roll < 0.85:
            # Bank Transfer
            txn_type = TransactionType.TRANSFER
            channel = Channel.MOBILE_APP if self.prng.random() > 0.3 else Channel.INTERNET_BANKING
            mcc = None
            merchant = None
            amount_pln = round(self.prng.uniform(50.0, 3500.0), 2)
        else:
            # ATM withdrawal
            txn_type = TransactionType.ATM_WITHDRAWAL
            channel = Channel.ATM
            mcc = "6011"
            merchant = "Euronet / Planet Cash"
            amount_pln = float(self.prng.choice([50, 100, 200, 500, 1000]))

        # Apply Fraud Pattern injections
        city = self.prng.choice(self.cities)
        coords = CITY_COORDINATES.get(city, (52.2297, 21.0122))

        if is_fraud:
            fraud_type_roll = self.prng.choice(["VELOCITY", "GEO_IMPOSSIBLE", "AMOUNT_SPIKE"])
            fraud_pattern = fraud_type_roll
            risk_score = round(self.prng.uniform(0.75, 0.99), 3)

            if fraud_type_roll == "VELOCITY":
                # High frequency burst
                amount_pln = round(self.prng.uniform(800.0, 2500.0), 2)
            elif fraud_type_roll == "GEO_IMPOSSIBLE":
                # Impossible travel: card logged in exotic foreign capital
                city = "Madrid / London"
                coords = (40.4168, -3.7038)
            elif fraud_type_roll == "AMOUNT_SPIKE":
                # Massive single outlier transfer
                amount_pln = round(self.prng.uniform(45000.0, 120000.0), 2)

        # Apply AML Pattern injections
        if is_aml:
            aml_type_roll = self.prng.choice(["STRUCTURING", "ROUND_TRIPPING"])
            aml_pattern = aml_type_roll
            risk_score = round(self.prng.uniform(0.60, 0.88), 3)
            txn_type = TransactionType.TRANSFER
            if aml_type_roll == "STRUCTURING":
                # Transfers just below the 15,000 PLN (GIIF threshold)
                amount_pln = round(self.prng.uniform(14200.0, 14950.0), 2)

        # Convert original amount according to currency
        amount_orig = round(amount_pln / fx_rate, 2)

        now_utc = datetime.now(timezone.utc).isoformat()
        status = TransactionStatus.BLOCKED_FRAUD if (is_fraud and risk_score > 0.92) else TransactionStatus.SETTLED

        return FinancialTransaction(
            transaction_id=f"TXN-{int(time.time()*1000)}-{event_idx:05d}",
            account_id=acc.account_id,
            counterparty_account_id=counterparty.account_id if txn_type == TransactionType.TRANSFER else None,
            customer_id=acc.customer_id,
            ecommerce_order_id=ecommerce_order_id,
            transaction_type=txn_type,
            channel=channel,
            status=status,
            amount_original=amount_orig,
            currency_original=currency,
            amount_pln=amount_pln,
            fx_rate=fx_rate,
            merchant_category_code=mcc,
            merchant_name=merchant,
            city=city,
            country="PL" if fraud_pattern != "GEO_IMPOSSIBLE" else "ES",
            latitude=coords[0],
            longitude=coords[1],
            device_id=f"DEV-{acc.customer_id:04d}-{self.prng.randint(1, 3)}",
            ip_address=f"195.116.{self.prng.randint(1, 254)}.{self.prng.randint(1, 254)}",
            session_id=str(uuid.uuid4())[:8],
            latency_ms=self.prng.randint(8, 45),
            timestamp_utc=now_utc,
            is_synthetic_fraud=is_fraud,
            fraud_pattern=fraud_pattern,
            aml_flag=is_aml,
            aml_pattern=aml_pattern,
            risk_score=risk_score,
        )

    #CDC: Converts a financial transaction to a Debezium-standard CDC payload
    def to_cdc_envelope(self, txn: FinancialTransaction) -> DebeziumCdcEnvelope:
        ts_ms = int(time.time() * 1000)
        source = DebeziumSourceInfo(
            connector="oracle",                         # #CDC: Oracle LogMiner source
            name="oracle_core_banking",
            ts_ms=ts_ms,
            db="FREEPDB1",                              # #CDC: Oracle 23c Free pluggable database
            schema_name="BANK",
            table="TRANSACTIONS",
            txId=f"0x{random.randint(1000, 9999):x}",
            scn=str(random.randint(1000000, 2000000)),  # #CDC: System Change Number
        )
        return DebeziumCdcEnvelope(
            before=None,                                # #CDC: 'before' is null for INSERT operations
            after=txn.model_dump(),
            source=source,
            op="c",                                     # #CDC: 'c' indicates an INSERT (CREATE)
            ts_ms=ts_ms,
        )

    def stream_generator(self) -> Generator[Dict[str, Any], None, None]:
        """
        Main generator loop respecting:
        - velocity: sleep delta between emissions
        - timeout: time limit cutoff
        - max_events: total event count cutoff
        """
        start_time = time.time()
        event_count = 0
        sleep_interval = 1.0 / max(0.001, self.config.velocity)

        while True:
            # Check timeout termination
            elapsed = time.time() - start_time
            if self.config.timeout is not None and elapsed >= self.config.timeout:
                break

            # Check max_events termination
            if self.config.max_events is not None and event_count >= self.config.max_events:
                break

            event_count += 1
            txn = self.generate_single_transaction(event_count)

            payload = {
                "raw_transaction": txn.model_dump(),
            }
            if self.config.include_cdc_envelopes:
                payload["cdc_envelope"] = self.to_cdc_envelope(txn).model_dump()

            yield payload

            # Control emission velocity
            time.sleep(sleep_interval)
