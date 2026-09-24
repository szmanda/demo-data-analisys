"""
Declarative schema metadata model for synthetic datasets.
Separates schema definitions from serialization/export logic.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class DataType(Enum):
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    TEXT = "TEXT"
    DATE = "DATE"
    DATETIME = "DATETIME"
    BOOLEAN = "BOOLEAN"


@dataclass(frozen=True)
class Column:
    name: str
    data_type: DataType
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None  # Format: "table_name.column_name"
    description: str = ""


@dataclass(frozen=True)
class TableSchema:
    name: str
    columns: list[Column]
    description: str = ""

    @property
    def primary_keys(self) -> list[str]:
        return [col.name for col in self.columns if col.primary_key]

    @property
    def column_names(self) -> list[str]:
        return [col.name for col in self.columns]

    def get_column(self, name: str) -> Optional[Column]:
        for col in self.columns:
            if col.name == name:
                return col
        return None


@dataclass
class DatabaseSchema:
    name: str
    tables: dict[str, TableSchema] = field(default_factory=dict)

    def add_table(self, table: TableSchema) -> None:
        self.tables[table.name] = table

    def get_table(self, name: str) -> Optional[TableSchema]:
        return self.tables.get(name)


def get_aroma_schema() -> DatabaseSchema:
    """Returns the official AromaData relational database schema."""
    db = DatabaseSchema(name="aroma_data")

    # 1. bases
    db.add_table(
        TableSchema(
            name="bases",
            description="Carrier/solvent bases for essential oils",
            columns=[
                Column("id", DataType.INTEGER, nullable=False, primary_key=True),
                Column("name", DataType.TEXT, nullable=False, description="Nazwa bazy (np. Olej Jojoba)"),
                Column("type", DataType.TEXT, nullable=False, description="Typ bazy (np. Olej roślinny, Alkohol)"),
                Column("description", DataType.TEXT, nullable=True),
                Column("cost_per_ml_pln", DataType.FLOAT, nullable=False),
            ],
        )
    )

    # 2. ingredients
    db.add_table(
        TableSchema(
            name="ingredients",
            description="Single botanicals and raw essential essences",
            columns=[
                Column("id", DataType.INTEGER, nullable=False, primary_key=True),
                Column("name", DataType.TEXT, nullable=False, description="Nazwa składnika po polsku"),
                Column("latin_name", DataType.TEXT, nullable=False, description="Nazwa botaniczna łacińska"),
                Column("origin_country", DataType.TEXT, nullable=False, description="Kraj pochodzenia"),
                Column("scent_note", DataType.TEXT, nullable=False, description="Nuta zapachowa: głowa, serce, baza"),
            ],
        )
    )

    # 3. tags
    db.add_table(
        TableSchema(
            name="tags",
            description="Descriptive tags for categorization and marketing",
            columns=[
                Column("id", DataType.INTEGER, nullable=False, primary_key=True),
                Column("name", DataType.TEXT, nullable=False, description="Nazwa tagu"),
                Column("category", DataType.TEXT, nullable=False, description="Kategoria tagu"),
            ],
        )
    )

    # 4. actions
    db.add_table(
        TableSchema(
            name="actions",
            description="Therapeutic, aesthetic and wellness actions",
            columns=[
                Column("id", DataType.INTEGER, nullable=False, primary_key=True),
                Column("name", DataType.TEXT, nullable=False, description="Działanie lecznicze lub pielęgnacyjne"),
                Column("type", DataType.TEXT, nullable=False, description="Typ: Lecznicze, Kosmetyczne, Aromaterapia"),
            ],
        )
    )

    # 5. oils
    db.add_table(
        TableSchema(
            name="oils",
            description="Finished commercial oil products",
            columns=[
                Column("id", DataType.INTEGER, nullable=False, primary_key=True),
                Column("sku", DataType.TEXT, nullable=False),
                Column("name", DataType.TEXT, nullable=False, description="Nazwa produktu handlowego"),
                Column("base_id", DataType.INTEGER, nullable=False, foreign_key="bases.id"),
                Column("capacity_ml", DataType.INTEGER, nullable=False),
                Column("price_pln", DataType.FLOAT, nullable=False),
                Column("production_cost_pln", DataType.FLOAT, nullable=False),
                Column("category", DataType.TEXT, nullable=False),
                Column("description", DataType.TEXT, nullable=True),
                Column("created_at", DataType.DATE, nullable=False),
            ],
        )
    )

    # 6. oil_ingredients (Recipe)
    db.add_table(
        TableSchema(
            name="oil_ingredients",
            description="Oil composition recipe linking oils to raw botanical ingredients",
            columns=[
                Column("id", DataType.INTEGER, nullable=False, primary_key=True),
                Column("oil_id", DataType.INTEGER, nullable=False, foreign_key="oils.id"),
                Column("ingredient_id", DataType.INTEGER, nullable=False, foreign_key="ingredients.id"),
                Column("percentage", DataType.FLOAT, nullable=False, description="Udział procentowy składnika (0.0 - 1.0)"),
            ],
        )
    )

    # 7. oil_tags
    db.add_table(
        TableSchema(
            name="oil_tags",
            description="Many-to-many relationship linking oils and descriptive tags",
            columns=[
                Column("oil_id", DataType.INTEGER, nullable=False, foreign_key="oils.id", primary_key=True),
                Column("tag_id", DataType.INTEGER, nullable=False, foreign_key="tags.id", primary_key=True),
            ],
        )
    )

    # 8. oil_actions
    db.add_table(
        TableSchema(
            name="oil_actions",
            description="Many-to-many relationship linking oils and wellness actions with intensity score",
            columns=[
                Column("oil_id", DataType.INTEGER, nullable=False, foreign_key="oils.id", primary_key=True),
                Column("action_id", DataType.INTEGER, nullable=False, foreign_key="actions.id", primary_key=True),
                Column("intensity", DataType.INTEGER, nullable=False, description="Siła działania w skali 1-5"),
            ],
        )
    )

    # 9. customers
    db.add_table(
        TableSchema(
            name="customers",
            description="Registered and guest clients",
            columns=[
                Column("id", DataType.INTEGER, nullable=False, primary_key=True),
                Column("first_name", DataType.TEXT, nullable=False),
                Column("last_name", DataType.TEXT, nullable=False),
                Column("email", DataType.TEXT, nullable=False),
                Column("phone", DataType.TEXT, nullable=True),
                Column("city", DataType.TEXT, nullable=False),
                Column("voivodeship", DataType.TEXT, nullable=False),
                Column("postal_code", DataType.TEXT, nullable=False),
                Column("segment", DataType.TEXT, nullable=False, description="Segment klienta: Indywidualny, Salon SPA, Lojalny, Hurtownik"),
                Column("registration_date", DataType.DATE, nullable=False),
            ],
        )
    )

    # 10. orders
    db.add_table(
        TableSchema(
            name="orders",
            description="Sales orders placed by customers",
            columns=[
                Column("id", DataType.INTEGER, nullable=False, primary_key=True),
                Column("order_number", DataType.TEXT, nullable=False),
                Column("customer_id", DataType.INTEGER, nullable=False, foreign_key="customers.id"),
                Column("order_date", DataType.DATETIME, nullable=False),
                Column("status", DataType.TEXT, nullable=False, description="zrealizowane, wysłane, anulowane, zwrócone"),
                Column("sales_channel", DataType.TEXT, nullable=False, description="Sklep online, Stacjonarny, Targi eko"),
                Column("payment_method", DataType.TEXT, nullable=False, description="BLIK, Karta, Przelew, Pobranie"),
                Column("total_amount_pln", DataType.FLOAT, nullable=False),
                Column("discount_code", DataType.TEXT, nullable=True),
            ],
        )
    )

    # 11. order_items
    db.add_table(
        TableSchema(
            name="order_items",
            description="Line items for each order",
            columns=[
                Column("id", DataType.INTEGER, nullable=False, primary_key=True),
                Column("order_id", DataType.INTEGER, nullable=False, foreign_key="orders.id"),
                Column("oil_id", DataType.INTEGER, nullable=False, foreign_key="oils.id"),
                Column("quantity", DataType.INTEGER, nullable=False),
                Column("unit_price_pln", DataType.FLOAT, nullable=False),
                Column("total_price_pln", DataType.FLOAT, nullable=False),
            ],
        )
    )

    # 12. reviews
    db.add_table(
        TableSchema(
            name="reviews",
            description="Product reviews and ratings left by customers",
            columns=[
                Column("id", DataType.INTEGER, nullable=False, primary_key=True),
                Column("oil_id", DataType.INTEGER, nullable=False, foreign_key="oils.id"),
                Column("customer_id", DataType.INTEGER, nullable=False, foreign_key="customers.id"),
                Column("rating", DataType.INTEGER, nullable=False),
                Column("review_date", DataType.DATE, nullable=False),
                Column("comment", DataType.TEXT, nullable=True),
            ],
        )
    )

    return db
