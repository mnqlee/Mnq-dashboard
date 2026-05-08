import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import plotly.graph_objects as go

from config import MNQ_PROXY_TICKER, MAG7_TICKERS
from data.market_data import (
    get_intraday,
    add_vwap,
    detect_fvgs,
    detect_liquidity_sweeps,
    pivot_supply_demand_zones,
    structure_score,
)
from data.news_feeds import collect_news, score_news_sentiment
from data.sentiment import (
    get_mag7_snapshot,
    social_sentiment_placeholder,
    volatility_risk_score,
    final_engine_score,
)


st.set_page_config(page_title="MNQ Weighted Sentiment Dashboard", layout="wide")

st.title("MNQ Weighted Sentiment Dashboard")
st.caption("Decision-support dashboard only. Not financial advice. Use this to filter risk, not blindly enter trades.")

with st.sidebar:
    st.header("Settings")
    ticker = st.text_input("MNQ/NQ data ticker", MNQ_PROXY_TICKER)
    period = st.selectbox("Chart period", ["1d", "5d"], index=0)
    interval = st.selectbox("Chart interval", ["1m", "2m", "5m", "15m"], index=0)
    refresh_seconds = st.slider("Auto-refresh seconds", 15, 300, 60, step=15)
    st.info("For true MNQ live execution-grade data, connect TradingView/NinjaTrader/Rithmic/Tradovate/CME feed later.")

st_autorefresh(interval=refresh_seconds * 1000, key="refresh")

# Data loading
df = get_intraday(ticker=ticker, period=period, interval=interval)
if not df.empty:
    df = add_vwap(df)

structure = structure_score(df)
mag7 = get_mag7_snapshot()
news_items = collect_news(MAG7_TICKERS)
news = score_news_sentiment(news_items)
social = social_sentiment_placeholder()
risk = volatility_risk_score(structure["notes"])
engine = final_engine_score(structure, mag7, news, social, risk)

# Top signal row
c1, c2, c3, c4 = st.columns(4)
c1.metric("Bullish Strength", f"{engine['bullish']} / 100")
c2.metric("Bearish Strength", f"{engine['bearish']} / 100")
c3.metric("Trade Permission", engine["trade_permission"])
c4.metric("Mode", engine["mode"])

st.progress(int(engine["bullish"]) / 100, text=f"Bullish Strength: {engine['bullish']}%")

# Main layout
left, right = st.columns([2.2, 1])

with left:
    st.subheader("MNQ / NQ Proxy Live Chart")
    if df.empty:
        st.error("No chart data loaded. Try a different interval/period or connect a live futures data feed.")
    else:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name=ticker,
        ))
        fig.add_trace(go.Scatter(x=df.index, y=df["VWAP"], name="VWAP", mode="lines"))

        # FVG overlays
        fvgs = detect_fvgs(df)
        for z in fvgs:
            fig.add_hrect(
                y0=z["low"], y1=z["high"],
                line_width=1,
                annotation_text=z["type"],
                annotation_position="top left",
                opacity=0.18,
            )

        # Supply / demand overlays
        zones = pivot_supply_demand_zones(df)
        for z in zones[-6:]:
            fig.add_hrect(
                y0=z["low"], y1=z["high"],
                line_width=1,
                annotation_text=z["type"],
                annotation_position="bottom right",
                opacity=0.12,
            )

        fig.update_layout(height=650, xaxis_rangeslider_visible=False, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)

        sweeps = detect_liquidity_sweeps(df)
        sweep_cols = st.columns(2)
        sweep_cols[0].metric("Sweep Low + Reclaim", "YES" if sweeps.get("sweep_low_reclaim") else "NO")
        sweep_cols[1].metric("Sweep High + Reject", "YES" if sweeps.get("sweep_high_reject") else "NO")

with right:
    st.subheader("Weighted Engine Breakdown")
    breakdown = pd.DataFrame([
        {"Module": "Market Structure", "Max": 40, "Bullish Points": structure["points"]},
        {"Module": "MAG 7 Breadth", "Max": 20, "Bullish Points": mag7["points"]},
        {"Module": "News Sentiment", "Max": 20, "Bullish Points": news["points"]},
        {"Module": "Social Sentiment", "Max": 10, "Bullish Points": social["points"]},
        {"Module": "Volatility / Risk", "Max": 10, "Bullish Points": risk["points"]},
    ])
    st.dataframe(breakdown, hide_index=True, use_container_width=True)

    st.subheader("Structure Notes")
    for n in structure["notes"]:
        st.write("•", n)

    st.subheader("Risk Notes")
    for n in risk["notes"]:
        st.write("•", n)

st.divider()

# MAG 7
st.subheader("MAG 7 Breadth")
mag_rows = []
for ticker_symbol, row in mag7["raw"].items():
    mag_rows.append({
        "Ticker": ticker_symbol,
        "Day %": round(row["pct"], 2),
        "Status": row["status"],
        "Weighted Points": round(row["weighted_points"], 2),
    })
st.dataframe(pd.DataFrame(mag_rows), hide_index=True, use_container_width=True)

# News
st.subheader("News Sentiment")
st.metric("News Sentiment Points", f"{news['points']} / 20", f"Avg compound {news['avg_compound']:.2f}")

news_table = []
for item in news["items"][:20]:
    news_table.append({
        "Compound": round(item.get("compound", 0), 2),
        "Source": item.get("source", ""),
        "Title": item.get("title", ""),
        "Link": item.get("link", ""),
    })
st.dataframe(pd.DataFrame(news_table), hide_index=True, use_container_width=True)

st.divider()
st.subheader("Next Tweaks")
st.write("""
1. Connect actual MNQ data from TradingView/NinjaTrader/Rithmic/Tradovate.
2. Add your exact Pine Script FVG / liquidity sweep / supply-demand rules.
3. Add economic-calendar blackout windows.
4. Add red-folder news hard stop.
5. Add a prop-firm risk module: daily drawdown, max trades/day, loss lockout.
""")
