import requests
import pandas as pd
import streamlit as st

from config import CHAIN_IDS, LIFI_QUOTE_CACHE_FILE
from helpers.cache import load_json_cache, save_json_cache, make_quote_cache_key


@st.cache_data(ttl=60 * 30)
def load_defillama_pools():
    url = "https://yields.llama.fi/pools"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return pd.DataFrame(response.json()["data"])


@st.cache_data(ttl=60 * 30)
def load_lifi_tokens():
    url = "https://li.quest/v1/tokens"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()["tokens"]


@st.cache_data(ttl=60 * 30)
def load_historical_apy(pool_id):
    url = f"https://yields.llama.fi/chart/{pool_id}"
    response = requests.get(url, timeout=30)

    if response.status_code != 200:
        return pd.DataFrame()

    data = response.json().get("data", [])
    if not data:
        return pd.DataFrame()

    df_hist = pd.DataFrame(data)

    if "timestamp" in df_hist.columns:
        df_hist["date"] = pd.to_datetime(df_hist["timestamp"], errors="coerce")
    elif "date" in df_hist.columns:
        df_hist["date"] = pd.to_datetime(df_hist["date"], errors="coerce")
    else:
        return pd.DataFrame()

    if "apy" not in df_hist.columns:
        return pd.DataFrame()

    return df_hist.dropna(subset=["date", "apy"])


def get_token_info(tokens, chain_id, symbol):
    chain_key = str(chain_id)

    if chain_key not in tokens:
        return None

    chain_tokens = pd.DataFrame(tokens[chain_key])

    if chain_tokens.empty or "symbol" not in chain_tokens.columns:
        return None

    matches = chain_tokens[
        chain_tokens["symbol"].astype(str).str.upper().eq(symbol.upper())
    ]

    if matches.empty:
        return None

    token = matches.iloc[0]

    return {
        "address": token["address"],
        "decimals": int(token["decimals"]),
    }


def get_lifi_migration_cost(from_chain, to_chain, asset, amount, from_token, to_token, decimals):
    cache_key = make_quote_cache_key(
        from_chain=from_chain,
        to_chain=to_chain,
        asset=asset,
        amount=amount,
        from_token=from_token,
        to_token=to_token,
    )

    quote_cache = load_json_cache(LIFI_QUOTE_CACHE_FILE)

    if cache_key in quote_cache:
        cached = quote_cache[cache_key]
        cached["quote_source"] = "cache"
        return cached

    params = {
        "fromChain": CHAIN_IDS[from_chain],
        "toChain": CHAIN_IDS[to_chain],
        "fromToken": from_token,
        "toToken": to_token,
        "fromAmount": str(int(amount * 10 ** decimals)),
        "fromAddress": "0x1111111111111111111111111111111111111111",
    }

    response = requests.get("https://li.quest/v1/quote", params=params, timeout=30)

    if response.status_code != 200:
        return None

    data = response.json()
    estimate = data["estimate"]

    gas_costs = estimate.get("gasCosts", [])
    fee_costs = estimate.get("feeCosts", [])

    total_gas_usd = sum(float(x.get("amountUSD", 0)) for x in gas_costs)
    total_fee_usd = sum(float(x.get("amountUSD", 0)) for x in fee_costs)
    total_migration_cost = total_gas_usd + total_fee_usd

    result = {
        "bridge_tool": data.get("tool"),
        "execution_duration_sec": estimate.get("executionDuration"),
        "gas_cost_usd": total_gas_usd,
        "fee_cost_usd": total_fee_usd,
        "total_migration_cost_usd": total_migration_cost,
        "from_amount_usd": float(estimate.get("fromAmountUSD", 0)),
        "to_amount_usd": float(estimate.get("toAmountUSD", 0)),
        "quote_source": "api",
    }

    quote_cache[cache_key] = result
    save_json_cache(LIFI_QUOTE_CACHE_FILE, quote_cache)

    return result
