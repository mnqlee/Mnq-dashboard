import pandas as pd
import numpy as np
import yfinance as yf


def get_intraday(ticker: str = "NQ=F", period: str = "1d", interval: str = "1m") -> pd.DataFrame:
    """Fetch starter intraday data. For production, replace with broker/CME/TradingView data."""
    df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=False)
    if df.empty:
        return pd.DataFrame()

    # Flatten multi-index columns when yfinance returns them
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]

    df = df.rename(columns=str.title)
    required = ["Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in df.columns:
            df[col] = np.nan

    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    return df


def add_vwap(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    typical_price = (out["High"] + out["Low"] + out["Close"]) / 3
    volume = out["Volume"].replace(0, np.nan).fillna(1)
    out["VWAP"] = (typical_price * volume).cumsum() / volume.cumsum()
    return out


def detect_fvgs(df: pd.DataFrame, lookback: int = 80) -> list[dict]:
    """
    Basic 3-candle fair value gap detection.
    Bullish FVG: current low > high two candles back.
    Bearish FVG: current high < low two candles back.
    """
    zones = []
    if len(df) < 3:
        return zones

    d = df.tail(lookback)
    for i in range(2, len(d)):
        c0 = d.iloc[i - 2]
        c2 = d.iloc[i]
        ts = d.index[i]

        if c2["Low"] > c0["High"]:
            zones.append({
                "type": "Bullish FVG",
                "start": ts,
                "low": float(c0["High"]),
                "high": float(c2["Low"]),
            })

        if c2["High"] < c0["Low"]:
            zones.append({
                "type": "Bearish FVG",
                "start": ts,
                "low": float(c2["High"]),
                "high": float(c0["Low"]),
            })

    return zones[-10:]


def detect_liquidity_sweeps(df: pd.DataFrame, window: int = 20) -> dict:
    """
    Simple liquidity sweep detector:
    - Sweep low: latest candle takes prior window low then closes back above it.
    - Sweep high: latest candle takes prior window high then closes back below it.
    """
    if len(df) < window + 2:
        return {"sweep_low_reclaim": False, "sweep_high_reject": False}

    prior = df.iloc[-window-1:-1]
    last = df.iloc[-1]

    prior_low = prior["Low"].min()
    prior_high = prior["High"].max()

    return {
        "sweep_low_reclaim": bool(last["Low"] < prior_low and last["Close"] > prior_low),
        "sweep_high_reject": bool(last["High"] > prior_high and last["Close"] < prior_high),
        "prior_low": float(prior_low),
        "prior_high": float(prior_high),
    }


def pivot_supply_demand_zones(df: pd.DataFrame, left_right: int = 3, lookback: int = 120) -> list[dict]:
    """
    Lightweight pivot-based zones.
    - Pivot lows become demand zones.
    - Pivot highs become supply zones.
    This is intentionally simple and should be replaced with your exact TradingView logic later.
    """
    zones = []
    if len(df) < left_right * 2 + 1:
        return zones

    d = df.tail(lookback)
    for i in range(left_right, len(d) - left_right):
        row = d.iloc[i]
        left = d.iloc[i-left_right:i]
        right = d.iloc[i+1:i+1+left_right]
        ts = d.index[i]

        if row["Low"] <= left["Low"].min() and row["Low"] <= right["Low"].min():
            zones.append({
                "type": "Demand",
                "start": ts,
                "low": float(row["Low"]),
                "high": float((row["Low"] + row["Close"]) / 2),
            })

        if row["High"] >= left["High"].max() and row["High"] >= right["High"].max():
            zones.append({
                "type": "Supply",
                "start": ts,
                "low": float((row["High"] + row["Close"]) / 2),
                "high": float(row["High"]),
            })

    return zones[-12:]


def structure_score(df: pd.DataFrame) -> dict:
    """Return bullish points out of 40 and explanatory notes."""
    if df.empty or len(df) < 30:
        return {"points": 20, "notes": ["Insufficient chart data; neutral structure score."]}

    df = add_vwap(df)
    last = df.iloc[-1]
    recent = df.tail(20)
    prev = df.tail(40).head(20)

    points = 0
    notes = []

    if last["Close"] > last["VWAP"]:
        points += 8
        notes.append("MNQ/NQ proxy is above VWAP.")
    else:
        notes.append("MNQ/NQ proxy is below VWAP.")

    recent_high = recent["High"].max()
    recent_low = recent["Low"].min()
    prev_high = prev["High"].max()
    prev_low = prev["Low"].min()

    if recent_high > prev_high and recent_low > prev_low:
        points += 12
        notes.append("Recent structure shows higher high / higher low pressure.")
    elif recent_high < prev_high and recent_low < prev_low:
        notes.append("Recent structure shows lower high / lower low pressure.")
    else:
        points += 6
        notes.append("Recent structure is mixed/choppy.")

    sweeps = detect_liquidity_sweeps(df)
    if sweeps.get("sweep_low_reclaim"):
        points += 8
        notes.append("Liquidity sweep low + reclaim detected.")
    if sweeps.get("sweep_high_reject"):
        notes.append("Liquidity sweep high + rejection detected.")

    fvgs = detect_fvgs(df)
    if fvgs:
        last_fvg = fvgs[-1]
        if last_fvg["type"] == "Bullish FVG":
            points += 6
            notes.append("Most recent FVG is bullish.")
        else:
            notes.append("Most recent FVG is bearish.")

    # Momentum slope
    if df["Close"].tail(10).iloc[-1] > df["Close"].tail(10).iloc[0]:
        points += 6
        notes.append("Short-term close momentum is positive.")
    else:
        notes.append("Short-term close momentum is negative.")

    return {"points": min(points, 40), "notes": notes}
