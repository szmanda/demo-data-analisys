# Synthetic Oils Data Generator Implementation Plan

> **Goal:** Build an end-to-end reproducible, scale-parametrized synthetic data generation pipeline simulating an essential oil business, exporting cleanly into SQLite, multi-sheet/single Excel, and CSV without schema pollution.

**Architecture:**
- Declarative schema metadata model (`Schema` & `TableSchema`) defining field types, keys, and descriptions.
- Realistic domain base vocabulary (Polish botanical names, carrier bases, actions, tags, customer demographics).
- Simulation engine using power laws (Pareto for product/customer popularity, log-normal pricing, negative binomial baskets, seasonal time spikes).
- Generic schema-agnostic exporters (`SqliteExporter`, `CsvExporter`, `ExcelExporter`, `PostgresDumpExporter`).
- CLI interface accepting `--scale`, `--seed`, `--output-dir`, and YAML configuration.

**Tech Stack:**
- Python 3.14 (in project venv)
- `numpy`, `pyyaml`, `openpyxl`, `pytest`

---

### Task 1: Environment & Dependency Setup
- Create `pyproject.toml` or `requirements.txt` with `numpy`, `pyyaml`, `openpyxl`, `pytest`.
- Install dependencies into `./venv`.
- Verify environment.

### Task 2: Schema Definition & Table Model
- Create `src/schema.py` defining `Column`, `TableSchema`, and `DatabaseSchema`.
- Create tests in `tests/test_schema.py` to ensure schema declarations validate data dictionaries.

### Task 3: Base Knowledge & Seed Vocabulary
- Create `seeds/base_data.yaml` and `src/generators/vocabulary.py` containing rich Polish botanicals, carrier bases, therapeutic actions, tags, Polish cities with voivodeship weights, and Polish first/last names.
- Verify reproducibility with seed tests.

### Task 4: Power-Law & Stochastic Engine
- Create `src/generators/distributions.py` providing Pareto sampler, Log-Normal price generator, basket size generator, and seasonal calendar weighting.
- Create tests in `tests/test_distributions.py` to verify mathematical skewness and reproducibility under a fixed random seed.

### Task 5: Relational Generator Pipeline
- Create `src/generators/pipeline.py` implementing `generate_dataset(config: Config) -> dict[str, list[dict[str, Any]]]`.
- Generate: `bases`, `ingredients`, `tags`, `actions`, `oils`, `oil_ingredients`, `oil_tags`, `oil_actions`, `customers`, `orders`, `order_items`, `reviews`.
- Verify relational integrity (all foreign keys exist in parent tables).

### Task 6: Schema-Parametrized Exporters (CSV, Excel, SQLite, Postgres DDL)
- Implement `src/exporters/csv_exporter.py`.
- Implement `src/exporters/excel_exporter.py` (both multi-sheet workbook and single-sheet per table).
- Implement `src/exporters/sqlite_exporter.py` with dynamic DDL generation, indexes, and FKs.
- Implement `src/exporters/postgres_exporter.py` generating SQL scripts ready for Apache Superset.

### Task 7: Master Config & CLI Entrypoint
- Implement `seeds/config.yaml` with master `scale: 0.1` default for quick testing and 1.0/5.0 scaling presets.
- Implement `src/main.py` CLI supporting `--scale`, `--seed`, `--config`, and `--formats`.
- Generate a sample dataset in `data/raw/` and `data/db/` and verify files.

### Task 8: Verification & Superset / Orange Documentation
- Run full test suite (`pytest`).
- Generate test scale dataset and verify CSV, Excel, and SQLite files.
- Add documentation for loading into Orange Data Mining and Superset.
- Commit all changes.
