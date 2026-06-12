"""Transparent rule tables for Phase 3 headline classification."""

CLASSIFICATION_METHOD = "rule_based_v1"

TICKER_KEYWORDS = {
    "NVDA": ["nvidia", "gpu", "blackwell", "cuda"],
    "AMD": ["amd", "instinct", "mi300", "mi350"],
    "AVGO": ["broadcom", "asic", "custom silicon"],
    "MU": ["micron", "dram", "nand", "memory", "sram", "hbm", "high bandwidth memory"],
    "INTC": ["intel", "foundry", "cpu"],
    "ASML": ["asml", "euv", "lithography"],
    "TSM": ["tsmc", "taiwan semiconductor", "tsm"],
    "AAPL": ["apple", "iphone", "mac", "ipad"],
    "MSFT": ["microsoft", "azure", "microsoft cloud", "microsoft data center", "microsoft datacenter"],
    "AMZN": ["amazon", "aws", "amazon cloud", "amazon data center", "amazon datacenter"],
    "GOOGL": [
        "googl",
        "alphabet",
        "google cloud",
        "google data center",
        "google datacenter",
        "google ai",
        "gemini",
        "tpu",
        "google parent",
        "google shares",
        "google stock",
    ],
}

SECTOR_KEYWORDS = {
    "Semiconductor": [
        "semiconductor",
        "semiconductor stocks",
        "chip",
        "chips",
        "chip sector",
        "chip stocks",
        "gpu",
        "asic",
        "foundry",
        "euv",
        "lithography",
        "tsmc",
        "nvidia",
        "amd",
        "broadcom",
        "intel",
        "asml",
    ],
    "AI Infrastructure": [
        "ai infrastructure",
        "ai server",
        "ai server demand",
        "accelerator",
        "blackwell",
        "cuda",
        "gpu",
        "hyperscaler",
        "server rack",
        "rack-scale",
    ],
    "Memory": [
        "micron",
        "dram",
        "nand",
        "memory",
        "memory chip",
        "memory chips",
        "sram",
        "hbm",
        "high bandwidth memory",
        "inventory correction",
    ],
    "Apple Supply Chain": ["apple", "iphone", "mac", "ipad"],
    "Cloud / Data Center": [
        "data center",
        "datacenter",
        "cloud capex",
        "cloud infrastructure",
        "hyperscaler",
        "azure",
        "aws",
        "google cloud",
        "ai infrastructure",
        "server rack",
        "rack-scale",
        "cloud provider",
        "tpu",
        "gemini infrastructure",
    ],
    "Macro": ["fed", "federal reserve", "interest rate", "rates", "inflation", "treasury yields"],
    "Energy": ["oil", "crude", "energy", "shipping risks"],
}

THEME_KEYWORDS = {
    "AI chip demand": [
        "ai chip",
        "ai chips",
        "edge ai chip",
        "ai server",
        "gpu",
        "accelerator",
        "blackwell",
        "cuda",
        "strong demand",
    ],
    "data center capex": [
        "data center",
        "datacenter",
        "cloud capex",
        "capex increase",
        "cloud infrastructure",
        "hyperscaler",
        "aws",
        "azure",
        "google cloud",
        "tpu",
    ],
    "semiconductor equipment": ["asml", "euv", "lithography", "semiconductor equipment"],
    "memory cycle": [
        "micron",
        "dram",
        "nand",
        "memory",
        "memory chip",
        "memory chips",
        "sram",
        "hbm",
        "high bandwidth memory",
        "inventory correction",
    ],
    "foundry demand": ["foundry", "tsmc", "taiwan semiconductor"],
    "Apple hardware demand": ["apple", "iphone", "mac", "ipad"],
    "interest rates / Fed": ["fed", "federal reserve", "interest rate", "rates", "inflation", "treasury yields"],
    "oil / energy": ["oil", "crude", "energy"],
}

POSITIVE_KEYWORDS = [
    "rises",
    "gains",
    "beats",
    "strong demand",
    "raises guidance",
    "upgraded",
    "record revenue",
    "expansion",
    "capex increase",
    "orders surge",
]

NEGATIVE_KEYWORDS = [
    "falls",
    "drops",
    "misses",
    "weak demand",
    "cuts guidance",
    "downgraded",
    "investigation",
    "export restrictions",
    "supply disruption",
    "capex cut",
    "inventory correction",
]

NEUTRAL_KEYWORDS = ["announces", "says", "launches", "reports", "plans"]

SECTOR_PRIORITY = [
    "Energy",
    "Macro",
    "Memory",
    "Apple Supply Chain",
    "Semiconductor",
    "AI Infrastructure",
    "Cloud / Data Center",
]

THEME_PRIORITY = [
    "oil / energy",
    "interest rates / Fed",
    "memory cycle",
    "Apple hardware demand",
    "AI chip demand",
    "data center capex",
    "semiconductor equipment",
    "foundry demand",
]

VALID_SENTIMENT_LABELS = {"positive", "negative", "neutral", "mixed", "irrelevant"}
VALID_RELEVANCE_LABELS = {"high", "medium", "low", "irrelevant"}

LOW_QUALITY_TITLE_KEYWORDS = [
    "official homepage",
    "sponsored",
    "advertisement",
    "subscribe now",
    "newsletter signup",
    "login",
    "press release homepage",
    "unrelated sports schedule",
]
