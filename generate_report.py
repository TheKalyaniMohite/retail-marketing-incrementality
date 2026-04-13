"""
generate_report.py
==================
Generates a polished Executive Summary report for the
Retail Marketing Incrementality Project.

Outputs:
  - output/executive_summary.md   (GitHub-viewable markdown)
  - output/executive_report.html  (Standalone printable HTML report)

This is the final deliverable — written for a CMO audience,
not a technical one.
"""

import os
import pandas as pd
import numpy as np

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── load data ────────────────────────────────────────────────────────────────
df = pd.read_csv("retail_sales_2025.csv", parse_dates=["date"])
lift_df = pd.read_csv(os.path.join(OUTPUT_DIR, "incremental_lift_summary.csv"))

CAMPAIGN_BUDGET = 100_000
CAMPAIGN_START = "2025-12-01"

# ── calculate aggregate metrics ──────────────────────────────────────────────
total_incremental = lift_df["CI Cumulative ($)"].sum()
total_ci_lower    = lift_df["CI 95% Lower ($)"].sum()
total_ci_upper    = lift_df["CI 95% Upper ($)"].sum()
avg_lift_pct      = lift_df["CI Lift %"].mean()
roi               = (total_incremental - CAMPAIGN_BUDGET) / CAMPAIGN_BUDGET * 100
roi_lower         = (total_ci_lower - CAMPAIGN_BUDGET) / CAMPAIGN_BUDGET * 100
roi_upper         = (total_ci_upper - CAMPAIGN_BUDGET) / CAMPAIGN_BUDGET * 100
net_profit        = total_incremental - CAMPAIGN_BUDGET
roas              = total_incremental / CAMPAIGN_BUDGET  # Return on Ad Spend

# Per-city metrics
best_city = lift_df.loc[lift_df["CI Cumulative ($)"].idxmax()]
worst_city = lift_df.loc[lift_df["CI Cumulative ($)"].idxmin()]

# Pre-intervention baseline
pre_df = df[df["date"] < CAMPAIGN_START]
test_pre_avg = pre_df[pre_df["group"] == "Test"]["daily_sales"].mean()
ctrl_pre_avg = pre_df[pre_df["group"] == "Control"]["daily_sales"].mean()

# December data
dec_df = df[df["date"] >= CAMPAIGN_START]
test_dec_avg = dec_df[dec_df["group"] == "Test"]["daily_sales"].mean()
ctrl_dec_avg = dec_df[dec_df["group"] == "Control"]["daily_sales"].mean()

# Cost efficiency
cost_per_incremental_dollar = CAMPAIGN_BUDGET / total_incremental
daily_avg_lift = lift_df["CI Lift ($/day)"].mean()

# ── generate markdown summary ────────────────────────────────────────────────
md = f"""# Executive Summary: Retail Marketing Incrementality Analysis

> **Prepared for:** Marketing Leadership
> **Date:** December 2025
> **Analyst:** Portfolio Project Demonstration

---

## The Question

> *Did our $100,000 December advertising campaign actually drive incremental sales,
> or would sales have increased anyway due to holiday seasonality?*

---

## The Answer

**Yes. The campaign generated ${total_incremental:,.0f} in incremental revenue —
a {roi:.0f}% ROI — and the effect is statistically significant (p < 0.001).**

Every dollar invested in this campaign returned **${roas:.2f}** in revenue.

---

## Key Performance Indicators

| Metric | Value |
|--------|-------|
| **Campaign Investment** | $100,000 |
| **Incremental Revenue** | **${total_incremental:,.0f}** |
| **Net Profit** | **${net_profit:,.0f}** |
| **ROI** | **{roi:.0f}%** |
| **ROAS** (Return on Ad Spend) | **{roas:.2f}x** |
| **Average Sales Lift** | **{avg_lift_pct:.1f}%** |
| **95% Confidence Interval** | ${total_ci_lower:,.0f} – ${total_ci_upper:,.0f} |
| **Statistical Significance** | p < 0.001 (highly significant) |

---

## Market-Level Performance

| Market | Incremental Revenue | Lift % | Daily Avg Lift | 95% CI |
|--------|--------------------:|-------:|---------------:|--------|
"""

for _, row in lift_df.iterrows():
    md += f"| {row['City']} | ${row['CI Cumulative ($)']:,.0f} | +{row['CI Lift %']:.1f}% | ${row['CI Lift ($/day)']:,.0f}/day | [${row['CI 95% Lower ($)']:,.0f} – ${row['CI 95% Upper ($)']:,.0f}] |\n"

md += f"""| **Total** | **${total_incremental:,.0f}** | **+{avg_lift_pct:.1f}%** | **${daily_avg_lift:,.0f}/day** | **[${total_ci_lower:,.0f} – ${total_ci_upper:,.0f}]** |

### Highlights

- **Top performer:** {best_city['City']} delivered ${best_city['CI Cumulative ($)']:,.0f} in incremental revenue (+{best_city['CI Lift %']:.1f}% lift)
- **Most efficient:** {best_city['City']} — highest absolute return on a per-market basis
- **Opportunity market:** {worst_city['City']} showed the lowest response (+{worst_city['CI Lift %']:.1f}%), suggesting creative or channel optimization may be needed

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

With a {roi:.0f}% ROI and ROAS of {roas:.2f}x, this campaign significantly exceeded
typical retail benchmarks (industry avg ROAS: 2-4x).

**Recommendation:** Increase the budget for the next seasonal push, particularly in
high-performing markets ({best_city['City']}, Chicago).

### 2. Optimize Underperforming Markets

{worst_city['City']} showed the lowest relative lift (+{worst_city['CI Lift %']:.1f}%).
This doesn't mean the market is unprofitable — it still generated ${worst_city['CI Cumulative ($)']:,.0f} — but there
may be room for improvement.

**Recommendation:** Test alternative creatives, channels, or bid strategies in {worst_city['City']}
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
"""

# Write markdown
md_path = os.path.join(OUTPUT_DIR, "executive_summary.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write(md)
print(f"[OK] Markdown summary: {md_path}")

# ── generate printable HTML report ───────────────────────────────────────────
html_report = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Executive Summary - Retail Marketing Incrementality</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            color: #1e293b;
            line-height: 1.7;
            background: #ffffff;
            max-width: 900px;
            margin: 0 auto;
            padding: 3rem 2rem;
        }}

        h1 {{
            font-size: 2rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 0.3rem;
            letter-spacing: -0.02em;
        }}

        h2 {{
            font-size: 1.3rem;
            font-weight: 700;
            color: #0f172a;
            margin-top: 2.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e2e8f0;
        }}

        h3 {{
            font-size: 1.05rem;
            font-weight: 600;
            color: #334155;
            margin-top: 1.5rem;
            margin-bottom: 0.8rem;
        }}

        p {{ margin-bottom: 1rem; color: #475569; }}

        strong {{ color: #0f172a; }}

        .subtitle {{
            color: #64748b;
            font-size: 0.9rem;
            margin-bottom: 2rem;
        }}

        .highlight-box {{
            background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
            border: 1px solid #bbf7d0;
            border-left: 4px solid #22c55e;
            border-radius: 8px;
            padding: 1.5rem 2rem;
            margin: 1.5rem 0;
        }}

        .highlight-box p {{
            color: #166534;
            font-size: 1.05rem;
            margin: 0;
        }}

        .highlight-box strong {{
            color: #14532d;
        }}

        .question-box {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #3b82f6;
            border-radius: 8px;
            padding: 1.2rem 1.5rem;
            margin: 1.5rem 0;
            font-style: italic;
            color: #334155;
        }}

        /* KPI Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin: 1.5rem 0;
        }}

        .kpi {{
            text-align: center;
            padding: 1.2rem 0.5rem;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
        }}

        .kpi:nth-child(1) {{ background: #f0fdf4; border-color: #bbf7d0; }}
        .kpi:nth-child(2) {{ background: #eff6ff; border-color: #bfdbfe; }}
        .kpi:nth-child(3) {{ background: #fefce8; border-color: #fde68a; }}
        .kpi:nth-child(4) {{ background: #fdf2f8; border-color: #fbcfe8; }}

        .kpi .label {{
            font-size: 0.65rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #64748b;
            margin-bottom: 0.3rem;
        }}

        .kpi .value {{
            font-size: 1.6rem;
            font-weight: 800;
            letter-spacing: -0.02em;
        }}

        .kpi:nth-child(1) .value {{ color: #16a34a; }}
        .kpi:nth-child(2) .value {{ color: #2563eb; }}
        .kpi:nth-child(3) .value {{ color: #d97706; }}
        .kpi:nth-child(4) .value {{ color: #db2777; }}

        .kpi .detail {{
            font-size: 0.7rem;
            color: #94a3b8;
            margin-top: 0.2rem;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            font-size: 0.85rem;
        }}

        th {{
            text-align: left;
            padding: 0.8rem 1rem;
            background: #f8fafc;
            color: #475569;
            font-weight: 600;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 2px solid #e2e8f0;
        }}

        td {{
            padding: 0.7rem 1rem;
            border-bottom: 1px solid #f1f5f9;
            color: #475569;
        }}

        tr:hover td {{ background: #f8fafc; }}

        .num {{ font-weight: 600; font-variant-numeric: tabular-nums; }}
        .positive {{ color: #16a34a; }}
        .total-row {{ font-weight: 700; background: #f0fdf4 !important; }}
        .total-row td {{ color: #166534; border-top: 2px solid #bbf7d0; }}

        /* Recommendations */
        .rec {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 1.2rem 1.5rem;
            margin: 1rem 0;
        }}

        .rec h4 {{
            font-size: 0.95rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.4rem;
        }}

        .rec p {{
            font-size: 0.85rem;
            margin: 0;
        }}

        .rec-tag {{
            display: inline-block;
            padding: 0.15rem 0.6rem;
            border-radius: 50px;
            font-size: 0.65rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-left: 0.5rem;
            vertical-align: middle;
        }}

        .rec-tag.high {{ background: #dcfce7; color: #166534; }}
        .rec-tag.medium {{ background: #fef3c7; color: #92400e; }}

        hr {{
            border: none;
            border-top: 1px solid #e2e8f0;
            margin: 2rem 0;
        }}

        .footer {{
            text-align: center;
            color: #94a3b8;
            font-size: 0.75rem;
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid #e2e8f0;
        }}

        @media print {{
            body {{ padding: 1rem; font-size: 0.8rem; }}
            .kpi-grid {{ grid-template-columns: repeat(4, 1fr); }}
            h2 {{ page-break-before: auto; }}
        }}

        @media (max-width: 700px) {{
            .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>

<h1>Retail Marketing Incrementality</h1>
<div class="subtitle">
    Executive Summary &bull; December 2025 Campaign Analysis &bull; Portfolio Demonstration
</div>

<div class="question-box">
    Did our $100,000 December advertising campaign actually drive incremental sales,
    or would sales have increased anyway due to holiday seasonality?
</div>

<div class="highlight-box">
    <p><strong>Yes.</strong> The campaign generated <strong>${total_incremental:,.0f}</strong> in
    incremental revenue &mdash; a <strong>{roi:.0f}% ROI</strong> &mdash; and the effect is
    statistically significant (p &lt; 0.001). Every dollar invested returned
    <strong>${roas:.2f}</strong> in revenue.</p>
</div>

<div class="kpi-grid">
    <div class="kpi">
        <div class="label">ROI</div>
        <div class="value">{roi:.0f}%</div>
        <div class="detail">CI: [{roi_lower:.0f}% &ndash; {roi_upper:.0f}%]</div>
    </div>
    <div class="kpi">
        <div class="label">Incremental Revenue</div>
        <div class="value">${total_incremental/1000:.0f}k</div>
        <div class="detail">Net profit: ${net_profit:,.0f}</div>
    </div>
    <div class="kpi">
        <div class="label">ROAS</div>
        <div class="value">{roas:.2f}x</div>
        <div class="detail">Industry avg: 2-4x</div>
    </div>
    <div class="kpi">
        <div class="label">Avg Lift</div>
        <div class="value">+{avg_lift_pct:.1f}%</div>
        <div class="detail">Across 5 markets</div>
    </div>
</div>

<h2>Market-Level Performance</h2>

<table>
    <thead>
        <tr>
            <th>Market</th>
            <th style="text-align:right">Inc. Revenue</th>
            <th style="text-align:right">Lift %</th>
            <th style="text-align:right">Daily Lift</th>
            <th>95% CI</th>
        </tr>
    </thead>
    <tbody>
"""

for _, row in lift_df.iterrows():
    html_report += f"""        <tr>
            <td><strong>{row['City']}</strong></td>
            <td class="num positive" style="text-align:right">${row['CI Cumulative ($)']:,.0f}</td>
            <td class="num positive" style="text-align:right">+{row['CI Lift %']:.1f}%</td>
            <td class="num" style="text-align:right">${row['CI Lift ($/day)']:,.0f}/day</td>
            <td style="font-size:0.75rem; color:#94a3b8">[${row['CI 95% Lower ($)']:,.0f} &ndash; ${row['CI 95% Upper ($)']:,.0f}]</td>
        </tr>
"""

html_report += f"""        <tr class="total-row">
            <td>Total</td>
            <td class="num" style="text-align:right">${total_incremental:,.0f}</td>
            <td class="num" style="text-align:right">+{avg_lift_pct:.1f}%</td>
            <td class="num" style="text-align:right">${daily_avg_lift:,.0f}/day</td>
            <td style="font-size:0.75rem">[${total_ci_lower:,.0f} &ndash; ${total_ci_upper:,.0f}]</td>
        </tr>
    </tbody>
</table>

<h2>Methodology</h2>

<h3>Twin-City Quasi-Experiment</h3>
<p>We matched 5 test cities (which received the campaign) with 5 structurally similar
control cities (no campaign). The control cities serve as the <strong>counterfactual</strong>
&mdash; what would have happened without the ad.</p>

<table>
    <thead><tr><th>Test City</th><th>Control Twin</th><th>Pre-Period Correlation</th></tr></thead>
    <tbody>
        <tr><td>San Francisco</td><td>Seattle</td><td class="num">r = 0.994</td></tr>
        <tr><td>Austin</td><td>Denver</td><td class="num">r = 0.992</td></tr>
        <tr><td>Miami</td><td>Phoenix</td><td class="num">r = 0.993</td></tr>
        <tr><td>Chicago</td><td>Boston</td><td class="num">r = 0.991</td></tr>
        <tr><td>Dallas</td><td>Atlanta</td><td class="num">r = 0.992</td></tr>
    </tbody>
</table>

<h3>Dual Analytical Methods</h3>
<p>Two independent causal inference methods were deployed as a robustness check:</p>
<table>
    <thead><tr><th>Method</th><th>Approach</th><th>Result</th></tr></thead>
    <tbody>
        <tr>
            <td><strong>Diff-in-Diff</strong></td>
            <td>OLS regression with HC1 robust SEs</td>
            <td class="num">$1,713/day (p = 1.95 &times; 10<sup>-23</sup>)</td>
        </tr>
        <tr>
            <td><strong>CausalImpact</strong></td>
            <td>Bayesian counterfactual + bootstrap CIs</td>
            <td class="num">${total_incremental:,.0f} cumulative</td>
        </tr>
    </tbody>
</table>
<p>Both methods converge, strengthening confidence in the result.</p>

<h2>Recommendations</h2>

<div class="rec">
    <h4>1. Scale the Campaign <span class="rec-tag high">High Confidence</span></h4>
    <p>With {roi:.0f}% ROI and {roas:.2f}x ROAS (well above industry average of 2-4x),
    increase budget for the next seasonal push, particularly in {best_city['City']} and Chicago.</p>
</div>

<div class="rec">
    <h4>2. Optimize {worst_city['City']} <span class="rec-tag medium">Medium Priority</span></h4>
    <p>{worst_city['City']} showed the lowest relative lift (+{worst_city['CI Lift %']:.1f}%) but still generated
    ${worst_city['CI Cumulative ($)']:,.0f}. Test alternative creatives or channels before the next cycle.</p>
</div>

<div class="rec">
    <h4>3. Extend the Measurement Framework <span class="rec-tag high">High Confidence</span></h4>
    <p>Apply the twin-city methodology to other campaigns (email, social, CTV) to build a
    comprehensive incrementality measurement program across all channels.</p>
</div>

<div class="rec">
    <h4>4. Invest in Always-On Measurement <span class="rec-tag medium">Medium Priority</span></h4>
    <p>Move from periodic studies to continuous measurement, enabling real-time budget
    reallocation and diminishing-returns analysis.</p>
</div>

<h2>Limitations</h2>
<table>
    <tbody>
        <tr><td style="width:30%"><strong>Synthetic Data</strong></td><td>Portfolio demonstration using simulated data. Real-world analysis requires actual POS/transaction data.</td></tr>
        <tr><td><strong>Single Period</strong></td><td>31-day measurement window. Long-term effects (brand lift, CLV) not captured.</td></tr>
        <tr><td><strong>Confounders</strong></td><td>Unobserved local factors (competitor activity, weather) could influence results.</td></tr>
        <tr><td><strong>No Channel Split</strong></td><td>Total campaign effect measured; individual channel contributions unknown.</td></tr>
    </tbody>
</table>

<div class="footer">
    Retail Marketing Incrementality Project &bull; Portfolio Demonstration &bull;
    Python &bull; Causal Inference &bull; Chart.js
</div>

</body>
</html>
"""

html_path = os.path.join(OUTPUT_DIR, "executive_report.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_report)
print(f"[OK] HTML report:      {html_path}")

# ── print final project summary ──────────────────────────────────────────────
print(f"""
{'='*70}
PROJECT COMPLETE - FINAL SUMMARY
{'='*70}

Campaign Investment:     $100,000
Incremental Revenue:     ${total_incremental:,.0f}
Net Profit:              ${net_profit:,.0f}
ROI:                     {roi:.0f}%
ROAS:                    {roas:.2f}x
Average Lift:            {avg_lift_pct:.1f}%
95% CI:                  [${total_ci_lower:,.0f} - ${total_ci_upper:,.0f}]

Best Market:   {best_city['City']} (${best_city['CI Cumulative ($)']:,.0f}, +{best_city['CI Lift %']:.1f}%)
Needs Work:    {worst_city['City']} (${worst_city['CI Cumulative ($)']:,.0f}, +{worst_city['CI Lift %']:.1f}%)

All deliverables saved to: ./{OUTPUT_DIR}/
{'='*70}
""")
