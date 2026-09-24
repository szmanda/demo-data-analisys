"""
Generic SQLite exporter parametrized by schema definition.
Generates DDL, creates indexes, enables foreign keys, and batch-inserts data.
"""
from pathlib import Path
import sqlite3
from typing import Any
from src.schema import DatabaseSchema, DataType


class SqliteExporter:
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)

    def _map_type(self, dt: DataType) -> str:
        mapping = {
            DataType.INTEGER: "INTEGER",
            DataType.FLOAT: "REAL",
            DataType.TEXT: "TEXT",
            DataType.DATE: "TEXT",
            DataType.DATETIME: "TEXT",
            DataType.BOOLEAN: "INTEGER",
        }
        return mapping.get(dt, "TEXT")

    def _generate_ddl(self, schema: DatabaseSchema) -> list[str]:
        statements = []

        # Order tables respecting foreign key dependencies
        table_order = [
            "bases", "ingredients", "tags", "actions",
            "oils", "oil_ingredients", "oil_tags", "oil_actions",
            "customers", "orders", "order_items", "reviews"
        ]

        for table_name in table_order:
            tbl = schema.get_table(table_name)
            if not tbl:
                continue

            col_defs = []
            fks = []

            has_composite_pk = len(tbl.primary_keys) > 1

            for col in tbl.columns:
                type_str = self._map_type(col.data_type)
                null_str = " NOT NULL" if not col.nullable else ""
                
                if col.primary_key and not has_composite_pk:
                    pk_str = " PRIMARY KEY"
                else:
                    pk_str = ""

                col_defs.append(f"  {col.name} {type_str}{pk_str}{null_str}")

                if col.foreign_key:
                    ref_table, ref_col = col.foreign_key.split(".")
                    fks.append(f"  FOREIGN KEY ({col.name}) REFERENCES {ref_table}({ref_col}) ON DELETE CASCADE")

            if has_composite_pk:
                pk_cols = ", ".join(tbl.primary_keys)
                col_defs.append(f"  PRIMARY KEY ({pk_cols})")

            body = ",\n".join(col_defs + fks)
            sql = f"CREATE TABLE IF NOT EXISTS {tbl.name} (\n{body}\n);"
            statements.append(sql)

        return statements

    def export(self, schema: DatabaseSchema, dataset: dict[str, list[dict[str, Any]]]) -> Path:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if self.db_path.exists():
            self.db_path.unlink()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Create tables
        ddl_statements = self._generate_ddl(schema)
        for ddl in ddl_statements:
            cursor.execute(ddl)

        # Insert rows table by table
        for table_name, rows in dataset.items():
            tbl = schema.get_table(table_name)
            if not tbl or not rows:
                continue

            cols = tbl.column_names
            placeholders = ", ".join(["?"] * len(cols))
            col_list_str = ", ".join(cols)
            insert_sql = f"INSERT INTO {table_name} ({col_list_str}) VALUES ({placeholders});"

            records = [
                tuple(row.get(col) for col in cols)
                for row in rows
            ]
            cursor.executemany(insert_sql, records)

        # Create high-value analytics indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);",
            "CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);",
            "CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);",
            "CREATE INDEX IF NOT EXISTS idx_order_items_oil_id ON order_items(oil_id);",
            "CREATE INDEX IF NOT EXISTS idx_reviews_oil_id ON reviews(oil_id);",
        ]
        for idx in indexes:
            cursor.execute(idx)

        conn.commit()
        conn.close()
        return self.db_path
