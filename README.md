# MNQ Weighted Sentiment Dashboard

This is a starter Streamlit dashboard for MNQ/NQ decision support.

## What it includes

- MNQ/NQ proxy chart using Yahoo Finance futures ticker `NQ=F`
- MAG 7 live breadth panel
- Weighted confluence engine:
  - Market structure: 40%
  - MAG 7 breadth: 20%
  - News sentiment: 20%
  - Social sentiment placeholder: 10%
  - Volatility/risk conditions: 10%
- Basic detection for:
  - VWAP
  - Fair value gaps
  - Liquidity sweeps
  - Pivot-based supply/demand zones
- News sentiment from:
  - BBC Business RSS
  - Yahoo Finance RSS
  - Optional Financial Modeling Prep API

## Important

This dashboard is a decision-support/risk-filter tool. It does not guarantee trade outcomes and should not be used as the only reason to enter or exit a trade.

## Install

```bash
cd mnq_dashboard
python -m venv .venv
source .venv/bin/activate   # Mac/Linux
# .venv\Scripts\activate  # Windows

pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## Recommended next upgrades

1. Replace `NQ=F` starter data with your actual broker/TradingView/NinjaTrader MNQ feed.
2. Add TradingView webhook alerts for your custom FVG / supply-demand / liquidity sweep indicators.
3. Add a paid real-time squawk feed such as Benzinga/Newsquawk if speed matters.
4. Backtest the weighted score before trusting live signals.
