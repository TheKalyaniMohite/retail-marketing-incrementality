# Retail Marketing Incrementality Project

# Note: 
This project uses a High-Fidelity Synthetic Dataset modeled after real US retail trends. This approach allowed for a "Ground Truth" validation of the Causal Inference model, simulating a real-world $100k campaign across 10 major US markets.

> **Goal:** Measure the **Incremental Lift** of a \$100k digital ad campaign using a twin-city quasi-experiment and causal inference.

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
| Language | Python 3.x | Data engineering, modeling, visualization |
| Data Generation | NumPy, Pandas | Synthetic sales time-series with realistic patterns |
| EDA & Validation | Matplotlib, SciPy | Time-series plots, correlation, paired t-tests |
| Causal Inference | Statsmodels, SciPy | DiD regression (OLS), counterfactual modeling, bootstrap CIs |
| Dashboard | Chart.js, HTML/CSS/JS | Interactive dark-mode dashboard with animated KPIs |
| Reporting | Python, HTML/CSS | Executive summary (markdown + printable HTML) |
| Version Control | Git / GitHub | Portfolio-ready repository |

---

## Study Design

### Timeline
- **Baseline period:** January – November 2025
- **Intervention (ad campaign):** December 2025

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
| **ROAS** | **2.59x** (industry avg: 2–4x) |
| DiD p-value | 1.95 × 10⁻²³ (highly significant) |

---

## How to Run

```bash
cd "Retail Marketing Incrementality Project"

# Step 1 — Generate the dataset
python data_generator.py

# Step 2 — EDA & pre-intervention validation
python eda_analysis.py

# Step 3 — Causal inference (DiD + CausalImpact)
python causal_analysis.py

# Step 4 — Build interactive dashboard
python build_dashboard.py

# Step 5 — Generate executive summary & report
python generate_report.py

# Then open these in your browser:
#   output/dashboard.html          (interactive dashboard)
#   output/executive_report.html   (printable executive summary)
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
    ├── executive_report.html      # Printable executive summary
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

# The Business Case
The Problem: In a privacy-first world, traditional tracking (like GA4 cookies) often misses the true impact of marketing. We needed to know: If we stopped spending $100k, how much revenue would we actually lose?

The Solution: I built a Geo-Experimental Framework. By matching cities into "Twin Pairs" (like San Francisco and Seattle), we created a "Science Lab" environment to prove that our December ads caused a 14.6% sales lift, generating $259k in new revenue.