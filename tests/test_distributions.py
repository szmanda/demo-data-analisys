from datetime import date
import numpy as np
from src.generators.distributions import DistributionEngine

def test_pareto_distribution_skewness():
    rng = np.random.default_rng(42)
    engine = DistributionEngine(rng)
    n_items = 100
    sample_size = 10000
    samples = engine.pareto_sample_indices(n_items=n_items, size=sample_size, alpha=1.16)

    # Check top 20% of items capture significant volume (around 70-85%)
    top_20_count = np.sum(samples < 20)
    top_20_ratio = top_20_count / sample_size
    assert 0.65 <= top_20_ratio <= 0.90, f"Expected ~80/20 rule, got {top_20_ratio:.2f}"

def test_lognormal_pricing():
    rng = np.random.default_rng(42)
    engine = DistributionEngine(rng)
    prices = [engine.lognormal_price() for _ in range(1000)]
    assert min(prices) >= 15.0
    assert max(prices) <= 350.0
    # Median should hover around 45 PLN
    median_price = np.median(prices)
    assert 35.0 <= median_price <= 60.0

def test_basket_size_geometric():
    rng = np.random.default_rng(42)
    engine = DistributionEngine(rng)
    baskets = [engine.basket_size() for _ in range(1000)]
    assert min(baskets) == 1
    # Count how many are size 1 or 2
    small_baskets = sum(1 for b in baskets if b in (1, 2))
    assert small_baskets / len(baskets) > 0.60

def test_seasonality_and_hours():
    rng = np.random.default_rng(42)
    engine = DistributionEngine(rng)
    start = date(2023, 1, 1)
    end = date(2023, 12, 31)
    dates = [engine.random_date_with_seasonality(start, end) for _ in range(2000)]
    
    # November/December should have higher density than summer
    q4_count = sum(1 for d in dates if d.month in (11, 12))
    summer_count = sum(1 for d in dates if d.month in (7, 8))
    assert q4_count > summer_count * 1.5
