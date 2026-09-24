"""
Data generation pipeline producing relational dataset according to schema.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import math
from typing import Any
import numpy as np

from src.generators.distributions import DistributionEngine
from src.generators.vocabulary import Vocabulary


@dataclass
class GeneratorConfig:
    scale: float = 0.1
    seed: int = 42
    start_date: date = date(2022, 1, 1)
    end_date: date = date(2024, 12, 31)
    pareto_alpha_products: float = 1.16
    pareto_alpha_customers: float = 1.25


def generate_dataset(
    config: GeneratorConfig, vocab: Vocabulary
) -> dict[str, list[dict[str, Any]]]:
    """
    Generates a full relational dataset partitioned into dictionary of tables.
    Returns: dict mapping table_name -> list of row dicts.
    """
    rng = np.random.default_rng(config.seed)
    dist = DistributionEngine(rng)

    # 1. bases, ingredients, tags, actions directly from vocab
    bases = [dict(b) for b in vocab.bases]
    ingredients = [dict(i) for i in vocab.ingredients]
    tags = [dict(t) for t in vocab.tags]
    actions = [dict(a) for a in vocab.actions]

    # Calculate target counts based on master scale parameter
    n_oils = max(15, int(250 * config.scale))
    n_customers = max(30, int(3000 * config.scale))
    n_orders = max(60, int(15000 * config.scale))

    # 2. Oils generation
    oils: list[dict[str, Any]] = []
    oil_ingredients: list[dict[str, Any]] = []
    oil_tags: list[dict[str, Any]] = []
    oil_actions: list[dict[str, Any]] = []

    adjectives = [
        "Królewski", "Aksamitny", "Złocisty", "Krystaliczny", "Zmysłowy",
        "Poranny", "Wieczorny", "Górski", "Leśny", "Egzotyczny",
        "Harmonijny", "Słoneczny", "Odżywczy", "Czysty", "Mistyczny"
    ]
    categories = [
        ("Olejek Pojedynczy", 0.45),
        ("Mieszanka Olejków (Blend)", 0.40),
        ("Mgiełka Aromaterapeutyczna", 0.15)
    ]
    cat_names = [c[0] for c in categories]
    cat_weights = [c[1] for c in categories]

    capacities = [10, 15, 30, 50, 100]
    cap_weights = [0.45, 0.25, 0.15, 0.10, 0.05]

    oil_ing_counter = 1

    for oil_id in range(1, n_oils + 1):
        cat = str(rng.choice(cat_names, p=cat_weights))
        capacity = int(rng.choice(capacities, p=cap_weights))

        # Select base appropriate for product
        if cat == "Mgiełka Aromaterapeutyczna":
            # water or alcohol or hydrosol
            possible_bases = [b["id"] for b in bases if b["type"] in ("Hydrolat", "Rozpuszczalnik", "Hydrolat / Baza wodna")]
        else:
            possible_bases = [b["id"] for b in bases if b["type"] == "Olej nośnikowy"]
        
        if not possible_bases:
            possible_bases = [b["id"] for b in bases]
        
        base_id = int(rng.choice(possible_bases))
        base_obj = next(b for b in bases if b["id"] == base_id)

        # Pick ingredients for recipe
        if cat == "Olejek Pojedynczy":
            chosen_ing_ids = [int(rng.choice([i["id"] for i in ingredients]))]
            ing_obj = next(i for i in ingredients if i["id"] == chosen_ing_ids[0])
            name = f"Olejek {ing_obj['name']} {capacity}ml"
            percentages = [1.0]
        else:
            n_ing = int(rng.integers(2, 5))
            all_ing_ids = [i["id"] for i in ingredients]
            chosen_ing_ids = [int(x) for x in rng.choice(all_ing_ids, size=n_ing, replace=False)]
            adj = str(rng.choice(adjectives))
            theme_ing = next(i for i in ingredients if i["id"] == chosen_ing_ids[0])
            name = f"{adj} {theme_ing['name']} - {cat.split()[0]} {capacity}ml"
            raw_weights = rng.uniform(0.1, 1.0, size=n_ing)
            percentages = [round(float(p), 3) for p in (raw_weights / raw_weights.sum())]
            # normalize rounding
            percentages[-1] = round(1.0 - sum(percentages[:-1]), 3)

        # SKU
        sku = f"OLK-{capacity:03d}-{oil_id:04d}"

        # Production cost & Price
        base_cost = base_obj["cost_per_ml_pln"] * capacity
        packaging_cost = 4.50
        prod_cost = round(base_cost + packaging_cost + float(rng.uniform(3.0, 12.0)), 2)
        price = dist.lognormal_price(median=max(35.0, prod_cost * 2.2), min_val=prod_cost * 1.3)

        # Created date (some time before the main order history)
        catalog_start = config.start_date - timedelta(days=180)
        created_at = catalog_start + timedelta(days=int(rng.integers(0, 180)))

        desc = f"{name}. Naturalna kompozycja na bazie {base_obj['name']}."

        oils.append({
            "id": oil_id,
            "sku": sku,
            "name": name,
            "base_id": base_id,
            "capacity_ml": capacity,
            "price_pln": price,
            "production_cost_pln": prod_cost,
            "category": cat,
            "description": desc,
            "created_at": created_at.isoformat(),
        })

        # Recipes
        for ing_id, pct in zip(chosen_ing_ids, percentages):
            oil_ingredients.append({
                "id": oil_ing_counter,
                "oil_id": oil_id,
                "ingredient_id": ing_id,
                "percentage": pct,
            })
            oil_ing_counter += 1

        # Tags (1 to 4 tags per oil)
        n_tags = int(rng.integers(1, 4))
        chosen_tags = rng.choice([t["id"] for t in tags], size=n_tags, replace=False)
        for t_id in chosen_tags:
            oil_tags.append({"oil_id": oil_id, "tag_id": int(t_id)})

        # Actions (1 to 3 actions per oil with intensity)
        n_actions = int(rng.integers(1, 4))
        chosen_actions = rng.choice([a["id"] for a in actions], size=n_actions, replace=False)
        for a_id in chosen_actions:
            oil_actions.append({
                "oil_id": oil_id,
                "action_id": int(a_id),
                "intensity": int(rng.integers(2, 6)),  # 2 to 5
            })

    # 3. Customers generation
    customers: list[dict[str, Any]] = []
    city_weights = [c["weight"] for c in vocab.cities]
    city_weights = [w / sum(city_weights) for w in city_weights]

    segments = ["Indywidualny", "Lojalny Klubowicz", "Salon SPA & Wellness", "Okazjonalny"]
    segment_weights = [0.65, 0.15, 0.05, 0.15]

    for cust_id in range(1, n_customers + 1):
        is_female = rng.random() < 0.68  # Natural skew in cosmetics & aromatherapy
        first_name = str(rng.choice(vocab.first_names_female if is_female else vocab.first_names_male))
        last_name = str(rng.choice(vocab.last_names))
        
        # Polish female last name inflection check
        if is_female and last_name.endswith("ski"):
            last_name = last_name[:-3] + "ska"
        elif is_female and last_name.endswith("cki"):
            last_name = last_name[:-3] + "cka"

        email = f"{first_name.lower()}.{last_name.lower()}{cust_id}@example-poczta.pl"
        phone = f"+48 {rng.integers(500, 799)} {rng.integers(100, 999)} {rng.integers(100, 999)}"

        city_obj = vocab.cities[int(rng.choice(len(vocab.cities), p=city_weights))]
        postal_code = f"{city_obj['postal_code_prefix']}-{rng.integers(100, 999):03d}"
        segment = str(rng.choice(segments, p=segment_weights))

        # Registration date between config.start_date - 1 year and config.end_date
        total_reg_days = (config.end_date - (config.start_date - timedelta(days=365))).days
        reg_offset = int(rng.integers(0, max(1, total_reg_days)))
        reg_date = (config.start_date - timedelta(days=365)) + timedelta(days=reg_offset)

        customers.append({
            "id": cust_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "city": city_obj["name"],
            "voivodeship": city_obj["voivodeship"],
            "postal_code": postal_code,
            "segment": segment,
            "registration_date": reg_date.isoformat(),
        })

    # 4. Orders and Order Items generation
    orders: list[dict[str, Any]] = []
    order_items: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []

    # Sample customer purchases with power law (Pareto - loyal customers buy repeatedly)
    cust_indices = dist.pareto_sample_indices(
        n_items=n_customers, size=n_orders, alpha=config.pareto_alpha_customers
    )

    statuses = ["zrealizowane", "wysłane", "anulowane", "zwrócone"]
    status_weights = [0.88, 0.06, 0.03, 0.03]

    channels = ["Sklep online", "Stacjonarny", "Targi rzemieślnicze"]
    channel_weights = [0.82, 0.12, 0.06]

    payments = ["BLIK", "Karta płatnicza", "Przelew online (PayU)", "Za pobraniem"]
    payment_weights = [0.55, 0.25, 0.15, 0.05]

    discount_codes = [None, None, None, None, "AROMA10", "WIOSNA15", "VIP20", "NEWSLETTER"]
    discount_weights = [0.70, 0.10, 0.05, 0.05, 0.04, 0.03, 0.02, 0.01]

    order_item_counter = 1
    review_counter = 1

    review_templates = [
        "Zapach jest cudowny, bardzo relaksuje po ciężkim dniu.",
        "Świetna jakość! Zapach utrzymuje się w dyfuzorze przez wiele godzin.",
        "Piękne opakowanie, idealne na prezent. Na pewno zamówię ponownie.",
        "Dobra jakość, aczkolwiek zapach mógłby być nieco bardziej intensywny.",
        "Mój ulubiony olejek, stosuję codziennie przed snem.",
        "Bardzo szybka wysyłka, produkt zgodny z opisem i naturalny skład.",
        "Spodziewałam się trochę mocniejszego aromatu, ale ogólnie na plus.",
        "Absolutny hit, ból głowy mija po kilku minutach inhalacji!",
    ]

    # Pre-index oil prices and product popularity
    oil_id_lookup = {o["id"]: o for o in oils}

    for order_id in range(1, n_orders + 1):
        cust_id = int(cust_indices[order_id - 1]) + 1
        customer = customers[cust_id - 1]
        cust_reg_date = date.fromisoformat(customer["registration_date"])

        # Order date must be on or after customer registration date
        order_dt = dist.random_date_with_seasonality(
            max(config.start_date, cust_reg_date), config.end_date
        )

        status = str(rng.choice(statuses, p=status_weights))
        channel = str(rng.choice(channels, p=channel_weights))
        payment = str(rng.choice(payments, p=payment_weights))
        discount = rng.choice(discount_codes, p=discount_weights)
        discount_code = str(discount) if discount is not None else None

        # Determine items in basket using power laws
        basket_len = dist.basket_size(p=0.42, max_items=12)
        # SPA salons buy larger quantities
        if customer["segment"] == "Salon SPA & Wellness":
            basket_len = min(20, basket_len + int(rng.integers(3, 8)))

        # Popularity of oils follows Pareto
        chosen_oil_indices = dist.pareto_sample_indices(
            n_items=n_oils, size=basket_len, alpha=config.pareto_alpha_products
        )
        unique_oil_ids = list(dict.fromkeys([int(idx) + 1 for idx in chosen_oil_indices]))

        order_total = 0.0
        for o_id in unique_oil_ids:
            oil_obj = oil_id_lookup[o_id]
            # Quantity
            if customer["segment"] == "Salon SPA & Wellness":
                qty = int(rng.integers(2, 6))
            else:
                qty = 1 if rng.random() < 0.85 else int(rng.integers(2, 4))

            unit_price = oil_obj["price_pln"]
            item_total = round(unit_price * qty, 2)
            order_total += item_total

            order_items.append({
                "id": order_item_counter,
                "order_id": order_id,
                "oil_id": o_id,
                "quantity": qty,
                "unit_price_pln": unit_price,
                "total_price_pln": item_total,
            })
            order_item_counter += 1

            # Organic product reviews (~8% of delivered purchases get a review)
            if status == "zrealizowane" and rng.random() < 0.08:
                rating_weights = [0.03, 0.04, 0.08, 0.25, 0.60]  # E-commerce positive skew
                rating = int(rng.choice([1, 2, 3, 4, 5], p=rating_weights))
                rev_days = int(rng.integers(3, 21))
                rev_date = (order_dt + timedelta(days=rev_days)).date()
                if rev_date <= config.end_date:
                    comment = str(rng.choice(review_templates)) if rng.random() < 0.70 else None
                    reviews.append({
                        "id": review_counter,
                        "oil_id": o_id,
                        "customer_id": cust_id,
                        "rating": rating,
                        "review_date": rev_date.isoformat(),
                        "comment": comment,
                    })
                    review_counter += 1

        # Apply discount if any
        if discount_code == "AROMA10":
            order_total = round(order_total * 0.90, 2)
        elif discount_code == "WIOSNA15":
            order_total = round(order_total * 0.85, 2)
        elif discount_code in ("VIP20", "NEWSLETTER"):
            order_total = round(order_total * 0.80, 2)

        order_num = f"ZAM/{order_dt.year}/{order_dt.month:02d}/{order_id:06d}"

        orders.append({
            "id": order_id,
            "order_number": order_num,
            "customer_id": cust_id,
            "order_date": order_dt.isoformat(),
            "status": status,
            "sales_channel": channel,
            "payment_method": payment,
            "total_amount_pln": round(order_total, 2),
            "discount_code": discount_code,
        })

    return {
        "bases": bases,
        "ingredients": ingredients,
        "tags": tags,
        "actions": actions,
        "oils": oils,
        "oil_ingredients": oil_ingredients,
        "oil_tags": oil_tags,
        "oil_actions": oil_actions,
        "customers": customers,
        "orders": orders,
        "order_items": order_items,
        "reviews": reviews,
    }
