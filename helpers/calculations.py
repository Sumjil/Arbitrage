import time
import pandas as pd

from config import CHAIN_IDS
from helpers.api import get_token_info, get_lifi_migration_cost


def calculate_break_even_days(spread_percent, position_size_usd, migration_cost_usd):
    if spread_percent <= 0:
        return None

    annual_extra_yield = (spread_percent / 100) * position_size_usd

    if annual_extra_yield <= 0:
        return None

    return (migration_cost_usd / annual_extra_yield) * 365


def prepare_pools_for_comparison(filtered_df, mode):
    if mode == "Best pool per chain":
        return (
            filtered_df
            .sort_values("apy", ascending=False)
            .groupby("chain")
            .head(1)
            .reset_index(drop=True)
        )

    return filtered_df.reset_index(drop=True)


def filter_current_pools(df, selected_asset, protocols, chains, min_tvl):
    filtered = df[
        (df["symbol"].astype(str).str.upper().eq(selected_asset.upper()))
        & (df["project"].isin(protocols))
        & (df["chain"].isin(chains))
        & (df["tvlUsd"] > min_tvl)
    ].copy()

    columns = [
        "pool",
        "chain",
        "project",
        "symbol",
        "tvlUsd",
        "apy",
        "apyBase",
        "apyReward",
    ]

    return (
        filtered[columns]
        .dropna(subset=["apy"])
        .sort_values("apy", ascending=False)
    )


def build_arbitrage_table(pools_df, selected_asset, position_size, min_spread_bps, tokens):
    signals = []

    token_info_by_chain = {
        chain: get_token_info(tokens=tokens, chain_id=chain_id, symbol=selected_asset)
        for chain, chain_id in CHAIN_IDS.items()
    }

    for i, source in pools_df.iterrows():
        for j, dest in pools_df.iterrows():
            if i == j or source["chain"] == dest["chain"]:
                continue

            from_chain = source["chain"]
            to_chain = dest["chain"]

            source_apy = float(source["apy"])
            dest_apy = float(dest["apy"])

            spread_percent = dest_apy - source_apy
            spread_bps = spread_percent * 100

            if spread_bps <= min_spread_bps:
                continue

            from_token_info = token_info_by_chain.get(from_chain)
            to_token_info = token_info_by_chain.get(to_chain)

            if from_token_info is None or to_token_info is None:
                continue

            migration = get_lifi_migration_cost(
                from_chain=from_chain,
                to_chain=to_chain,
                asset=selected_asset,
                amount=position_size,
                from_token=from_token_info["address"],
                to_token=to_token_info["address"],
                decimals=from_token_info["decimals"],
            )

            if migration is None:
                continue

            migration_cost = migration["total_migration_cost_usd"]
            break_even_days = calculate_break_even_days(
                spread_percent=spread_percent,
                position_size_usd=position_size,
                migration_cost_usd=migration_cost,
            )

            signals.append({
                "asset": selected_asset,
                "route": f"{from_chain} → {to_chain}",
                "protocol_route": f"{source['project']} → {dest['project']}",
                "source_apy_%": round(source_apy, 2),
                "dest_apy_%": round(dest_apy, 2),
                "spread_bps": round(spread_bps),
                "migration_cost_usd": round(migration_cost),
                "break_even_days": round(break_even_days) if break_even_days is not None else None,
                "bridge_tool": migration["bridge_tool"],
                "quote_source": migration.get("quote_source", "unknown"),
            })

            time.sleep(0.1)

    return pd.DataFrame(signals)
