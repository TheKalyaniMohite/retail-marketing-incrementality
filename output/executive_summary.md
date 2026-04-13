# Executive Summary: Retail Marketing Incrementality Analysis

> **Prepared for:** Marketing Leadership
> **Date:** December 2025
> **Analyst:** Portfolio Project Demonstration

---

## The Question

> *Did our $100,000 December advertising campaign actually drive incremental sales,
> or would sales have increased anyway due to holiday seasonality?*

---

## The Answer

**Yes. The campaign generated $259,324 in incremental revenue —
a 159% ROI — and the effect is statistically significant (p < 0.001).**

Every dollar invested in this campaign returned **$2.59** in revenue.

---

## Key Performance Indicators

| Metric | Value |
|--------|-------|
| **Campaign Investment** | $100,000 |
| **Incremental Revenue** | **$259,324** |
| **Net Profit** | **$159,324** |
| **ROI** | **159%** |
| **ROAS** (Return on Ad Spend) | **2.59x** |
| **Average Sales Lift** | **14.6%** |
| **95% Confidence Interval** | $248,992 – $269,880 |
| **Statistical Significance** | p < 0.001 (highly significant) |

---

## Market-Level Performance

| Market | Incremental Revenue | Lift % | Daily Avg Lift | 95% CI |
|--------|--------------------:|-------:|---------------:|--------|
| San Francisco | $60,333 | +15.1% | $1,946/day | [$58,027 – $62,591] |
| Austin | $53,423 | +16.5% | $1,723/day | [$51,472 – $55,490] |
| Miami | $38,875 | +11.0% | $1,254/day | [$36,940 – $40,821] |
| Chicago | $58,044 | +15.7% | $1,872/day | [$55,780 – $60,364] |
| Dallas | $48,649 | +14.8% | $1,569/day | [$46,772 – $50,615] |
| **Total** | **$259,324** | **+14.6%** | **$1,673/day** | **[$248,992 – $269,880]** |

### Highlights

- **Top performer:** San Francisco delivered $60,333 in incremental revenue (+15.1% lift)
- **Most efficient:** San Francisco — highest absolute return on a per-market basis
- **Opportunity market:** Miami showed the lowest response (+11.0%), suggesting creative or channel optimization may be needed

---

## Methodology

### Study Design: Twin-City Quasi-Experiment

We used a **quasi-experimental design** with matched city pairs to isolate the campaign's
causal effect from seasonal trends:

| Design Element | Detail |
|----------------|--------|
| **Test Group** | 5 cities received the ad campaign (SF, Austin, Miami, Chicago, Dallas) |
| **Control Group** | 5 matched "twin" cities with no campaign (Seattle, Denver, Phoenix, Boston, Atlanta) |
| **Baseline Period** | January – November 2025 (11 months) |
| **Treatment Period** | December 2025 (31 days) |
| **Matching Quality** | Pearson r > 0.99 for all pairs pre-intervention |

### Analytical Approach

Two independent methods were used to estimate the causal effect, providing a robustness check:

1. **Difference-in-Differences (DiD)** — OLS regression with heteroscedasticity-robust
   standard errors. Pooled estimate: $1,713/day incremental lift (p = 1.95 x 10^-23).

2. **Bayesian Structural Time-Series (CausalImpact)** — Counterfactual prediction model
   with bootstrapped 95% confidence intervals (1,000 iterations). Both methods converge
   on the same conclusion.

### Pre-Intervention Validation

Before measuring the campaign effect, we validated that twin cities moved in lockstep:

- **Correlation:** All 5 pairs showed Pearson r > 0.99 (pre-intervention)
- **T-test:** No significant differences in any pair (all p > 0.05)
- **Visual inspection:** 7-day rolling averages confirmed parallel trends

This validation is critical — without it, any December difference could be attributed
to pre-existing divergence rather than the campaign.

---

## Recommendations

### 1. Scale the Campaign (High Confidence)

With a 159% ROI and ROAS of 2.59x, this campaign significantly exceeded
typical retail benchmarks (industry avg ROAS: 2-4x).

**Recommendation:** Increase the budget for the next seasonal push, particularly in
high-performing markets (San Francisco, Chicago).

### 2. Optimize Underperforming Markets

Miami showed the lowest relative lift (+11.0%).
This doesn't mean the market is unprofitable — it still generated $38,875 — but there
may be room for improvement.

**Recommendation:** Test alternative creatives, channels, or bid strategies in Miami
before the next campaign cycle.

### 3. Extend the Measurement Framework

The twin-city methodology proved highly effective and can be reused:

**Recommendation:** Apply this framework to future campaigns across other channels
(email, social, CTV) to build a comprehensive incrementality measurement program.

### 4. Invest in Always-On Measurement

This study measured a single pulse campaign. Continuous measurement would enable:
- Real-time budget reallocation
- Channel-level attribution
- Diminishing returns analysis

---

## Limitations & Caveats

1. **Synthetic data:** This analysis uses simulated data for portfolio demonstration.
   Real-world results would require actual POS/transaction data.

2. **Single campaign period:** Results reflect a 31-day window. Long-term effects
   (brand awareness, customer lifetime value) are not captured.

3. **Geographic confounders:** While twin cities were matched on key attributes,
   unobserved local factors (competitor promotions, weather) could influence results.

4. **No channel decomposition:** The analysis measures total campaign effect, not
   individual channel (search, display, social) contributions.

---

## Technical Appendix

| Component | Tool | File |
|-----------|------|------|
| Data Generation | Python, NumPy, Pandas | `data_generator.py` |
| EDA & Validation | Matplotlib, SciPy | `eda_analysis.py` |
| Causal Inference | Statsmodels, SciPy | `causal_analysis.py` |
| Dashboard | Chart.js, HTML/CSS/JS | `build_dashboard.py` |
| Executive Report | Python (this script) | `generate_report.py` |

### Files in `output/`

| File | Description |
|------|-------------|
| `dashboard.html` | Interactive dark-mode dashboard |
| `incremental_lift_summary.csv` | City-level results table |
| `did_regression_summary.txt` | Full OLS regression output |
| `combined_test_vs_control.png` | Aggregate time-series chart |
| `scatter_pre_intervention.png` | Pre-period twin validation |
| `december_lift_comparison.png` | December bar comparison |
| `causalimpact_*.png` | Per-city 3-panel CausalImpact plots |
| `roi_summary.png` | ROI waterfall chart |
| `executive_summary.md` | This document |
| `executive_report.html` | Printable HTML version |

---

*This analysis was conducted as a portfolio demonstration of marketing incrementality
measurement using causal inference techniques.*
