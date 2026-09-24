# Synthetic Oil Business Data Generator (AromaData) - Design Document

## 1. Overview
The AromaData project provides a configurable, reproducible, and schema-driven synthetic data generation pipeline simulating an artisanal and commercial essential oils business ("Olejki"). 
The generated data mimics realistic organic consumer and supply chain behavior using power laws (Pareto distribution), seasonal trends, log-normal pricing, and discrete basket sizing.

Data can be exported into multiple target formats without schema pollution:
- **SQLite Database** (`.db`)
- **CSV files** (per-table, UTF-8)
- **Excel Workbook** (`.xlsx`, multi-sheet or single-file per table)
- **PostgreSQL / Superset ready DDL/DML**

The generator is scalable using a single master scale parameter (`scale`), is 100% reproducible via seed configuration, and produces Polish-localized product, recipe, and customer records.

---

## 2. Realistic / Organic Data Modeling & Power Laws
To satisfy exploratory data analysis, business intelligence, and data mining requirements (e.g. in Orange Data Mining and Apache Superset):
1. **Product Popularity (Pareto / Zipf's Law)**:
   - A minority of hero products (e.g., Lavender, Tea Tree, Eucalyptus, signature blends) account for the majority of sales volume (~80/20 rule).
2. **Customer Purchasing Frequency (Exponential / Pareto)**:
   - Most customers make 1 or 2 purchases (churn/one-offs).
   - A long tail of loyal repeat customers make frequent recurring orders.
3. **Basket Size (Negative Binomial / Geometric Distribution)**:
   - Typically 1-3 items per order, tapering off towards rare wholesale/bulk baskets (10-25+ items).
4. **Price Distribution (Log-Normal Distribution)**:
   - Bulk base oils and common oils cluster around 25-50 PLN.
   - Rare/precious oils (e.g., Damascus Rose, Sandalwood, Neroli) extend into a natural high-price tail (150-300+ PLN).
5. **Seasonality & Day-of-Week Effect**:
   - Q4 holiday surges (November-December gift shopping, Black Friday).
   - Spring/summer bumps for insect-repellent oils (citronella, lemongrass) and refreshing scents.
   - Weekend vs. weekday order distribution variations.
6. **Geographic Distribution**:
   - Major Polish metropolitan centers (Warszawa, Kraków, Wrocław, Poznań, Gdańsk, etc.) represent proportional population weights with a long tail of smaller towns.

---

## 3. Relational Schema Architecture

The system defines entities declaratively in metadata / schemas so that all export layers (SQLite, PostgreSQL, CSV, Excel) operate generically over `Dataset` containers:

1. **`bases`**: Carrier/solvent bases for essential oils (`id`, `name`, `type`, `description`, `cost_per_ml`).
2. **`ingredients`**: Raw botanicals / single-note essences (`id`, `name`, `latin_name`, `origin_country`, `scent_note`).
3. **`tags`**: Descriptive tags (`id`, `name`, `category`).
4. **`actions`**: Therapeutic, cosmetic, and wellness effects (`id`, `name`, `type`).
5. **`oils`**: Finished products (`id`, `sku`, `name`, `base_id`, `capacity_ml`, `price_pln`, `production_cost_pln`, `category`, `description`, `created_at`).
6. **`oil_ingredients`**: Recipes (`oil_id`, `ingredient_id`, `percentage`).
7. **`oil_tags`**: Many-to-many tag associations (`oil_id`, `tag_id`).
8. **`oil_actions`**: Many-to-many therapeutic/marketing effects with intensity (`oil_id`, `action_id`, `intensity`).
9. **`customers`**: Customer demographics (`id`, `first_name`, `last_name`, `email`, `phone`, `city`, `voivodeship`, `postal_code`, `segment`, `registration_date`).
10. **`orders`**: Commercial orders (`id`, `order_number`, `customer_id`, `order_date`, `status`, `sales_channel`, `payment_method`, `total_amount_pln`, `discount_code`).
11. **`order_items`**: Basket line items (`id`, `order_id`, `oil_id`, `quantity`, `unit_price_pln`, `total_price_pln`).
12. **`reviews`**: Product ratings & opinions (`id`, `oil_id`, `customer_id`, `rating`, `review_date`, `comment`).

---

## 4. Generic Exporters (Separation of Schema and Serialization)
Exporters receive an in-memory dictionary/dataclass of table collections: `dict[str, list[dict[str, Any]]]`.
- **`CsvExporter`**: Writes standard CSV files in `data/raw/csv/`, UTF-8 encoded with header.
- **`ExcelExporter`**: Writes consolidated multi-sheet `data/raw/excel/olejki_calosc.xlsx` and individual table sheets.
- **`SqliteExporter`**: Creates schema DDL with proper PK/FK constraints and indexes, inserting rows into `data/db/olejki.db`.
- **`PostgresDumpExporter`**: Produces a clean `schema.sql` and `seed.sql` importable into PostgreSQL / Superset.

---

## 5. Parameterized Scaling and Reproducibility
Configuration file `seeds/config.yaml`:
```yaml
seed: 42
scale: 0.1 # 0.05 micro/test, 1.0 medium (~500 oils, 10k customers, 50k orders), 5.0+ large
dates:
  start: "2022-01-01"
  end: "2024-12-31"
distribution:
  pareto_alpha_products: 1.16
  pareto_alpha_customers: 1.25
  avg_basket_size: 2.3
```
