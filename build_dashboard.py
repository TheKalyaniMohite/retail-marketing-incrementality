"""
build_dashboard.py
==================
Generates a self-contained, interactive HTML dashboard for the
Retail Marketing Incrementality Project.

Reads:  retail_sales_2025.csv, output/incremental_lift_summary.csv
Writes: output/dashboard.html

The dashboard is a single HTML file with embedded CSS, JS, and data.
No server required — just open in a browser.
Uses Chart.js (CDN) for interactive charts.
"""

import json
import os
import pandas as pd
import numpy as np
from scipy import stats

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── load data ────────────────────────────────────────────────────────────────
df = pd.read_csv("retail_sales_2025.csv", parse_dates=["date"])
lift_df = pd.read_csv(os.path.join(OUTPUT_DIR, "incremental_lift_summary.csv"))

CAMPAIGN_START = "2025-12-01"
CAMPAIGN_BUDGET = 100_000

# ── prepare chart data ───────────────────────────────────────────────────────

# 1) Combined test vs control (7-day rolling avg)
test_avg = (
    df[df["group"] == "Test"]
    .groupby("date")["daily_sales"].mean()
    .rolling(7).mean().dropna()
)
ctrl_avg = (
    df[df["group"] == "Control"]
    .groupby("date")["daily_sales"].mean()
    .rolling(7).mean().dropna()
)

combined_dates = [d.strftime("%Y-%m-%d") for d in test_avg.index]
combined_test  = [round(v, 0) for v in test_avg.values]
combined_ctrl  = [round(v, 0) for v in ctrl_avg.values]

# 2) Per-pair December comparison
dec_df = df[df["date"] >= CAMPAIGN_START]
dec_comparison = {}
for pair in df["twin_pair"].unique():
    pair_dec = dec_df[dec_df["twin_pair"] == pair]
    test_city = pair_dec[pair_dec["group"] == "Test"]["city"].iloc[0]
    ctrl_city = pair_dec[pair_dec["group"] == "Control"]["city"].iloc[0]
    test_avg_dec = pair_dec[pair_dec["group"] == "Test"]["daily_sales"].mean()
    ctrl_avg_dec = pair_dec[pair_dec["group"] == "Control"]["daily_sales"].mean()
    dec_comparison[test_city] = {
        "test_avg":  round(test_avg_dec, 0),
        "ctrl_avg":  round(ctrl_avg_dec, 0),
        "ctrl_city": ctrl_city,
    }

# 3) Per-pair time series for individual twin charts
twin_series = {}
for pair in df["twin_pair"].unique():
    pair_df = df[df["twin_pair"] == pair]
    test_city = pair_df[pair_df["group"] == "Test"]["city"].iloc[0]
    ctrl_city = pair_df[pair_df["group"] == "Control"]["city"].iloc[0]

    test_ts = pair_df[pair_df["group"] == "Test"].sort_values("date")
    ctrl_ts = pair_df[pair_df["group"] == "Control"].sort_values("date")

    # 7-day rolling
    test_rolling = test_ts.set_index("date")["daily_sales"].rolling(7).mean().dropna()
    ctrl_rolling = ctrl_ts.set_index("date")["daily_sales"].rolling(7).mean().dropna()

    twin_series[test_city] = {
        "ctrl_city": ctrl_city,
        "dates": [d.strftime("%Y-%m-%d") for d in test_rolling.index],
        "test_vals": [round(v, 0) for v in test_rolling.values],
        "ctrl_vals": [round(v, 0) for v in ctrl_rolling.values],
    }

# 4) Aggregate KPIs
total_incremental = lift_df["CI Cumulative ($)"].sum()
avg_lift_pct = lift_df["CI Lift %"].mean()
roi = (total_incremental - CAMPAIGN_BUDGET) / CAMPAIGN_BUDGET * 100
total_ci_lower = lift_df["CI 95% Lower ($)"].sum()
total_ci_upper = lift_df["CI 95% Upper ($)"].sum()

# 5) City-level lift data for bar chart
city_lifts = []
for _, row in lift_df.iterrows():
    city_lifts.append({
        "city": row["City"],
        "cumulative": round(row["CI Cumulative ($)"], 0),
        "lift_pct": round(row["CI Lift %"], 1),
        "ci_lower": round(row["CI 95% Lower ($)"], 0),
        "ci_upper": round(row["CI 95% Upper ($)"], 0),
        "did_lift": round(row["DiD Lift ($/day)"], 0),
        "ci_lift": round(row["CI Lift ($/day)"], 0),
    })

# ── build HTML ───────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Interactive dashboard measuring the incremental lift of a $100k retail ad campaign using twin-city quasi-experiment and causal inference.">
    <title>Retail Marketing Incrementality Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.1.0/dist/chartjs-plugin-annotation.min.js"></script>
    <style>
        :root {{
            --bg-primary: #0a0e1a;
            --bg-secondary: #111827;
            --bg-card: rgba(17, 24, 39, 0.7);
            --bg-glass: rgba(255, 255, 255, 0.03);
            --border-glass: rgba(255, 255, 255, 0.08);
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-teal: #2dd4bf;
            --accent-red: #f43f5e;
            --accent-blue: #3b82f6;
            --accent-gold: #f59e0b;
            --accent-purple: #a78bfa;
            --accent-green: #22c55e;
            --gradient-teal: linear-gradient(135deg, #2dd4bf 0%, #0d9488 100%);
            --gradient-red: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%);
            --gradient-blue: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            --gradient-gold: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            --shadow-lg: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            --shadow-glow-teal: 0 0 40px rgba(45, 212, 191, 0.15);
            --shadow-glow-red: 0 0 40px rgba(244, 63, 94, 0.15);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }}

        /* Animated background gradient */
        body::before {{
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background:
                radial-gradient(ellipse at 20% 50%, rgba(45, 212, 191, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 20%, rgba(59, 130, 246, 0.06) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 80%, rgba(168, 85, 247, 0.05) 0%, transparent 50%);
            z-index: 0;
            pointer-events: none;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            position: relative;
            z-index: 1;
        }}

        /* ── Header ─────────────────────────────────────── */
        .header {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 2.5rem 0;
        }}

        .header-badge {{
            display: inline-block;
            padding: 0.4rem 1.2rem;
            background: rgba(45, 212, 191, 0.1);
            border: 1px solid rgba(45, 212, 191, 0.3);
            border-radius: 50px;
            color: var(--accent-teal);
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-bottom: 1.2rem;
        }}

        .header h1 {{
            font-size: 2.8rem;
            font-weight: 800;
            background: linear-gradient(135deg, #f1f5f9 0%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.6rem;
            letter-spacing: -0.02em;
        }}

        .header p {{
            color: var(--text-secondary);
            font-size: 1.1rem;
            font-weight: 300;
        }}

        .header p strong {{
            color: var(--accent-teal);
            font-weight: 600;
        }}

        /* ── KPI Cards ──────────────────────────────────── */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }}

        .kpi-card {{
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-glass);
            border-radius: 16px;
            padding: 1.8rem;
            position: relative;
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .kpi-card:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
        }}

        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            border-radius: 16px 16px 0 0;
        }}

        .kpi-card:nth-child(1)::before {{ background: var(--gradient-teal); }}
        .kpi-card:nth-child(2)::before {{ background: var(--gradient-blue); }}
        .kpi-card:nth-child(3)::before {{ background: var(--gradient-gold); }}
        .kpi-card:nth-child(4)::before {{ background: var(--gradient-red); }}

        .kpi-card:nth-child(1):hover {{ box-shadow: var(--shadow-glow-teal); }}
        .kpi-card:nth-child(4):hover {{ box-shadow: var(--shadow-glow-red); }}

        .kpi-label {{
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--text-muted);
            margin-bottom: 0.6rem;
        }}

        .kpi-value {{
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: 0.3rem;
        }}

        .kpi-card:nth-child(1) .kpi-value {{ color: var(--accent-teal); }}
        .kpi-card:nth-child(2) .kpi-value {{ color: var(--accent-blue); }}
        .kpi-card:nth-child(3) .kpi-value {{ color: var(--accent-gold); }}
        .kpi-card:nth-child(4) .kpi-value {{ color: var(--accent-red); }}

        .kpi-detail {{
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}

        .kpi-detail .ci {{
            color: var(--text-muted);
            font-size: 0.7rem;
        }}

        /* ── Chart Section ──────────────────────────────── */
        .chart-section {{
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-glass);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            transition: box-shadow 0.3s ease;
        }}

        .chart-section:hover {{
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}

        .chart-title {{
            font-size: 1.2rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
        }}

        .chart-subtitle {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
        }}

        .chart-container {{
            position: relative;
            height: 380px;
        }}

        .chart-container.short {{
            height: 320px;
        }}

        /* ── Grid Layouts ───────────────────────────────── */
        .grid-2 {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 2rem;
            margin-bottom: 2rem;
        }}

        .grid-3 {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        /* ── Twin Pair Selector ─────────────────────────── */
        .twin-selector {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }}

        .twin-btn {{
            padding: 0.5rem 1.2rem;
            border: 1px solid var(--border-glass);
            border-radius: 8px;
            background: var(--bg-glass);
            color: var(--text-secondary);
            font-family: 'Inter', sans-serif;
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.25s ease;
        }}

        .twin-btn:hover {{
            border-color: var(--accent-teal);
            color: var(--accent-teal);
            background: rgba(45, 212, 191, 0.08);
        }}

        .twin-btn.active {{
            border-color: var(--accent-teal);
            color: var(--accent-teal);
            background: rgba(45, 212, 191, 0.12);
            box-shadow: 0 0 15px rgba(45, 212, 191, 0.1);
        }}

        /* ── Results Table ──────────────────────────────── */
        .results-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }}

        .results-table th {{
            text-align: left;
            padding: 1rem 1.2rem;
            color: var(--text-muted);
            font-weight: 600;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            border-bottom: 1px solid var(--border-glass);
        }}

        .results-table td {{
            padding: 1rem 1.2rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
            color: var(--text-secondary);
        }}

        .results-table tr:hover td {{
            background: rgba(255, 255, 255, 0.02);
            color: var(--text-primary);
        }}

        .results-table .num {{
            font-weight: 600;
            font-variant-numeric: tabular-nums;
        }}

        .results-table .positive {{
            color: var(--accent-teal);
        }}

        /* ── Methodology Badge ──────────────────────────── */
        .method-badges {{
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }}

        .method-badge {{
            display: flex;
            align-items: center;
            gap: 0.8rem;
            padding: 1rem 1.5rem;
            background: var(--bg-glass);
            border: 1px solid var(--border-glass);
            border-radius: 12px;
            flex: 1;
            min-width: 280px;
        }}

        .method-badge .icon {{
            width: 44px;
            height: 44px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            flex-shrink: 0;
        }}

        .method-badge:nth-child(1) .icon {{
            background: rgba(59, 130, 246, 0.15);
        }}
        .method-badge:nth-child(2) .icon {{
            background: rgba(45, 212, 191, 0.15);
        }}

        .method-badge .info h4 {{
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 0.2rem;
        }}

        .method-badge .info p {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        /* ── Footer ─────────────────────────────────────── */
        .footer {{
            text-align: center;
            padding: 2rem 0;
            color: var(--text-muted);
            font-size: 0.75rem;
        }}

        .footer a {{
            color: var(--accent-teal);
            text-decoration: none;
        }}

        /* ── Animations ─────────────────────────────────── */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .animate-in {{
            animation: fadeInUp 0.6s ease-out forwards;
            opacity: 0;
        }}

        .delay-1 {{ animation-delay: 0.1s; }}
        .delay-2 {{ animation-delay: 0.2s; }}
        .delay-3 {{ animation-delay: 0.3s; }}
        .delay-4 {{ animation-delay: 0.4s; }}
        .delay-5 {{ animation-delay: 0.5s; }}
        .delay-6 {{ animation-delay: 0.6s; }}

        /* ── Responsive ─────────────────────────────────── */
        @media (max-width: 1024px) {{
            .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .grid-2 {{ grid-template-columns: 1fr; }}
            .grid-3 {{ grid-template-columns: 1fr; }}
            .header h1 {{ font-size: 2rem; }}
        }}

        @media (max-width: 600px) {{
            .kpi-grid {{ grid-template-columns: 1fr; }}
            .container {{ padding: 1rem; }}
            .header h1 {{ font-size: 1.5rem; }}
        }}
    </style>
</head>
<body>
<div class="container">

    <!-- Header -->
    <header class="header animate-in">
        <div class="header-badge">Portfolio Project</div>
        <h1>Retail Marketing Incrementality</h1>
        <p>Measuring the <strong>Incremental Lift</strong> of a $100k Ad Campaign &mdash; Twin-City Quasi-Experiment &amp; Causal Inference</p>
    </header>

    <!-- KPI Cards -->
    <div class="kpi-grid">
        <div class="kpi-card animate-in delay-1" id="kpi-roi">
            <div class="kpi-label">Campaign ROI</div>
            <div class="kpi-value" id="kpi-roi-val">0%</div>
            <div class="kpi-detail">95% CI: [{round(total_ci_lower - CAMPAIGN_BUDGET):,} &ndash; {round(total_ci_upper - CAMPAIGN_BUDGET):,}]</div>
        </div>
        <div class="kpi-card animate-in delay-2" id="kpi-revenue">
            <div class="kpi-label">Incremental Revenue</div>
            <div class="kpi-value" id="kpi-rev-val">$0</div>
            <div class="kpi-detail">
                Across 5 test cities in December
                <div class="ci">95% CI: [${round(total_ci_lower):,} &ndash; ${round(total_ci_upper):,}]</div>
            </div>
        </div>
        <div class="kpi-card animate-in delay-3" id="kpi-lift">
            <div class="kpi-label">Average Lift</div>
            <div class="kpi-value" id="kpi-lift-val">0%</div>
            <div class="kpi-detail">Sales increase vs. control cities</div>
        </div>
        <div class="kpi-card animate-in delay-4" id="kpi-pval">
            <div class="kpi-label">Statistical Significance</div>
            <div class="kpi-value" style="font-size: 1.6rem;">p &lt; 0.001</div>
            <div class="kpi-detail">DiD regression p = 1.95 &times; 10&sup2;&sup3;</div>
        </div>
    </div>

    <!-- Methodology Badges -->
    <div class="method-badges animate-in delay-3">
        <div class="method-badge">
            <div class="icon">&Delta;</div>
            <div class="info">
                <h4>Difference-in-Differences</h4>
                <p>OLS regression with HC1 robust standard errors &bull; Pooled estimate: $1,713/day</p>
            </div>
        </div>
        <div class="method-badge">
            <div class="icon">&fnof;</div>
            <div class="info">
                <h4>Bayesian Counterfactual (CausalImpact)</h4>
                <p>Structural time-series with 1,000-iteration bootstrap CIs</p>
            </div>
        </div>
    </div>

    <!-- Combined Time Series -->
    <div class="chart-section animate-in delay-4">
        <div class="chart-title">Test vs Control Cities &mdash; Full Year 2025</div>
        <div class="chart-subtitle">7-day rolling average &bull; Shaded region = December campaign period</div>
        <div class="chart-container">
            <canvas id="combinedChart"></canvas>
        </div>
    </div>

    <!-- Twin Pair Explorer -->
    <div class="chart-section animate-in delay-5">
        <div class="chart-title">Twin-Pair Explorer</div>
        <div class="chart-subtitle">Select a city pair to compare test and control performance</div>
        <div class="twin-selector" id="twinSelector"></div>
        <div class="chart-container">
            <canvas id="twinChart"></canvas>
        </div>
    </div>

    <!-- Lift by City + ROI -->
    <div class="grid-2 animate-in delay-5">
        <div class="chart-section" style="margin-bottom:0">
            <div class="chart-title">Incremental Revenue by City</div>
            <div class="chart-subtitle">CausalImpact cumulative estimates with 95% CI error bars</div>
            <div class="chart-container short">
                <canvas id="liftChart"></canvas>
            </div>
        </div>
        <div class="chart-section" style="margin-bottom:0">
            <div class="chart-title">Campaign Economics</div>
            <div class="chart-subtitle">$100k investment &rarr; $259k incremental revenue</div>
            <div class="chart-container short">
                <canvas id="roiChart"></canvas>
            </div>
        </div>
    </div>

    <!-- December Deep-Dive -->
    <div class="chart-section animate-in delay-5">
        <div class="chart-title">December Avg Daily Sales: Test vs Control</div>
        <div class="chart-subtitle">Grouped bar comparison showing lift in every test market</div>
        <div class="chart-container short">
            <canvas id="decChart"></canvas>
        </div>
    </div>

    <!-- Detailed Results Table -->
    <div class="chart-section animate-in delay-6">
        <div class="chart-title">Detailed City-Level Results</div>
        <div class="chart-subtitle">Comparing Diff-in-Diff and CausalImpact estimates side-by-side</div>
        <table class="results-table">
            <thead>
                <tr>
                    <th>City</th>
                    <th>DiD Lift ($/day)</th>
                    <th>CI Lift ($/day)</th>
                    <th>DiD Lift %</th>
                    <th>CI Lift %</th>
                    <th>Cumulative ($)</th>
                    <th>95% CI</th>
                </tr>
            </thead>
            <tbody>
"""

# Add table rows
for _, row in lift_df.iterrows():
    html += f"""                <tr>
                    <td style="font-weight:600; color:var(--text-primary)">{row['City']}</td>
                    <td class="num">${row['DiD Lift ($/day)']:,.0f}</td>
                    <td class="num">${row['CI Lift ($/day)']:,.0f}</td>
                    <td class="num positive">+{row['DiD Lift %']:.1f}%</td>
                    <td class="num positive">+{row['CI Lift %']:.1f}%</td>
                    <td class="num positive">${row['CI Cumulative ($)']:,.0f}</td>
                    <td class="num" style="font-size:0.75rem">[${row['CI 95% Lower ($)']:,.0f} &ndash; ${row['CI 95% Upper ($)']:,.0f}]</td>
                </tr>
"""

html += f"""            </tbody>
            <tfoot>
                <tr style="border-top: 2px solid var(--border-glass)">
                    <td style="font-weight:700; color:var(--accent-teal)">TOTAL</td>
                    <td class="num" style="color:var(--accent-teal)">${lift_df['DiD Lift ($/day)'].sum():,.0f}</td>
                    <td class="num" style="color:var(--accent-teal)">${lift_df['CI Lift ($/day)'].sum():,.0f}</td>
                    <td class="num" style="color:var(--accent-teal)">+{lift_df['DiD Lift %'].mean():.1f}%</td>
                    <td class="num" style="color:var(--accent-teal)">+{avg_lift_pct:.1f}%</td>
                    <td class="num" style="color:var(--accent-teal)">${total_incremental:,.0f}</td>
                    <td class="num" style="font-size:0.75rem; color:var(--accent-teal)">[${total_ci_lower:,.0f} &ndash; ${total_ci_upper:,.0f}]</td>
                </tr>
            </tfoot>
        </table>
    </div>

    <!-- Footer -->
    <footer class="footer">
        Retail Marketing Incrementality Project &bull; Portfolio Demo &bull; Built with Python, Chart.js &amp; Causal Inference
    </footer>
</div>

<script>
// ── Data ────────────────────────────────────────────────────────────────────
const combinedDates = {json.dumps(combined_dates)};
const combinedTest  = {json.dumps(combined_test)};
const combinedCtrl  = {json.dumps(combined_ctrl)};
const twinSeries    = {json.dumps(twin_series)};
const cityLifts     = {json.dumps(city_lifts)};
const decComparison = {json.dumps(dec_comparison)};

const CAMPAIGN_START_IDX = combinedDates.indexOf('2025-12-01');
const TOTAL_INCREMENTAL  = {round(total_incremental)};
const AVG_LIFT_PCT       = {round(avg_lift_pct, 1)};
const ROI_PCT            = {round(roi)};

// ── Chart.js global defaults ────────────────────────────────────────────────
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(255,255,255,0.05)';
Chart.defaults.font.family = "'Inter', sans-serif";

// ── Animated KPI counters ───────────────────────────────────────────────────
function animateValue(el, end, prefix='', suffix='', duration=1500) {{
    const start = 0;
    const startTime = performance.now();
    function update(currentTime) {{
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);  // ease-out cubic
        const current = Math.round(start + (end - start) * eased);
        el.textContent = prefix + current.toLocaleString() + suffix;
        if (progress < 1) requestAnimationFrame(update);
    }}
    requestAnimationFrame(update);
}}

setTimeout(() => {{
    animateValue(document.getElementById('kpi-roi-val'), ROI_PCT, '', '%');
    animateValue(document.getElementById('kpi-rev-val'), TOTAL_INCREMENTAL, '$', '');
    animateValue(document.getElementById('kpi-lift-val'), AVG_LIFT_PCT * 10, '', '%', 1500);
    // Fix lift to show decimal
    setTimeout(() => {{
        document.getElementById('kpi-lift-val').textContent = AVG_LIFT_PCT + '%';
    }}, 1600);
}}, 400);

// ── 1. Combined Time Series Chart ───────────────────────────────────────────
const combinedCtx = document.getElementById('combinedChart').getContext('2d');
new Chart(combinedCtx, {{
    type: 'line',
    data: {{
        labels: combinedDates,
        datasets: [
            {{
                label: 'Test Cities (avg)',
                data: combinedTest,
                borderColor: '#f43f5e',
                backgroundColor: 'rgba(244,63,94,0.05)',
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 4,
                tension: 0.3,
                fill: false,
            }},
            {{
                label: 'Control Cities (avg)',
                data: combinedCtrl,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59,130,246,0.05)',
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 4,
                tension: 0.3,
                fill: false,
            }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
            legend: {{ position: 'top', labels: {{ usePointStyle: true, padding: 20 }} }},
            annotation: {{
                annotations: {{
                    campaignLine: {{
                        type: 'line',
                        xMin: '2025-12-01',
                        xMax: '2025-12-01',
                        borderColor: 'rgba(45,212,191,0.6)',
                        borderWidth: 2,
                        borderDash: [6, 4],
                        label: {{
                            display: true,
                            content: 'Campaign Start',
                            position: 'start',
                            backgroundColor: 'rgba(45,212,191,0.15)',
                            color: '#2dd4bf',
                            font: {{ size: 11, weight: '600' }},
                            padding: 6,
                        }}
                    }},
                    campaignBox: {{
                        type: 'box',
                        xMin: '2025-12-01',
                        xMax: '2025-12-31',
                        backgroundColor: 'rgba(45,212,191,0.06)',
                        borderWidth: 0,
                    }}
                }}
            }}
        }},
        scales: {{
            x: {{
                type: 'category',
                ticks: {{
                    maxTicksLimit: 12,
                    callback: function(val, idx) {{
                        const d = new Date(this.getLabelForValue(val));
                        return d.toLocaleDateString('en-US', {{ month: 'short' }});
                    }}
                }}
            }},
            y: {{
                ticks: {{ callback: v => '$' + v.toLocaleString() }}
            }}
        }}
    }}
}});

// ── 2. Twin Pair Explorer ───────────────────────────────────────────────────
const twinCtx = document.getElementById('twinChart').getContext('2d');
let twinChart = null;
const twinCities = Object.keys(twinSeries);

// Build selector buttons
const selectorEl = document.getElementById('twinSelector');
twinCities.forEach((city, i) => {{
    const btn = document.createElement('button');
    btn.className = 'twin-btn' + (i === 0 ? ' active' : '');
    btn.textContent = city + ' vs ' + twinSeries[city].ctrl_city;
    btn.onclick = () => {{
        document.querySelectorAll('.twin-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        updateTwinChart(city);
    }};
    selectorEl.appendChild(btn);
}});

function updateTwinChart(testCity) {{
    const data = twinSeries[testCity];
    if (twinChart) twinChart.destroy();

    twinChart = new Chart(twinCtx, {{
        type: 'line',
        data: {{
            labels: data.dates,
            datasets: [
                {{
                    label: testCity + ' (Test)',
                    data: data.test_vals,
                    borderColor: '#f43f5e',
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    tension: 0.3,
                }},
                {{
                    label: data.ctrl_city + ' (Control)',
                    data: data.ctrl_vals,
                    borderColor: '#3b82f6',
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    tension: 0.3,
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            interaction: {{ mode: 'index', intersect: false }},
            plugins: {{
                legend: {{ position: 'top', labels: {{ usePointStyle: true, padding: 20 }} }},
                annotation: {{
                    annotations: {{
                        campaignLine: {{
                            type: 'line',
                            xMin: '2025-12-01', xMax: '2025-12-01',
                            borderColor: 'rgba(45,212,191,0.6)',
                            borderWidth: 2, borderDash: [6, 4],
                            label: {{
                                display: true, content: 'Campaign',
                                position: 'start',
                                backgroundColor: 'rgba(45,212,191,0.15)',
                                color: '#2dd4bf',
                                font: {{ size: 10, weight: '600' }}, padding: 4,
                            }}
                        }},
                        campaignBox: {{
                            type: 'box',
                            xMin: '2025-12-01', xMax: '2025-12-31',
                            backgroundColor: 'rgba(45,212,191,0.06)',
                            borderWidth: 0,
                        }}
                    }}
                }}
            }},
            scales: {{
                x: {{ ticks: {{ maxTicksLimit: 12,
                    callback: function(val) {{
                        const d = new Date(this.getLabelForValue(val));
                        return d.toLocaleDateString('en-US', {{ month: 'short' }});
                    }}
                }} }},
                y: {{ ticks: {{ callback: v => '$' + v.toLocaleString() }} }},
            }}
        }}
    }});
}}
updateTwinChart(twinCities[0]);

// ── 3. Lift by City (Horizontal Bar) ────────────────────────────────────────
const liftCtx = document.getElementById('liftChart').getContext('2d');
new Chart(liftCtx, {{
    type: 'bar',
    data: {{
        labels: cityLifts.map(c => c.city),
        datasets: [{{
            label: 'Incremental Revenue ($)',
            data: cityLifts.map(c => c.cumulative),
            backgroundColor: [
                'rgba(45,212,191,0.8)',
                'rgba(59,130,246,0.8)',
                'rgba(245,158,11,0.8)',
                'rgba(168,85,250,0.8)',
                'rgba(244,63,94,0.8)',
            ],
            borderRadius: 6,
            borderSkipped: false,
        }}]
    }},
    options: {{
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
            legend: {{ display: false }},
        }},
        scales: {{
            x: {{ ticks: {{ callback: v => '$' + (v/1000).toFixed(0) + 'k' }} }},
            y: {{ grid: {{ display: false }} }},
        }}
    }}
}});

// ── 4. ROI Waterfall ────────────────────────────────────────────────────────
const roiCtx = document.getElementById('roiChart').getContext('2d');
new Chart(roiCtx, {{
    type: 'bar',
    data: {{
        labels: ['Campaign Cost', 'Incremental Revenue', 'Net Profit'],
        datasets: [{{
            data: [-100000, {round(total_incremental)}, {round(total_incremental - CAMPAIGN_BUDGET)}],
            backgroundColor: [
                'rgba(244,63,94,0.8)',
                'rgba(45,212,191,0.8)',
                'rgba(245,158,11,0.8)',
            ],
            borderRadius: 6,
            borderSkipped: false,
        }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
            legend: {{ display: false }},
        }},
        scales: {{
            y: {{ ticks: {{ callback: v => '$' + (v/1000).toFixed(0) + 'k' }} }},
            x: {{ grid: {{ display: false }} }},
        }}
    }}
}});

// ── 5. December Grouped Bar ─────────────────────────────────────────────────
const decCtx = document.getElementById('decChart').getContext('2d');
const decCities = Object.keys(decComparison);
new Chart(decCtx, {{
    type: 'bar',
    data: {{
        labels: decCities,
        datasets: [
            {{
                label: 'Test City (with campaign)',
                data: decCities.map(c => decComparison[c].test_avg),
                backgroundColor: 'rgba(244,63,94,0.75)',
                borderRadius: 4,
            }},
            {{
                label: 'Control City (no campaign)',
                data: decCities.map(c => decComparison[c].ctrl_avg),
                backgroundColor: 'rgba(59,130,246,0.75)',
                borderRadius: 4,
            }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
            legend: {{ position: 'top', labels: {{ usePointStyle: true, padding: 20 }} }},
        }},
        scales: {{
            y: {{ ticks: {{ callback: v => '$' + v.toLocaleString() }} }},
            x: {{ grid: {{ display: false }} }},
        }}
    }}
}});
</script>
</body>
</html>
"""

# ── write ────────────────────────────────────────────────────────────────────
output_path = os.path.join(OUTPUT_DIR, "dashboard.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"[OK] Dashboard generated: {output_path}")
print(f"     Open in your browser to view.")
