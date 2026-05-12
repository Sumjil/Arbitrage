from pathlib import Path

CHAIN_IDS = {
    "Ethereum": 1,
    "Arbitrum": 42161,
    "Base": 8453,
    "Optimism": 10,
    "Polygon": 137,
}

CHAINS = list(CHAIN_IDS.keys())

PROTOCOLS = [
    "aave-v3",
    "compound-v3",
    "spark",
    "morpho-blue",
]

SELECTED_ASSET = "USDC"

CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

LIFI_QUOTE_CACHE_FILE = CACHE_DIR / "lifi_quote_cache.json"
