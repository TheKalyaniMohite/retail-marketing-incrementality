"""
data_generator.py
=================
Generates synthetic retail daily-sales data for a Marketing Incrementality study.

Twin-City Pairs (Test → Control):
    SF       → Seattle
    Austin   → Denver
    Miami    → Phoenix
    Chicago  → Boston
    Dallas   → Atlanta

Design choices
--------------
* Each twin pair shares the SAME baseline parameters (base sales, trend slope,
  seasonality amplitude) so they move in lock-step before the intervention,
  which is the core assumption behind the twin-city quasi-experiment.
* Gaussian noise is added independently per city so the twins are correlated
  but not identical — just like real-world counterparts.
* The December 2025 marketing push adds incremental lift ONLY to the 5 test
  cities, simulating a $100k ad campaign.

Output: retail_sales_2025.csv
"""

import numpy as np
import pandas as pd
from datetime import datetime

# ── reproducibility ──────────────────────────────────────────────────────────
np.random.seed(42)

# ── date range ───────────────────────────────────────────────────────────────
dates = pd.date_range(start="2025-01-01", end="2025-12-31", freq="D")
n_days = len(dates)

# ── twin-city configuration ─────────────────────────────────────────────────
# Each tuple: (test_city, control_city, base_daily_sales, trend_per_day,
#               seasonality_amplitude, noise_std)
twin_pairs = [
    ("San Francisco", "Seattle",  12000, 8.0, 2500, 400),
    ("Austin",        "Denver",    9500, 6.5, 2000, 350),
    ("Miami",         "Phoenix",  10500, 7.0, 2200, 380),
    ("Chicago",       "Boston",   11000, 7.5, 2400, 420),
    ("Dallas",        "Atlanta",   9800, 6.0, 1800, 360),
]

# ── marketing lift configuration (December 2025 only) ───────────────────────
CAMPAIGN_START = datetime(2025, 12, 1)
CAMPAIGN_END   = datetime(2025, 12, 31)

# Lift ramps up linearly over the first 7 days, then holds steady.
# Peak lift is a percentage of the city's base sales — varies by city to
# reflect market-specific ad effectiveness.
PEAK_LIFT_PCT = {
    "San Francisco": 0.18,   # 18 % lift
    "Austin":        0.22,   # 22 %
    "Miami":         0.15,   # 15 %
    "Chicago":       0.20,   # 20 %
    "Dallas":        0.17,   # 17 %
}
RAMP_DAYS = 7  # days for the lift to reach full strength


def _seasonality(day_of_year: np.ndarray, amplitude: float) -> np.ndarray:
    """Annual sinusoidal seasonality peaking around the holiday season (late Nov/Dec)."""
    # Phase shift so peak ≈ day 340 (early December)
    return amplitude * np.sin(2 * np.pi * (day_of_year - 80) / 365)


def _weekly_effect(day_of_week: np.ndarray, base: float) -> np.ndarray:
    """Weekend bump: Sat/Sun sales ~12-15 % higher than weekday average."""
    multiplier = np.where(day_of_week >= 5, 1.13, 1.0)
    return base * (multiplier - 1.0)


def _holiday_spike(dates_series: pd.DatetimeIndex, base: float) -> np.ndarray:
    """Extra spikes on major US retail holidays."""
    holidays = {
        # (month, day): multiplier on top of base
        (1, 1):  0.05,   # New Year's Day
        (2, 14): 0.08,   # Valentine's Day
        (5, 26): 0.10,   # Memorial Day (approx.)
        (7, 4):  0.12,   # Independence Day
        (9, 1):  0.10,   # Labor Day (approx.)
        (11, 27): 0.30,  # Thanksgiving (approx.)
        (11, 28): 0.45,  # Black Friday
        (12, 24): 0.25,  # Christmas Eve
        (12, 25): 0.15,  # Christmas Day
        (12, 31): 0.10,  # New Year's Eve
    }
    spike = np.zeros(len(dates_series))
    for (m, d), mult in holidays.items():
        mask = (dates_series.month == m) & (dates_series.day == d)
        spike[mask] = base * mult
    return spike


def _campaign_lift(dates_series: pd.DatetimeIndex, base: float,
                   lift_pct: float) -> np.ndarray:
    """
    Incremental sales lift during the December campaign.
    Ramps linearly over `RAMP_DAYS`, then holds at `lift_pct * base`.
    """
    lift = np.zeros(len(dates_series))
    peak_lift = lift_pct * base

    for i, dt in enumerate(dates_series):
        if CAMPAIGN_START <= dt <= CAMPAIGN_END:
            day_in_campaign = (dt - CAMPAIGN_START).days + 1
            ramp_factor = min(day_in_campaign / RAMP_DAYS, 1.0)
            lift[i] = peak_lift * ramp_factor

    return lift


# ── generate data ────────────────────────────────────────────────────────────
rows = []
day_of_year = dates.dayofyear.values
day_of_week = dates.dayofweek.values

for test_city, ctrl_city, base, trend, seas_amp, noise_std in twin_pairs:
    # Shared deterministic components (twins move together)
    trend_component = trend * np.arange(n_days)
    seas_component  = _seasonality(day_of_year, seas_amp)
    weekly_component = _weekly_effect(day_of_week, base)
    holiday_component = _holiday_spike(dates, base)

    for city, group in [(test_city, "Test"), (ctrl_city, "Control")]:
        # Independent noise per city
        noise = np.random.normal(0, noise_std, n_days)

        sales = (base
                 + trend_component
                 + seas_component
                 + weekly_component
                 + holiday_component
                 + noise)

        # Apply campaign lift ONLY to test cities
        if group == "Test":
            sales += _campaign_lift(dates, base, PEAK_LIFT_PCT[city])

        # Floor at zero (sales can't be negative)
        sales = np.maximum(sales, 0).round(2)

        for i, dt in enumerate(dates):
            rows.append({
                "date":       dt.strftime("%Y-%m-%d"),
                "city":       city,
                "group":      group,
                "twin_pair":  f"{test_city} / {ctrl_city}",
                "daily_sales": sales[i],
            })

# ── write to CSV ─────────────────────────────────────────────────────────────
df = pd.DataFrame(rows)
df.to_csv("retail_sales_2025.csv", index=False)

print(f"[OK] Generated retail_sales_2025.csv")
print(f"    Rows  : {len(df):,}")
print(f"    Cities: {df['city'].nunique()}")
print(f"    Date range: {df['date'].min()} to {df['date'].max()}")
print(f"\nSample rows:")
print(df.head(10).to_string(index=False))
