# Equity Trading Cost Analysis (TCA) Framework

**Python | Pandas | Plotly | Streamlit | Execution Simulation**

A practical transaction cost analysis framework built from 15+ years of institutional equity markets experience.

---

## Project Overview

This project simulates realistic institutional equity order flow and analyses execution quality across multiple strategies (Immediate, VWAP, VWAP-Dark, Careful). It measures implementation shortfall, venue performance, order size impact, and timing effects.

The interactive Streamlit dashboard allows users to explore how different execution approaches affect costs, helping to surface insights relevant to execution desks and best execution analysis.

**Related Project:** See [execution-quality-db](https://github.com/rosesparrow/execution-quality-db) for a SQL-based approach to execution quality analytics and database design in the same domain.

---

## Key Insights

- Patient VWAP strategies tend to reduce implementation shortfall for larger orders compared to aggressive execution
- Dark pool routing can provide measurable market impact savings on block orders
- Order size and arrival timing are significant drivers of execution quality

## Features

- Simulation of 200+ institutional-sized equity orders
- Four execution strategies with realistic multi-fill logic
- Implementation Shortfall as the primary performance metric
- Interactive Streamlit dashboard with filters and visualisations
- Analysis of venue routing (lit vs dark pools)

## Technical Stack

- **Python** – pandas, NumPy, Plotly, Streamlit
- **Visualisation** – Interactive Plotly charts + Streamlit dashboard


---

## Project Structure

```
equity-trading-cost-analysis/
├── README.md
├── Notebooks/
│   ├── 01_market_data_pipeline.ipynb
│   ├── 02_trade_simulation.ipynb
│   └── 03_tca_analysis.ipynb
├── Dashboard/
│   ├── tca_trading_dashboard.py
│   └── requirements.txt
├── Data/
│   ├── market_data_processed.csv
│   ├── simulated_trades.csv
│   ├── simulated_trades_with_analysis.csv
│   └── tca_summary.xlsx
└── Images/
```

---
## Getting Started

```bash
git clone https://github.com/rosesparrow/equity-trading-cost-analysis.git
cd equity-trading-cost-analysis
pip install -r Dashboard/requirements.txt
streamlit run Dashboard/tca_trading_dashboard.py
```