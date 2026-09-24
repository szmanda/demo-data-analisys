"""
Generic PostgreSQL DDL and DML dump exporter parametrized by schema definition.
Generates SQL script compatible with PostgreSQL and Apache Superset.
"""
from pathlib import Path
from typing import Any
from src.schema import DatabaseSchema, DataType


class PostgresDumpExporter:
    def __init__(self, output_dir: Path | str):
        self.output_dir = Path(output_dir)

    def _map_type(self, dt: DataType) -> str:
        mapping = {
            DataType.INTEGER: "INTEGER",
            DataType.FLOAT: "NUMERIC(10, 2)",
            DataType.TEXT: "TEXT",
            DataType.DATE: "DATE",
            DataType.DATETIME: "TIMESTAMP",
            DataType.BOOLEAN: "BOOLEAN",
        }
        return mapping.get(dt, "TEXT")

    def _escape_sql_val(self, val: Any) -> str:
        if val is None:
            return "NULL"
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, bool):
            return "TRUE" if val else "FALSE"
        s = str(val).replace("'", "''")
        return f"'{s}'"

    def export(self, schema: DatabaseSchema, dataset: dict[str, list[dict[str, Any]]]) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        dump_path = self.output_dir / "aroma_dump_postgres.sql"

        lines = [
            "-- AromaData PostgreSQL dump",
            "-- Generated automatically by schema-driven exporter",
            "BEGIN;",
            ""
        ]

        table_order = [
            "bases", "ingredients", "tags", "actions",
            "oils", "oil_ingredients", "oil_tags", "oil_actions",
            "customers", "orders", "order_items", "reviews"
        ]

        # Drops in reverse
        for tbl_name in reversed(table_order):
            lines.append(f"DROP TABLE IF EXISTS {tbl_name} CASCADE;")
        lines.append("")

        # DDL
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
                pk_str = " PRIMARY KEY" if col.primary_key and not has_composite_pk else ""
                col_defs.append(f"  {col.name} {type_str}{pk_str}{null_str}")

                if col.foreign_key:
                    ref_table, ref_col = col.foreign_key.split(".")
                    fks.append(f"  FOREIGN KEY ({col.name}) REFERENCES {ref_table}({ref_col}) ON DELETE CASCADE")

            if has_composite_pk:
                pk_cols = ", ".join(tbl.primary_keys)
                col_defs.append(f"  PRIMARY KEY ({pk_cols})")

            body = ",\n".join(col_defs + fks)
            lines.append(f"CREATE TABLE {tbl.name} (\n{body}\n);")
            lines.append("")

        # DML (Batch INSERTS)
        for table_name in table_order:
            tbl = schema.get_table(table_name)
            rows = dataset.get(table_name, [])
            if not tbl or not rows:
                continue

            cols = tbl.column_names
            col_list_str = ", ".join(cols)

            # Insert in chunks of 200
            chunk_size = 200
            for i in range(0, len(rows), chunk_size):
                chunk = rows[i:i + chunk_size]
                val_tuples = []
                for row in chunk:
                    vals = [self._escape_sql_val(row.get(c)) for c in cols]
                    val_tuples.append(f"  ({', '.join(vals)})")
                
                insert_stmt = f"INSERT INTO {table_name} ({col_list_str}) VALUES\n" + ",\n".join(val_tuples) + ";"
                lines.append(insert_stmt)
            lines.append("")

        # Indexes
        lines.extend([
            "CREATE INDEX idx_orders_customer_id ON orders(customer_id);",
            "CREATE INDEX idx_orders_order_date ON orders(order_date);",
            "CREATE INDEX idx_order_items_order_id ON order_items(order_id);",
            "CREATE INDEX idx_order_items_oil_id ON order_items(oil_id);",
            "CREATE INDEX idx_reviews_oil_id ON reviews(oil_id);",
            "",
            "COMMIT;"
        ])

        with open(dump_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return dump_path
