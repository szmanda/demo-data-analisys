"""
Statistical distribution samplers implementing power laws, seasonal cycles,
and realistic demographic/economic properties for data mining.
"""
from datetime import date, datetime, timedelta
import math
import numpy as np


class DistributionEngine:
    def __init__(self, rng: np.random.Generator):
        self.rng = rng

    def pareto_sample_indices(self, n_items: int, size: int, alpha: float = 1.16) -> np.ndarray:
        """
        Samples indices in range [0, n_items) following a Zipf / Pareto power-law distribution.
        alpha parameter controls rank decay: w_i = (i + 1) ** (-alpha).
        alpha ~ 1.16 to 1.25 gives the classic 80/20 rule (top 20% of catalog = ~75-80% of sales).
        """
        if n_items <= 0 or size <= 0:
            return np.array([], dtype=int)
        
        ranks = np.arange(1, n_items + 1)
        weights = 1.0 / (ranks ** alpha)
        probabilities = weights / weights.sum()

        return self.rng.choice(n_items, size=size, p=probabilities)

    def lognormal_price(self, median: float = 45.0, sigma: float = 0.55, min_val: float = 15.0, max_val: float = 350.0) -> float:
        """
        Generates realistic prices with a log-normal distribution.
        Median is around typical artisan oil price, with a long tail of high-end precious oils.
        """
        mu = math.log(median)
        raw_price = float(self.rng.lognormal(mean=mu, sigma=sigma))
        clamped = max(min_val, min(max_val, raw_price))
        # Round to natural e-commerce ending (.99 or .00 or .50)
        endings = [0.0, 0.50, 0.90, 0.99]
        base_int = math.floor(clamped)
        ending = float(self.rng.choice(endings, p=[0.2, 0.2, 0.1, 0.5]))
        final_price = round(base_int + ending, 2)
        return max(min_val, final_price)

    def basket_size(self, p: float = 0.45, max_items: int = 15) -> int:
        """
        Generates number of items in a shopping basket.
        Geometric distribution: 1 item most common, 2-3 common, >5 rare.
        """
        size = int(self.rng.geometric(p=p))
        return min(max_items, size)

    def random_date_with_seasonality(
        self, start_date: date, end_date: date
    ) -> datetime:
        """
        Picks a date with realistic e-commerce seasonality:
        - Higher volume in Q4 (Black Friday, Christmas gifts)
        - Minor spring boost (March / Mother's Day)
        - Realistic hour distribution (peaking 18:00 - 22:00, low at 03:00 - 06:00)
        """
        total_days = (end_date - start_date).days
        if total_days <= 0:
            day_offset = 0
        else:
            while True:
                candidate_offset = int(self.rng.integers(0, total_days + 1))
                candidate_date = start_date + timedelta(days=candidate_offset)
                month = candidate_date.month

                # Seasonal weight
                if month in (11, 12):
                    weight = 2.2  # Q4 surge
                elif month in (2, 3, 5):
                    weight = 1.3  # Valentine's, Women's Day, Mother's Day
                elif month in (7, 8):
                    weight = 0.8  # Summer lull
                else:
                    weight = 1.0

                if self.rng.random() < (weight / 2.5):
                    day_offset = candidate_offset
                    break

        chosen_date = start_date + timedelta(days=day_offset)

        # Hour weights: peak in evening (19-22), low in late night (2-5)
        hours = np.arange(24)
        hour_weights = np.array([
            0.01, 0.005, 0.005, 0.002, 0.002, 0.005,
            0.015, 0.03, 0.04, 0.05, 0.05, 0.05,
            0.05, 0.05, 0.05, 0.05, 0.06, 0.07,
            0.09, 0.11, 0.11, 0.09, 0.06, 0.03
        ])
        hour_weights = hour_weights / hour_weights.sum()
        chosen_hour = int(self.rng.choice(hours, p=hour_weights))
        chosen_minute = int(self.rng.integers(0, 60))
        chosen_second = int(self.rng.integers(0, 60))

        return datetime(
            chosen_date.year,
            chosen_date.month,
            chosen_date.day,
            chosen_hour,
            chosen_minute,
            chosen_second,
        )
