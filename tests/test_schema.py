import pytest
from src.schema import get_aroma_schema, DataType

def test_schema_tables():
    schema = get_aroma_schema()
    expected_tables = {
        "bases", "ingredients", "tags", "actions",
        "oils", "oil_ingredients", "oil_tags", "oil_actions",
        "customers", "orders", "order_items", "reviews"
    }
    assert set(schema.tables.keys()) == expected_tables

def test_table_columns_and_keys():
    schema = get_aroma_schema()
    oils = schema.get_table("oils")
    assert oils is not None
    assert "sku" in oils.column_names
    assert oils.primary_keys == ["id"]
    base_fk = oils.get_column("base_id")
    assert base_fk is not None
    assert base_fk.foreign_key == "bases.id"

def test_composite_keys():
    schema = get_aroma_schema()
    oil_tags = schema.get_table("oil_tags")
    assert set(oil_tags.primary_keys) == {"oil_id", "tag_id"}
