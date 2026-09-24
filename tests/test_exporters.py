import sqlite3
import openpyxl
from src.schema import get_aroma_schema
from src.generators.vocabulary import load_vocabulary
from src.generators.pipeline import GeneratorConfig, generate_dataset
from src.exporters.csv_exporter import CsvExporter
from src.exporters.excel_exporter import ExcelExporter
from src.exporters.sqlite_exporter import SqliteExporter
from src.exporters.postgres_exporter import PostgresDumpExporter

def test_all_exporters(tmp_path):
    schema = get_aroma_schema()
    vocab = load_vocabulary("seeds/base_data.yaml")
    config = GeneratorConfig(scale=0.03, seed=42)
    dataset = generate_dataset(config, vocab)

    # 1. Test CSV Exporter
    csv_dir = tmp_path / "csv"
    csv_exporter = CsvExporter(csv_dir)
    csv_files = csv_exporter.export(schema, dataset)
    assert len(csv_files) == len(schema.tables)
    assert (csv_dir / "oils.csv").exists()
    assert (csv_dir / "orders.csv").exists()

    # 2. Test Excel Exporter
    excel_dir = tmp_path / "excel"
    excel_exporter = ExcelExporter(excel_dir)
    excel_files = excel_exporter.export(schema, dataset, export_individual=True)
    assert (excel_dir / "olejki_calosc.xlsx").exists()
    assert (excel_dir / "oils.xlsx").exists()

    # Check sheet names in consolidated workbook
    wb = openpyxl.load_workbook(excel_dir / "olejki_calosc.xlsx")
    assert "oils" in wb.sheetnames
    assert "orders" in wb.sheetnames

    # 3. Test SQLite Exporter
    sqlite_file = tmp_path / "db" / "test.db"
    sqlite_exporter = SqliteExporter(sqlite_file)
    db_path = sqlite_exporter.export(schema, dataset)
    assert db_path.exists()

    conn = sqlite3.connect(sqlite_file)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM oils;")
    oil_count = cursor.fetchone()[0]
    assert oil_count == len(dataset["oils"])

    cursor.execute("SELECT COUNT(*) FROM orders;")
    order_count = cursor.fetchone()[0]
    assert order_count == len(dataset["orders"])
    conn.close()

    # 4. Test Postgres Exporter
    pg_dir = tmp_path / "pg"
    pg_exporter = PostgresDumpExporter(pg_dir)
    dump_path = pg_exporter.export(schema, dataset)
    assert dump_path.exists()
    content = dump_path.read_text(encoding="utf-8")
    assert "CREATE TABLE oils" in content
    assert "INSERT INTO oils" in content
    assert "idx_orders_customer_id" in content
