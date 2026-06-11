"""Transparent rule tables for Phase 3 headline classification."""

CLASSIFICATION_METHOD = "rule_based_v1"

TICKER_KEYWORDS = {
    "NVDA": ["nvidia", "gpu", "blackwell", "cuda"],
    "AMD": ["amd", "instinct", "mi300", "mi350"],
    "AVGO": ["broadcom", "asic", "custom silicon"],
    "MU": ["micron", "dram", "nand", "memory"],
    "INTC": ["intel", "foundry", "cpu"],
    "ASML": ["asml", "euv", "lithography"],
    "TSM": ["tsmc", "taiwan semiconductor", "tsm"],
    "AAPL": ["apple", "iphone", "mac", "ipad"],
    "MSFT": ["microsoft", "azure", "data center", "datacenter"],
    "AMZN": ["amazon", "aws", "data center", "datacenter"],
    "GOOGL": ["google", "alphabet", "cloud", "data center", "datacenter"],
}

SECTOR_KEYWORDS = {
    "Semiconductor": [
        "semiconductor",
        "chip",
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
        "ai server",
        "accelerator",
        "blackwell",
        "cuda",
        "gpu",
        "data center",
        "datacenter",
        "cloud capex",
    ],
    "Memory": ["micron", "dram", "nand", "memory", "inventory correction"],
    "Apple Supply Chain": ["apple", "iphone", "mac", "ipad"],
    "Cloud / Data Center": ["microsoft", "azure", "amazon", "aws", "google", "alphabet", "cloud", "data center", "datacenter"],
    "Macro": ["fed", "federal reserve", "interest rate", "rates", "inflation", "treasury yields"],
    "Energy": ["oil", "crude", "energy", "shipping risks"],
}

THEME_KEYWORDS = {
    "AI chip demand": ["ai chip", "ai server", "gpu", "accelerator", "blackwell", "cuda", "strong demand"],
    "data center capex": ["data center", "datacenter", "cloud capex", "capex increase", "aws", "azure"],
    "semiconductor equipment": ["asml", "euv", "lithography", "semiconductor equipment"],
    "memory cycle": ["micron", "dram", "nand", "memory", "inventory correction"],
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
    "Memory",
    "Apple Supply Chain",
    "AI Infrastructure",
    "Cloud / Data Center",
    "Semiconductor",
    "Macro",
    "Energy",
]

THEME_PRIORITY = [
    "memory cycle",
    "Apple hardware demand",
    "AI chip demand",
    "data center capex",
    "semiconductor equipment",
    "foundry demand",
    "interest rates / Fed",
    "oil / energy",
]

VALID_SENTIMENT_LABELS = {"positive", "negative", "neutral", "mixed", "irrelevant"}
VALID_RELEVANCE_LABELS = {"high", "medium", "low", "irrelevant"}
