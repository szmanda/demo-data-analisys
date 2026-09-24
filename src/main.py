"""
Main CLI entrypoint for synthetic data generation.
Supports scale parameter, seed, output directory, and target format flags.
"""
import argparse
from datetime import date
from pathlib import Path
import sys
import yaml

from src.schema import get_aroma_schema
from src.generators.vocabulary import load_vocabulary
from src.generators.pipeline import GeneratorConfig, generate_dataset
from src.exporters.csv_exporter import CsvExporter
from src.exporters.excel_exporter import ExcelExporter
from src.exporters.sqlite_exporter import SqliteExporter
from src.exporters.postgres_exporter import PostgresDumpExporter


def load_yaml_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def parse_args():
    parser = argparse.ArgumentParser(
        description="AromaData: Organic Synthetic Essential Oil Data Generator"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("seeds/config.yaml"),
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=None,
        help="Master scaling parameter (e.g. 0.05=micro, 0.1=small, 1.0=medium, 5.0=large)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="PRNG seed for reproducible data generation",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=["sqlite", "csv", "excel", "postgres", "all"],
        default=None,
        help="Output formats to generate",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    file_cfg = load_yaml_config(args.config)

    # Resolve scale and seed with precedence: CLI flag > YAML config > defaults
    scale = args.scale if args.scale is not None else float(file_cfg.get("scale", 0.1))
    seed = args.seed if args.seed is not None else int(file_cfg.get("seed", 42))

    dates_cfg = file_cfg.get("dates", {})
    start_date = date.fromisoformat(dates_cfg.get("start", "2022-01-01"))
    end_date = date.fromisoformat(dates_cfg.get("end", "2024-12-31"))

    dist_cfg = file_cfg.get("distributions", {})
    alpha_prod = float(dist_cfg.get("pareto_alpha_products", 1.16))
    alpha_cust = float(dist_cfg.get("pareto_alpha_customers", 1.25))

    formats = args.formats
    if not formats:
        formats = file_cfg.get("formats", ["sqlite", "csv", "excel", "postgres"])
    if "all" in formats:
        formats = ["sqlite", "csv", "excel", "postgres"]

    paths_cfg = file_cfg.get("paths", {})
    csv_dir = Path(paths_cfg.get("csv_dir", "data/raw/csv"))
    excel_dir = Path(paths_cfg.get("excel_dir", "data/raw/excel"))
    sqlite_db = Path(paths_cfg.get("sqlite_db", "data/db/olejki.db"))
    postgres_dir = Path(paths_cfg.get("postgres_dir", "data/raw/postgres"))

    print(f"🌿 AromaData Generator Initializing...")
    print(f"   ► Scale: {scale}")
    print(f"   ► Seed: {seed}")
    print(f"   ► Date range: {start_date} to {end_date}")
    print(f"   ► Target Formats: {', '.join(formats)}")

    # 1. Load Schema and Vocabulary
    schema = get_aroma_schema()
    vocab = load_vocabulary("seeds/base_data.yaml")

    # 2. Generate Dataset
    print("\n[1/3] Generating synthetic relational data with power-law distributions...")
    gen_config = GeneratorConfig(
        scale=scale,
        seed=seed,
        start_date=start_date,
        end_date=end_date,
        pareto_alpha_products=alpha_prod,
        pareto_alpha_customers=alpha_cust,
    )
    dataset = generate_dataset(gen_config, vocab)

    print(f"   ✔ Bases: {len(dataset['bases'])}")
    print(f"   ✔ Ingredients: {len(dataset['ingredients'])}")
    print(f"   ✔ Tags: {len(dataset['tags'])}")
    print(f"   ✔ Actions: {len(dataset['actions'])}")
    print(f"   ✔ Finished Oils: {len(dataset['oils'])}")
    print(f"   ✔ Customers: {len(dataset['customers'])}")
    print(f"   ✔ Orders: {len(dataset['orders'])}")
    print(f"   ✔ Order Items: {len(dataset['order_items'])}")
    print(f"   ✔ Product Reviews: {len(dataset['reviews'])}")

    # 3. Export Data to requested formats
    print("\n[2/3] Exporting to selected formats...")

    if "csv" in formats:
        print(f"   ► Exporting CSV files to {csv_dir}...")
        csv_exporter = CsvExporter(csv_dir)
        csv_files = csv_exporter.export(schema, dataset)
        print(f"     ✔ Created {len(csv_files)} CSV files")

    if "excel" in formats:
        print(f"   ► Exporting Excel files to {excel_dir}...")
        excel_exporter = ExcelExporter(excel_dir)
        excel_files = excel_exporter.export(schema, dataset, export_individual=True)
        print(f"     ✔ Created {len(excel_files)} Excel workbooks (including master consolidated olejki_calosc.xlsx)")

    if "sqlite" in formats:
        print(f"   ► Exporting SQLite database to {sqlite_db}...")
        sqlite_exporter = SqliteExporter(sqlite_db)
        db_path = sqlite_exporter.export(schema, dataset)
        print(f"     ✔ SQLite database written to {db_path}")

    if "postgres" in formats:
        print(f"   ► Exporting PostgreSQL dump to {postgres_dir}...")
        pg_exporter = PostgresDumpExporter(postgres_dir)
        sql_path = pg_exporter.export(schema, dataset)
        print(f"     ✔ PostgreSQL dump script generated at {sql_path}")

    print("\n[3/3] ✨ Generation completed successfully!")


if __name__ == "__main__":
    main()
