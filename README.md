# Retail Marketing Incrementality Project

## Note
This project uses synthetic data modeled after real US retail trends. It let me validate the causal inference model with a known "ground truth" before applying it to real data. The simulation covers a $100k campaign across 10 major US markets.

> 🔗 **[Live Dashboard](https://thekalyanimohite.github.io/retail-marketing-incrementality/)**

> **Goal:** Figure out if a $100k ad campaign actually drove new sales, or if the revenue would have come in anyway.

---

## Project Status

| Step | Description | Status |
|------|-------------|--------|
| 1 | Data Generation (`data_generator.py`) | ✅ Complete |
| 2 | EDA & Pre-Intervention Validation (`eda_analysis.py`) | ✅ Complete |
| 3 | CausalImpact / Diff-in-Diff Modeling (`causal_analysis.py`) | ✅ Complete |
| 4 | Results Visualization & Dashboard (`build_dashboard.py`) | ✅ Complete |
| 5 | Executive Summary & ROI Calculation (`generate_report.py`) | ✅ Complete |

---

## Technical Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Language | Python 3.x | Data wrangling, modeling, charts |
| Data Generation | NumPy, Pandas | Synthetic daily sales data with realistic seasonality |
| EDA & Validation | Matplotlib, SciPy | Time-series plots, correlation checks, t-tests |
| Causal Inference | Statsmodels, SciPy | DiD regression (OLS), counterfactual model, bootstrap CIs |
| Dashboard | Chart.js, HTML/CSS/JS | Interactive dark-mode dashboard with live KPIs |
| Reporting | Python, HTML/CSS | Executive summary in markdown and printable HTML |
| Version Control | Git / GitHub | Portfolio-ready repository |

---

## Study Design

### Timeline
- **Baseline period:** January - November 2025
- **Ad campaign runs:** December 2025

### Twin-City Pairs

| Test City (Ad Campaign) | Control City (No Campaign) |
|--------------------------|----------------------------|
| San Francisco | Seattle |
| Austin | Denver |
| Miami | Phoenix |
| Chicago | Boston |
| Dallas | Atlanta |

### Data Schema (`retail_sales_2025.csv`)

| Column | Type | Description |
|--------|------|-------------|
| `date` | `YYYY-MM-DD` | Calendar date |
| `city` | string | City name |
| `group` | string | `Test` or `Control` |
| `twin_pair` | string | e.g., `San Francisco / Seattle` |
| `daily_sales` | float | Simulated daily retail sales ($) |

---

## Key Results

| Metric | Value |
|--------|-------|
| Total Incremental Revenue | **$259,324** |
| 95% Confidence Interval | [$248,992 – $269,880] |
| Average Lift Across Cities | **14.6%** |
| Campaign Budget | $100,000 |
| **Net Profit** | **$159,324** |
| **ROI** | **159%** |
| **ROAS** | **2.59x** (industry avg: 2-4x) |
| DiD p-value | 1.95 × 10⁻²³ (highly significant) |

---

## How to Run

```bash
cd "Retail Marketing Incrementality Project"

# Step 1 - Generate the dataset
python data_generator.py

# Step 2 - EDA and pre-intervention validation
python eda_analysis.py

# Step 3 - Causal inference (DiD + CausalImpact)
python causal_analysis.py

# Step 4 - Build interactive dashboard
python build_dashboard.py

# Step 5 - Generate executive summary and report
python generate_report.py

# Then open these in your browser:
#   output/dashboard.html          (interactive dashboard)
#   output/index.html   (printable executive summary)
```

All charts and results are saved to the `output/` folder.

---

## Project Structure

```
Retail Marketing Incrementality Project/
├── data_generator.py          # Step 1: Synthetic data generation
├── eda_analysis.py            # Step 2: EDA & pre-intervention validation
├── causal_analysis.py         # Step 3: DiD + CausalImpact modeling
├── build_dashboard.py         # Step 4: Interactive HTML dashboard
├── generate_report.py         # Step 5: Executive summary generation
├── retail_sales_2025.csv      # Generated dataset (3,650 rows)
├── README.md                  # This file
├── Interview_Prep.txt         # Interview Q&A cheat-sheet
└── output/
    ├── dashboard.html             # Interactive dark-mode dashboard
    ├── index.html      # Printable executive summary
    ├── executive_summary.md       # GitHub-viewable summary
    ├── incremental_lift_summary.csv
    ├── did_regression_summary.txt
    ├── combined_test_vs_control.png
    ├── scatter_pre_intervention.png
    ├── december_lift_comparison.png
    ├── roi_summary.png
    ├── causalimpact_*.png         # Per-city CausalImpact plots
    └── twin_pair_*.png            # Per-pair time-series plots
```

## The Business Case
**The problem:** Cookie-based tracking (like GA4) is becoming less reliable. We needed a way to answer a simple question: if we stop spending this $100k on ads, how much revenue do we actually lose?

**What I did:** I paired up similar cities (like San Francisco and Seattle) and only ran the ad campaign in one city from each pair. By comparing sales between the paired cities, I could isolate the actual effect of the ads. The result: a 14.6% sales lift and $259k in new revenue.