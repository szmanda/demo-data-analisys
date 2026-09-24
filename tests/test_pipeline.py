from datetime import date
from src.generators.vocabulary import load_vocabulary
from src.generators.pipeline import GeneratorConfig, generate_dataset
from src.schema import get_aroma_schema

def test_pipeline_generation_and_referential_integrity():
    vocab = load_vocabulary("seeds/base_data.yaml")
    config = GeneratorConfig(scale=0.05, seed=123)
    dataset = generate_dataset(config, vocab)

    # All tables must be populated
    schema = get_aroma_schema()
    for table_name in schema.tables.keys():
        assert table_name in dataset
        assert len(dataset[table_name]) > 0, f"Table {table_name} is empty"

    # Referential integrity checks
    base_ids = {b["id"] for b in dataset["bases"]}
    ingredient_ids = {i["id"] for i in dataset["ingredients"]}
    tag_ids = {t["id"] for t in dataset["tags"]}
    action_ids = {a["id"] for a in dataset["actions"]}
    oil_ids = {o["id"] for o in dataset["oils"]}
    customer_ids = {c["id"] for c in dataset["customers"]}
    order_ids = {ord["id"] for ord in dataset["orders"]}

    for oil in dataset["oils"]:
        assert oil["base_id"] in base_ids

    for oi in dataset["oil_ingredients"]:
        assert oi["oil_id"] in oil_ids
        assert oi["ingredient_id"] in ingredient_ids

    for ot in dataset["oil_tags"]:
        assert ot["oil_id"] in oil_ids
        assert ot["tag_id"] in tag_ids

    for oa in dataset["oil_actions"]:
        assert oa["oil_id"] in oil_ids
        assert oa["action_id"] in action_ids

    for order in dataset["orders"]:
        assert order["customer_id"] in customer_ids

    for item in dataset["order_items"]:
        assert item["order_id"] in order_ids
        assert item["oil_id"] in oil_ids

    for rev in dataset["reviews"]:
        assert rev["oil_id"] in oil_ids
        assert rev["customer_id"] in customer_ids

def test_reproducibility_with_seed():
    vocab = load_vocabulary("seeds/base_data.yaml")
    config1 = GeneratorConfig(scale=0.05, seed=999)
    config2 = GeneratorConfig(scale=0.05, seed=999)
    
    ds1 = generate_dataset(config1, vocab)
    ds2 = generate_dataset(config2, vocab)

    assert ds1["orders"][0]["order_number"] == ds2["orders"][0]["order_number"]
    assert ds1["orders"][0]["total_amount_pln"] == ds2["orders"][0]["total_amount_pln"]
