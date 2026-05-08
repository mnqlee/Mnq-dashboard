import yfinance as yf
from config import MAG7_WEIGHTS, ENGINE_WEIGHTS


def get_mag7_snapshot() -> dict:
    tickers = list(MAG7_WEIGHTS.keys())
    data = {}
    for t in tickers:
        try:
            hist = yf.Ticker(t).history(period="2d", interval="5m")
            if hist.empty:
                data[t] = {"pct": 0.0, "status": "unknown", "weighted_points": 0.0}
                continue

            last = float(hist["Close"].iloc[-1])
            open_today = float(hist["Open"].iloc[0])
            pct = ((last - open_today) / open_today) * 100 if open_today else 0.0
            bullish_fraction = max(0, min(1, (pct + 1.5) / 3.0))  # -1.5% -> 0, +1.5% -> 1
            weighted_points = bullish_fraction * MAG7_WEIGHTS[t]
            data[t] = {"pct": pct, "status": "green" if pct >= 0 else "red", "weighted_points": weighted_points}
        except Exception:
            data[t] = {"pct": 0.0, "status": "unknown", "weighted_points": 0.0}

    total_possible = sum(MAG7_WEIGHTS.values())
    raw = sum(x["weighted_points"] for x in data.values())
    points = (raw / total_possible) * ENGINE_WEIGHTS["mag7_breadth"]
    return {"points": round(points, 1), "raw": data}


def social_sentiment_placeholder() -> dict:
    """
    Placeholder until you connect X/Reddit/StockTwits APIs.
    Keep neutral by default so social media does not pollute the model.
    """
    return {
        "points": 5,
        "notes": ["Social sentiment is neutral until X/Reddit/StockTwits API is connected."]
    }


def volatility_risk_score(market_structure_notes: list[str]) -> dict:
    """
    Simple starter risk score out of 10.
    Later: use VIX, ATR expansion, calendar events, spread, volume shock.
    """
    score = 6
    notes = ["Starter volatility score is moderate. Add VIX/economic calendar next."]
    if any("choppy" in n.lower() for n in market_structure_notes):
        score -= 2
        notes.append("Choppy structure reduced risk-condition score.")
    return {"points": max(0, min(10, score)), "notes": notes}


def final_engine_score(structure, mag7, news, social, risk) -> dict:
    bullish = (
        structure["points"] +
        mag7["points"] +
        news["points"] +
        social["points"] +
        risk["points"]
    )
    bullish = round(max(0, min(100, bullish)), 1)
    bearish = round(100 - bullish, 1)

    if bullish >= 75:
        mode = "Strong Bullish Bias â Longs preferred, avoid chasing."
    elif bullish >= 60:
        mode = "Bullish Bias â Longs preferred only at quality pullbacks."
    elif bullish >= 45:
        mode = "Neutral / Chop â No trade or reduced size."
    elif bullish >= 25:
        mode = "Bearish Bias â Shorts preferred only at quality rallies."
    else:
        mode = "Strong Bearish Bias â Shorts preferred, avoid chasing."

    trade_permission = "TRADE ALLOWED WITH CONFIRMATION"
    if 45 <= bullish <= 55:
        trade_permission = "NO TRADE â mixed signal zone"
    if risk["points"] <= 3:
        trade_permission = "NO TRADE â risk conditions poor"

    return {
        "bullish": bullish,
        "bearish": bearish,
        "mode": mode,
        "trade_permission": trade_permission,
    }
