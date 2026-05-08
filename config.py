MAG7_WEIGHTS = {
    "NVDA": 5,
    "MSFT": 4,
    "AAPL": 4,
    "AMZN": 2,
    "META": 2,
    "GOOGL": 2,
    "TSLA": 1,
}

ENGINE_WEIGHTS = {
    "market_structure": 40,
    "mag7_breadth": 20,
    "news_sentiment": 20,
    "social_sentiment": 10,
    "volatility_risk": 10,
}

NEWS_KEYWORDS_BULLISH = [
    "beat", "beats", "rally", "surge", "dovish", "cut", "cuts", "cooling inflation",
    "soft landing", "upgrade", "record high", "ai demand", "strong earnings"
]

NEWS_KEYWORDS_BEARISH = [
    "miss", "misses", "selloff", "slump", "hawkish", "higher rates", "hot inflation",
    "recession", "downgrade", "tariff", "war", "risk-off", "weak guidance", "probe"
]

MNQ_PROXY_TICKER = "NQ=F"
MAG7_TICKERS = list(MAG7_WEIGHTS.keys())
