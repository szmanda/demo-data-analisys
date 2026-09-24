"""
Generic CSV exporter parametrized by table schema and dataset.
Produces clean, UTF-8 encoded CSV files for each table.
"""
import csv
from pathlib import Path
from typing import Any
from src.schema import DatabaseSchema


class CsvExporter:
    def __init__(self, output_dir: Path | str):
        self.output_dir = Path(output_dir)

    def export(self, schema: DatabaseSchema, dataset: dict[str, list[dict[str, Any]]]) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        created_files: list[Path] = []

        for table_name, rows in dataset.items():
            table_schema = schema.get_table(table_name)
            if not table_schema:
                continue

            fieldnames = table_schema.column_names
            target_path = self.output_dir / f"{table_name}.csv"

            with open(target_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                for row in rows:
                    # Clean up any None to empty string
                    clean_row = {k: ("" if row.get(k) is None else row.get(k)) for k in fieldnames}
                    writer.writerow(clean_row)

            created_files.append(target_path)

        return created_files
