"""
eda_analysis.py
===============
Exploratory Data Analysis & Pre-Intervention Validation for the
Retail Marketing Incrementality Project.

What this script does:
  1. Loads retail_sales_2025.csv
  2. Generates 5 twin-pair time-series plots (Test vs Control)
  3. Computes pre-intervention (Jan-Nov) correlation for each twin pair
  4. Runs a paired t-test on pre-intervention weekly averages to confirm
     twins are statistically indistinguishable before the campaign
  5. Produces a summary statistics table
  6. Saves all figures to an `output/` folder

Output folder: ./output/
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats

# ── configuration ────────────────────────────────────────────────────────────
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

CAMPAIGN_START = "2025-12-01"
PRE_PERIOD_END = "2025-11-30"

# Color palette — professional, colorblind-friendly
COLOR_TEST    = "#E63946"   # warm red
COLOR_CONTROL = "#457B9D"   # steel blue
COLOR_LIFT    = "#2A9D8F"   # teal

plt.rcParams.update({
    "figure.dpi":       150,
    "figure.facecolor": "#FAFAFA",
    "axes.facecolor":   "#FAFAFA",
    "axes.grid":        True,
    "grid.alpha":       0.3,
    "font.family":      "sans-serif",
    "font.size":        10,
})

# ── load data ────────────────────────────────────────────────────────────────
df = pd.read_csv("retail_sales_2025.csv", parse_dates=["date"])
print(f"Loaded {len(df):,} rows  |  {df['city'].nunique()} cities  |  "
      f"{df['date'].min().date()} to {df['date'].max().date()}\n")

# ── derive twin pairs ───────────────────────────────────────────────────────
twin_pairs = df["twin_pair"].unique()

# ══════════════════════════════════════════════════════════════════════════════
# 1. SUMMARY STATISTICS
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("SUMMARY STATISTICS (Full Year)")
print("=" * 70)

summary = (
    df.groupby(["city", "group"])["daily_sales"]
    .agg(["mean", "std", "min", "max"])
    .round(2)
)
summary.columns = ["Mean", "Std Dev", "Min", "Max"]
print(summary.to_string())
print()

# ══════════════════════════════════════════════════════════════════════════════
# 2. TWIN-PAIR TIME-SERIES PLOTS (7-day rolling average for clarity)
# ══════════════════════════════════════════════════════════════════════════════
print("Generating twin-pair time-series plots...")

for pair in twin_pairs:
    pair_df = df[df["twin_pair"] == pair].copy()
    test_city = pair_df[pair_df["group"] == "Test"]["city"].iloc[0]
    ctrl_city = pair_df[pair_df["group"] == "Control"]["city"].iloc[0]

    fig, ax = plt.subplots(figsize=(14, 5))

    for city, color, label_group in [
        (test_city, COLOR_TEST, "Test"),
        (ctrl_city, COLOR_CONTROL, "Control"),
    ]:
        city_df = pair_df[pair_df["city"] == city].sort_values("date")
        # 7-day rolling mean smooths out daily noise
        rolling = city_df.set_index("date")["daily_sales"].rolling(7).mean()
        ax.plot(rolling.index, rolling.values, color=color, linewidth=1.5,
                label=f"{city} ({label_group})")

    # Shade the campaign period
    ax.axvspan(pd.Timestamp(CAMPAIGN_START), pd.Timestamp("2025-12-31"),
               color=COLOR_LIFT, alpha=0.12, label="Campaign Period")
    ax.axvline(pd.Timestamp(CAMPAIGN_START), color=COLOR_LIFT,
               linestyle="--", linewidth=1, alpha=0.7)

    ax.set_title(f"Twin Pair: {test_city} vs {ctrl_city}  (7-day Rolling Avg)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Daily Sales ($)")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    fig.tight_layout()

    fname = f"twin_pair_{test_city.replace(' ', '_')}_vs_{ctrl_city}.png"
    fig.savefig(os.path.join(OUTPUT_DIR, fname))
    plt.close(fig)
    print(f"  Saved: {fname}")

# ══════════════════════════════════════════════════════════════════════════════
# 3. PRE-INTERVENTION CORRELATION ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PRE-INTERVENTION CORRELATION (Jan - Nov 2025)")
print("=" * 70)

pre_df = df[df["date"] <= PRE_PERIOD_END].copy()

correlation_results = []

for pair in twin_pairs:
    pair_pre = pre_df[pre_df["twin_pair"] == pair]
    test_city = pair_pre[pair_pre["group"] == "Test"]["city"].iloc[0]
    ctrl_city = pair_pre[pair_pre["group"] == "Control"]["city"].iloc[0]

    # Weekly averages reduce noise for more meaningful correlation
    test_weekly = (
        pair_pre[pair_pre["group"] == "Test"]
        .set_index("date")["daily_sales"]
        .resample("W")
        .mean()
    )
    ctrl_weekly = (
        pair_pre[pair_pre["group"] == "Control"]
        .set_index("date")["daily_sales"]
        .resample("W")
        .mean()
    )

    # Align indices
    aligned = pd.DataFrame({"test": test_weekly, "control": ctrl_weekly}).dropna()

    r, p_corr = stats.pearsonr(aligned["test"], aligned["control"])
    correlation_results.append({
        "Twin Pair": f"{test_city} / {ctrl_city}",
        "Pearson r": round(r, 4),
        "p-value": f"{p_corr:.2e}",
        "Match Quality": "Excellent" if r > 0.95 else "Good" if r > 0.85 else "Fair",
    })

corr_df = pd.DataFrame(correlation_results)
print(corr_df.to_string(index=False))
print()

# ══════════════════════════════════════════════════════════════════════════════
# 4. PRE-INTERVENTION PAIRED T-TEST
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("PRE-INTERVENTION PAIRED T-TEST (Weekly Averages, Jan - Nov 2025)")
print("Should show NO significant difference (p > 0.05) between twins.")
print("=" * 70)

ttest_results = []

for pair in twin_pairs:
    pair_pre = pre_df[pre_df["twin_pair"] == pair]
    test_city = pair_pre[pair_pre["group"] == "Test"]["city"].iloc[0]
    ctrl_city = pair_pre[pair_pre["group"] == "Control"]["city"].iloc[0]

    test_weekly = (
        pair_pre[pair_pre["group"] == "Test"]
        .set_index("date")["daily_sales"]
        .resample("W")
        .mean()
    )
    ctrl_weekly = (
        pair_pre[pair_pre["group"] == "Control"]
        .set_index("date")["daily_sales"]
        .resample("W")
        .mean()
    )

    aligned = pd.DataFrame({"test": test_weekly, "control": ctrl_weekly}).dropna()

    t_stat, p_val = stats.ttest_rel(aligned["test"], aligned["control"])
    ttest_results.append({
        "Twin Pair": f"{test_city} / {ctrl_city}",
        "t-statistic": round(t_stat, 4),
        "p-value": round(p_val, 4),
        "Significant?": "YES (problem!)" if p_val < 0.05 else "No (good)",
    })

ttest_df = pd.DataFrame(ttest_results)
print(ttest_df.to_string(index=False))
print()

# ══════════════════════════════════════════════════════════════════════════════
# 5. COMBINED OVERVIEW PLOT: ALL PAIRS, TEST vs CONTROL AVERAGES
# ══════════════════════════════════════════════════════════════════════════════
print("Generating combined overview plot...")

fig, ax = plt.subplots(figsize=(14, 6))

# Average across all test cities and all control cities
test_avg = (
    df[df["group"] == "Test"]
    .groupby("date")["daily_sales"]
    .mean()
    .rolling(7)
    .mean()
)
ctrl_avg = (
    df[df["group"] == "Control"]
    .groupby("date")["daily_sales"]
    .mean()
    .rolling(7)
    .mean()
)

ax.plot(test_avg.index, test_avg.values, color=COLOR_TEST, linewidth=2,
        label="Test Cities (avg)")
ax.plot(ctrl_avg.index, ctrl_avg.values, color=COLOR_CONTROL, linewidth=2,
        label="Control Cities (avg)")

# Shade December
ax.axvspan(pd.Timestamp(CAMPAIGN_START), pd.Timestamp("2025-12-31"),
           color=COLOR_LIFT, alpha=0.12, label="Campaign Period")
ax.axvline(pd.Timestamp(CAMPAIGN_START), color=COLOR_LIFT,
           linestyle="--", linewidth=1, alpha=0.7)

# Annotate the lift
ax.annotate("Campaign\nStarts",
            xy=(pd.Timestamp(CAMPAIGN_START), test_avg.loc[CAMPAIGN_START]),
            xytext=(-80, 40), textcoords="offset points",
            fontsize=10, fontweight="bold", color=COLOR_LIFT,
            arrowprops=dict(arrowstyle="->", color=COLOR_LIFT, lw=1.5))

ax.set_title("All Twin Pairs Combined: Test vs Control  (7-day Rolling Avg)",
             fontsize=14, fontweight="bold")
ax.set_xlabel("Date")
ax.set_ylabel("Avg Daily Sales ($)")
ax.legend(loc="upper left", framealpha=0.9)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
ax.xaxis.set_major_locator(mdates.MonthLocator())
fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "combined_test_vs_control.png"))
plt.close(fig)
print("  Saved: combined_test_vs_control.png")

# ══════════════════════════════════════════════════════════════════════════════
# 6. SCATTER PLOT: PRE-INTERVENTION TEST vs CONTROL (per pair)
# ══════════════════════════════════════════════════════════════════════════════
print("Generating pre-intervention scatter plots...")

fig, axes = plt.subplots(1, 5, figsize=(22, 4.5), sharey=False)

for idx, pair in enumerate(twin_pairs):
    pair_pre = pre_df[pre_df["twin_pair"] == pair]
    test_city = pair_pre[pair_pre["group"] == "Test"]["city"].iloc[0]
    ctrl_city = pair_pre[pair_pre["group"] == "Control"]["city"].iloc[0]

    test_vals = pair_pre[pair_pre["group"] == "Test"].sort_values("date")["daily_sales"].values
    ctrl_vals = pair_pre[pair_pre["group"] == "Control"].sort_values("date")["daily_sales"].values

    ax = axes[idx]
    ax.scatter(ctrl_vals, test_vals, alpha=0.25, s=10, color=COLOR_TEST)

    # Fit line
    slope, intercept, r, _, _ = stats.linregress(ctrl_vals, test_vals)
    x_line = np.array([ctrl_vals.min(), ctrl_vals.max()])
    ax.plot(x_line, slope * x_line + intercept, color=COLOR_CONTROL,
            linewidth=1.5, label=f"r = {r:.3f}")

    # Perfect 45-degree line
    lims = [min(ctrl_vals.min(), test_vals.min()),
            max(ctrl_vals.max(), test_vals.max())]
    ax.plot(lims, lims, "--", color="gray", linewidth=0.8, alpha=0.5)

    ax.set_title(f"{test_city}\nvs {ctrl_city}", fontsize=9, fontweight="bold")
    ax.set_xlabel(f"{ctrl_city} ($)", fontsize=8)
    if idx == 0:
        ax.set_ylabel("Test City Sales ($)", fontsize=8)
    ax.legend(fontsize=8, loc="upper left")

fig.suptitle("Pre-Intervention Daily Sales: Test vs Control (Jan - Nov 2025)",
             fontsize=13, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "scatter_pre_intervention.png"),
            bbox_inches="tight")
plt.close(fig)
print("  Saved: scatter_pre_intervention.png")

# ══════════════════════════════════════════════════════════════════════════════
# 7. DECEMBER LIFT VISUALIZATION
# ══════════════════════════════════════════════════════════════════════════════
print("Generating December lift comparison...")

dec_df = df[df["date"] >= CAMPAIGN_START].copy()

fig, axes = plt.subplots(1, 5, figsize=(22, 4.5), sharey=False)

for idx, pair in enumerate(twin_pairs):
    pair_dec = dec_df[dec_df["twin_pair"] == pair]
    test_city = pair_dec[pair_dec["group"] == "Test"]["city"].iloc[0]
    ctrl_city = pair_dec[pair_dec["group"] == "Control"]["city"].iloc[0]

    test_dec = pair_dec[pair_dec["group"] == "Test"].sort_values("date")
    ctrl_dec = pair_dec[pair_dec["group"] == "Control"].sort_values("date")

    ax = axes[idx]
    ax.bar(test_dec["date"].dt.day - 0.2, test_dec["daily_sales"],
           width=0.4, color=COLOR_TEST, alpha=0.8, label=test_city)
    ax.bar(ctrl_dec["date"].dt.day + 0.2, ctrl_dec["daily_sales"],
           width=0.4, color=COLOR_CONTROL, alpha=0.8, label=ctrl_city)

    # Calculate avg lift
    avg_test = test_dec["daily_sales"].mean()
    avg_ctrl = ctrl_dec["daily_sales"].mean()
    lift_pct = (avg_test - avg_ctrl) / avg_ctrl * 100

    ax.set_title(f"{test_city} vs {ctrl_city}\nLift: +{lift_pct:.1f}%",
                 fontsize=9, fontweight="bold")
    ax.set_xlabel("Dec Day", fontsize=8)
    if idx == 0:
        ax.set_ylabel("Daily Sales ($)", fontsize=8)
    ax.legend(fontsize=7, loc="upper left")

fig.suptitle("December 2025 Campaign Period: Test vs Control",
             fontsize=13, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "december_lift_comparison.png"),
            bbox_inches="tight")
plt.close(fig)
print("  Saved: december_lift_comparison.png")

# ── final summary ────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("EDA COMPLETE")
print("=" * 70)
print(f"All figures saved to: ./{OUTPUT_DIR}/")
print(f"Files generated:")
for f in sorted(os.listdir(OUTPUT_DIR)):
    fpath = os.path.join(OUTPUT_DIR, f)
    size_kb = os.path.getsize(fpath) / 1024
    print(f"  {f:45s} ({size_kb:.0f} KB)")
