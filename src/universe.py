"""Initial ticker universe and Taiwan basket definitions.

The Phase 1 universe is intentionally narrow: semiconductor, AI hardware,
AI servers, Apple supply chain, and power / data-center infrastructure.
"""

US_TICKERS = [
    "NVDA",
    "AMD",
    "AVGO",
    "MU",
    "INTC",
    "ASML",
    "TSM",
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "QQQ",
    "SOXX",
    "SMH",
]

TAIWAN_TICKERS = [
    "2330.TW",
    "2454.TW",
    "2303.TW",
    "3711.TW",
    "2317.TW",
    "2382.TW",
    "6669.TW",
    "2408.TW",
    "2376.TW",
    "2357.TW",
    "2308.TW",
]

US_COMPANIES = {
    "NVDA": "NVIDIA",
    "AMD": "Advanced Micro Devices",
    "AVGO": "Broadcom",
    "MU": "Micron Technology",
    "INTC": "Intel",
    "ASML": "ASML Holding",
    "TSM": "Taiwan Semiconductor Manufacturing ADR",
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "QQQ": "Invesco QQQ Trust",
    "SOXX": "iShares Semiconductor ETF",
    "SMH": "VanEck Semiconductor ETF",
}

TAIWAN_COMPANIES = {
    "2330.TW": "TSMC",
    "2454.TW": "MediaTek",
    "2303.TW": "UMC",
    "3711.TW": "ASE Technology Holding",
    "2317.TW": "Hon Hai Precision Industry",
    "2382.TW": "Quanta Computer",
    "6669.TW": "Wiwynn",
    "2408.TW": "Nanya Technology",
    "2376.TW": "Gigabyte Technology",
    "2357.TW": "ASUS",
    "2308.TW": "Delta Electronics",
}

BASKETS = {
    "Taiwan Semiconductor Basket": [
        "2330.TW",
        "2454.TW",
        "2303.TW",
        "3711.TW",
        "2408.TW",
    ],
    "Taiwan AI Server Basket": [
        "2317.TW",
        "2382.TW",
        "6669.TW",
        "2376.TW",
        "2357.TW",
    ],
    "Taiwan Apple Supply Chain Basket": [
        "2317.TW",
        "2382.TW",
        "2357.TW",
    ],
    "Taiwan Power / Data Center Basket": [
        "2308.TW",
        "6669.TW",
        "2382.TW",
    ],
}
