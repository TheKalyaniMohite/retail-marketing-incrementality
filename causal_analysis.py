"""
causal_analysis.py
==================
Causal Inference for the Retail Marketing Incrementality Project.

Two complementary methods:
  1. Difference-in-Differences (DiD) — classic econometric regression
  2. Bayesian Structural Time-Series (CausalImpact) — Google's approach

Both estimate the INCREMENTAL LIFT of the December 2025 ad campaign
by comparing test cities to their twin controls.

Output:
  - Console: full statistical results
  - output/did_regression_summary.txt
  - output/causalimpact_{city}.png  (per-pair CausalImpact plots)
  - output/roi_summary.png
  - output/incremental_lift_summary.csv
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats

warnings.filterwarnings("ignore")

# ── configuration ────────────────────────────────────────────────────────────
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

CAMPAIGN_START = "2025-12-01"
PRE_PERIOD_END = "2025-11-30"
CAMPAIGN_BUDGET = 100_000  # $100k total campaign spend

COLOR_TEST    = "#E63946"
COLOR_CONTROL = "#457B9D"
COLOR_LIFT    = "#2A9D8F"
COLOR_GOLD    = "#E9C46A"

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
print(f"Loaded {len(df):,} rows\n")


# ══════════════════════════════════════════════════════════════════════════════
#  METHOD 1: DIFFERENCE-IN-DIFFERENCES (DiD)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("METHOD 1: DIFFERENCE-IN-DIFFERENCES (DiD)")
print("=" * 70)

# ── create DiD variables ─────────────────────────────────────────────────────
df["post"]      = (df["date"] >= CAMPAIGN_START).astype(int)
df["treatment"] = (df["group"] == "Test").astype(int)
df["did"]       = df["post"] * df["treatment"]  # interaction term

# ── DiD by twin pair ─────────────────────────────────────────────────────────
print("\n--- DiD Estimates by Twin Pair ---\n")

did_results = []

for pair in df["twin_pair"].unique():
    pair_df = df[df["twin_pair"] == pair]
    test_city = pair_df[pair_df["group"] == "Test"]["city"].iloc[0]
    ctrl_city = pair_df[pair_df["group"] == "Control"]["city"].iloc[0]

    # Four group means
    test_pre  = pair_df[(pair_df["treatment"] == 1) & (pair_df["post"] == 0)]["daily_sales"].mean()
    test_post = pair_df[(pair_df["treatment"] == 1) & (pair_df["post"] == 1)]["daily_sales"].mean()
    ctrl_pre  = pair_df[(pair_df["treatment"] == 0) & (pair_df["post"] == 0)]["daily_sales"].mean()
    ctrl_post = pair_df[(pair_df["treatment"] == 0) & (pair_df["post"] == 1)]["daily_sales"].mean()

    # DiD estimator = (Test_post - Test_pre) - (Control_post - Control_pre)
    did_estimate = (test_post - test_pre) - (ctrl_post - ctrl_pre)
    lift_pct = did_estimate / ctrl_post * 100

    # Incremental revenue over December (31 days)
    incremental_rev = did_estimate * 31

    did_results.append({
        "Twin Pair":           f"{test_city} / {ctrl_city}",
        "Test City":           test_city,
        "Control City":        ctrl_city,
        "Test Pre":            round(test_pre, 2),
        "Test Post":           round(test_post, 2),
        "Control Pre":         round(ctrl_pre, 2),
        "Control Post":        round(ctrl_post, 2),
        "DiD Estimate ($/day)": round(did_estimate, 2),
        "Lift %":              round(lift_pct, 2),
        "Incremental Rev ($)": round(incremental_rev, 2),
    })

    print(f"  {test_city:15s} vs {ctrl_city:10s}  |  "
          f"DiD = ${did_estimate:,.0f}/day  |  Lift = {lift_pct:.1f}%  |  "
          f"Inc. Rev = ${incremental_rev:,.0f}")

did_df = pd.DataFrame(did_results)

# ── Pooled OLS DiD regression ────────────────────────────────────────────────
print("\n--- Pooled OLS DiD Regression ---\n")

try:
    import statsmodels.api as sm

    # Y = b0 + b1*Treatment + b2*Post + b3*(Treatment x Post) + e
    X = df[["treatment", "post", "did"]].copy()
    X = sm.add_constant(X)
    y = df["daily_sales"]

    model = sm.OLS(y, X).fit(cov_type="HC1")  # heteroscedasticity-robust SEs
    print(model.summary2().tables[1].to_string())

    # Save regression output
    with open(os.path.join(OUTPUT_DIR, "did_regression_summary.txt"), "w") as f:
        f.write(str(model.summary()))
    print(f"\n  Saved: did_regression_summary.txt")

    did_coeff = model.params["did"]
    did_pval  = model.pvalues["did"]
    did_ci    = model.conf_int().loc["did"]
    print(f"\n  DiD coefficient (b3): ${did_coeff:,.2f} per day")
    print(f"  95% CI: [${did_ci[0]:,.2f}, ${did_ci[1]:,.2f}]")
    print(f"  p-value: {did_pval:.2e}")
    print(f"  Interpretation: The campaign caused an average increase of "
          f"${did_coeff:,.0f}/day across all test cities.")
    HAS_STATSMODELS = True

except ImportError:
    print("  [WARN] statsmodels not installed. Skipping OLS regression.")
    print("  Install with: pip install statsmodels")
    HAS_STATSMODELS = False
    did_coeff = did_df["DiD Estimate ($/day)"].mean()


# ══════════════════════════════════════════════════════════════════════════════
#  METHOD 2: BAYESIAN STRUCTURAL TIME-SERIES (CausalImpact-style)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("METHOD 2: BAYESIAN STRUCTURAL TIME-SERIES (CausalImpact-Style)")
print("=" * 70)

# We implement a lightweight CausalImpact approach:
#   1. Fit a linear model on the pre-period: Test_sales ~ Control_sales
#   2. Use the model to PREDICT what test sales WOULD have been in December
#      (the counterfactual) using the actual control sales as input.
#   3. The difference (actual - predicted) is the causal effect.
#   4. Bootstrap prediction intervals for uncertainty quantification.

print("\nApproach: OLS counterfactual model with bootstrapped confidence bands\n")

ci_results = []

for pair in df["twin_pair"].unique():
    pair_df = df[df["twin_pair"] == pair].copy()
    test_city = pair_df[pair_df["group"] == "Test"]["city"].iloc[0]
    ctrl_city = pair_df[pair_df["group"] == "Control"]["city"].iloc[0]

    # Pivot to wide format
    test_ts = pair_df[pair_df["group"] == "Test"].set_index("date")["daily_sales"]
    ctrl_ts = pair_df[pair_df["group"] == "Control"].set_index("date")["daily_sales"]
    wide = pd.DataFrame({"test": test_ts, "control": ctrl_ts}).dropna()

    # Split pre / post
    pre  = wide.loc[:PRE_PERIOD_END]
    post = wide.loc[CAMPAIGN_START:]

    # ── Fit pre-period model: Test = a + b * Control ──
    slope, intercept, r, p, se = stats.linregress(pre["control"], pre["test"])

    # ── Predict counterfactual for December ──
    post["predicted"] = intercept + slope * post["control"]
    post["pointwise_effect"] = post["test"] - post["predicted"]

    # ── Bootstrap prediction intervals ──
    n_boot = 1000
    residuals = pre["test"] - (intercept + slope * pre["control"])
    boot_effects = []

    for _ in range(n_boot):
        # Resample residuals and refit
        boot_idx = np.random.choice(len(pre), size=len(pre), replace=True)
        boot_pre_ctrl = pre["control"].values[boot_idx]
        boot_pre_test = pre["test"].values[boot_idx]
        b_slope, b_intercept, _, _, _ = stats.linregress(boot_pre_ctrl, boot_pre_test)
        boot_pred = b_intercept + b_slope * post["control"].values
        boot_effect = post["test"].values - boot_pred
        boot_effects.append(boot_effect.sum())

    boot_effects = np.array(boot_effects)
    cum_effect = post["pointwise_effect"].sum()
    ci_lower = np.percentile(boot_effects, 2.5)
    ci_upper = np.percentile(boot_effects, 97.5)

    avg_daily_effect = post["pointwise_effect"].mean()
    lift_pct = avg_daily_effect / post["predicted"].mean() * 100

    ci_results.append({
        "Twin Pair":             f"{test_city} / {ctrl_city}",
        "Test City":             test_city,
        "Avg Daily Lift ($/day)": round(avg_daily_effect, 2),
        "Lift %":                round(lift_pct, 2),
        "Cumulative Lift ($)":   round(cum_effect, 2),
        "95% CI Lower ($)":      round(ci_lower, 2),
        "95% CI Upper ($)":      round(ci_upper, 2),
        "Pre-period R":          round(r, 4),
    })

    print(f"  {test_city:15s}  |  Avg lift = ${avg_daily_effect:,.0f}/day  "
          f"({lift_pct:+.1f}%)  |  Cumulative = ${cum_effect:,.0f}  "
          f"[{ci_lower:,.0f}, {ci_upper:,.0f}]")

    # ── CausalImpact-style plot (3 panels) ───────────────────────────────────
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

    # Panel 1: Actual vs Predicted (Counterfactual)
    ax = axes[0]
    ax.plot(wide.index, wide["test"], color=COLOR_TEST, linewidth=1.2,
            label=f"{test_city} (Actual)")

    # Pre-period fit
    pre_pred = intercept + slope * pre["control"]
    ax.plot(pre_pred.index, pre_pred.values, color=COLOR_CONTROL,
            linewidth=1.2, linestyle="--", alpha=0.7, label="Model Fit (Pre)")

    # Post-period counterfactual
    ax.plot(post.index, post["predicted"], color=COLOR_CONTROL, linewidth=2,
            linestyle="--", label="Counterfactual (Predicted)")
    ax.fill_between(post.index,
                    post["predicted"] - 2 * residuals.std(),
                    post["predicted"] + 2 * residuals.std(),
                    color=COLOR_CONTROL, alpha=0.15, label="95% CI")
    ax.axvline(pd.Timestamp(CAMPAIGN_START), color=COLOR_LIFT,
               linestyle="--", linewidth=1)
    ax.set_ylabel("Daily Sales ($)")
    ax.set_title(f"CausalImpact: {test_city} vs {ctrl_city}",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)

    # Panel 2: Pointwise Effect
    ax = axes[1]
    full_effect = pd.Series(0, index=pre.index)
    full_effect = pd.concat([full_effect, post["pointwise_effect"]])
    ax.plot(full_effect.index, full_effect.values, color=COLOR_TEST, linewidth=1.2)
    ax.fill_between(post.index, post["pointwise_effect"], 0,
                    where=post["pointwise_effect"] > 0,
                    color=COLOR_LIFT, alpha=0.3)
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.axvline(pd.Timestamp(CAMPAIGN_START), color=COLOR_LIFT,
               linestyle="--", linewidth=1)
    ax.set_ylabel("Pointwise Effect ($)")
    ax.set_title("Pointwise Causal Effect", fontsize=11)

    # Panel 3: Cumulative Effect
    ax = axes[2]
    cum = full_effect.cumsum()
    ax.plot(cum.index, cum.values, color=COLOR_TEST, linewidth=1.5)
    ax.fill_between(cum.index, cum.values, 0,
                    where=cum.values > 0, color=COLOR_LIFT, alpha=0.2)
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.axvline(pd.Timestamp(CAMPAIGN_START), color=COLOR_LIFT,
               linestyle="--", linewidth=1)
    ax.set_ylabel("Cumulative Effect ($)")
    ax.set_title("Cumulative Causal Effect", fontsize=11)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())

    fig.tight_layout()
    fname = f"causalimpact_{test_city.replace(' ', '_')}.png"
    fig.savefig(os.path.join(OUTPUT_DIR, fname))
    plt.close(fig)
    print(f"            Saved: {fname}")

ci_df = pd.DataFrame(ci_results)


# ══════════════════════════════════════════════════════════════════════════════
#  COMBINED RESULTS & ROI
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("COMBINED RESULTS & ROI ANALYSIS")
print("=" * 70)

# Merge DiD and CausalImpact results
summary = pd.DataFrame({
    "City":                  ci_df["Test City"],
    "DiD Lift ($/day)":      did_df["DiD Estimate ($/day)"],
    "CI Lift ($/day)":       ci_df["Avg Daily Lift ($/day)"],
    "DiD Lift %":            did_df["Lift %"],
    "CI Lift %":             ci_df["Lift %"],
    "CI Cumulative ($)":     ci_df["Cumulative Lift ($)"],
    "CI 95% Lower ($)":      ci_df["95% CI Lower ($)"],
    "CI 95% Upper ($)":      ci_df["95% CI Upper ($)"],
})

print("\n--- Per-City Summary ---\n")
print(summary.to_string(index=False))

# Aggregate
total_incremental = ci_df["Cumulative Lift ($)"].sum()
total_ci_lower    = ci_df["95% CI Lower ($)"].sum()
total_ci_upper    = ci_df["95% CI Upper ($)"].sum()
avg_lift_pct      = ci_df["Lift %"].mean()
roi               = (total_incremental - CAMPAIGN_BUDGET) / CAMPAIGN_BUDGET * 100
roi_lower         = (total_ci_lower - CAMPAIGN_BUDGET) / CAMPAIGN_BUDGET * 100
roi_upper         = (total_ci_upper - CAMPAIGN_BUDGET) / CAMPAIGN_BUDGET * 100

print(f"\n--- Aggregate Metrics ---\n")
print(f"  Total Incremental Revenue:  ${total_incremental:,.0f}")
print(f"  95% CI:                     [${total_ci_lower:,.0f}, ${total_ci_upper:,.0f}]")
print(f"  Average Lift:               {avg_lift_pct:.1f}%")
print(f"  Campaign Budget:            ${CAMPAIGN_BUDGET:,}")
print(f"  ROI:                        {roi:,.0f}%")
print(f"  ROI 95% CI:                 [{roi_lower:,.0f}%, {roi_upper:,.0f}%]")

# ── Save summary CSV ─────────────────────────────────────────────────────────
summary.to_csv(os.path.join(OUTPUT_DIR, "incremental_lift_summary.csv"), index=False)
print(f"\n  Saved: incremental_lift_summary.csv")

# ── ROI visualization ────────────────────────────────────────────────────────
print("\nGenerating ROI summary chart...")

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Left: Incremental Revenue by City
ax = axes[0]
cities = ci_df["Test City"]
revenues = ci_df["Cumulative Lift ($)"]
ci_errors = [
    revenues - ci_df["95% CI Lower ($)"],
    ci_df["95% CI Upper ($)"] - revenues,
]
bars = ax.barh(cities, revenues, color=COLOR_LIFT, alpha=0.85, edgecolor="white")
ax.errorbar(revenues, cities, xerr=ci_errors, fmt="none",
            ecolor="#333", capsize=4, linewidth=1.2)
ax.set_xlabel("Incremental Revenue ($)")
ax.set_title("Incremental Revenue by City (December 2025)",
             fontsize=13, fontweight="bold")

# Add value labels
for bar, val in zip(bars, revenues):
    ax.text(val - 500, bar.get_y() + bar.get_height() / 2,
            f"${val:,.0f}", va="center", ha="right", fontsize=9,
            fontweight="bold", color="white")

# Right: ROI waterfall
ax = axes[1]
labels = ["Campaign\nCost", "Incremental\nRevenue", "Net\nProfit"]
values = [-CAMPAIGN_BUDGET, total_incremental, total_incremental - CAMPAIGN_BUDGET]
colors_bar = [COLOR_TEST, COLOR_LIFT, COLOR_GOLD]

bars = ax.bar(labels, values, color=colors_bar, edgecolor="white", width=0.5)
ax.axhline(0, color="gray", linewidth=0.8)
ax.set_ylabel("Amount ($)")
ax.set_title(f"Campaign ROI: {roi:,.0f}%", fontsize=13, fontweight="bold")

for bar, val in zip(bars, values):
    y_pos = val + 2000 if val > 0 else val - 5000
    ax.text(bar.get_x() + bar.get_width() / 2, y_pos,
            f"${val:+,.0f}", ha="center", fontsize=11, fontweight="bold")

fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "roi_summary.png"))
plt.close(fig)
print("  Saved: roi_summary.png")

# ── final summary ────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("CAUSAL ANALYSIS COMPLETE")
print("=" * 70)
print(f"\nAll outputs saved to: ./{OUTPUT_DIR}/")
print(f"\nKey takeaway: The $100k campaign generated ${total_incremental:,.0f} in")
print(f"incremental revenue across 5 test cities, yielding an ROI of {roi:,.0f}%.")
