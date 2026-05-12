import requests
import streamlit as st

from config import CHAINS, PROTOCOLS, SELECTED_ASSET
from components.style import apply_light_style
from components.charts import render_historical_apy_chart
from helpers.api import load_defillama_pools, load_lifi_tokens
from helpers.calculations import (
    build_arbitrage_table,
    filter_current_pools,
    prepare_pools_for_comparison,
)


st.set_page_config(
    page_title="USDC Cross-Chain Yield Opportunities",
    layout="wide",
)

apply_light_style()

try:
    with st.spinner("Loading DeFi data..."):
        df = load_defillama_pools()
        tokens = load_lifi_tokens()
except requests.RequestException as e:
    st.error(f"API request failed: {e}")
    st.stop()

required_cols = ["symbol", "project", "chain", "tvlUsd", "apy", "pool", "apyBase", "apyReward"]
missing_cols = [col for col in required_cols if col not in df.columns]

if missing_cols:
    st.error(f"DefiLlama response is missing expected columns: {missing_cols}")
    st.stop()

st.markdown("## USDC cross-chain yield opportunities")
st.caption("Historical APY and break-even calculator for USDC lending routes.")

# Defaults used before the user changes the widgets.
position_size = 10_000
min_tvl = 1_000_000
min_spread_bps = 20

filtered = filter_current_pools(
    df=df,
    selected_asset=SELECTED_ASSET,
    protocols=PROTOCOLS,
    chains=CHAINS,
    min_tvl=min_tvl,
)

if filtered.empty:
    st.warning("No USDC pools found for the selected filters.")
    st.stop()

render_historical_apy_chart(filtered)

st.markdown("### Parameters")

c1, c2, c3 = st.columns(3)

with c1:
    position_size = st.selectbox(
        "Position size",
        [1_000, 10_000, 50_000, 100_000, 1_000_000],
        index=1,
    )

with c2:
    min_tvl = st.selectbox(
        "Minimum TVL",
        [100_000, 1_000_000, 5_000_000, 10_000_000],
        index=1,
    )

with c3:
    min_spread_bps = st.slider(
        "Min spread, bps",
        min_value=0,
        max_value=500,
        value=20,
        step=10,
    )

compare_mode = st.radio(
    "Comparison mode",
    ["Best pool per chain", "All positive spreads"],
    index=1,
    horizontal=True,
)

filtered = filter_current_pools(
    df=df,
    selected_asset=SELECTED_ASSET,
    protocols=PROTOCOLS,
    chains=CHAINS,
    min_tvl=min_tvl,
)

if filtered.empty:
    st.warning("No USDC pools found for the selected filters.")
    st.stop()

st.markdown("### Arbitrage opportunities")

comparison_pools = prepare_pools_for_comparison(filtered, compare_mode)

with st.spinner("Calculating migration costs and break-even days..."):
    signals_df = build_arbitrage_table(
        pools_df=comparison_pools,
        selected_asset=SELECTED_ASSET,
        position_size=position_size,
        min_spread_bps=min_spread_bps,
        tokens=tokens,
    )

if signals_df.empty:
    st.warning("No positive opportunities found for the selected filters.")
else:
    signals_df = signals_df.sort_values(
        ["break_even_days", "spread_bps"],
        ascending=[True, False],
    )

    best = signals_df.iloc[0]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Best route", best["route"], best["protocol_route"])
    m2.metric("Spread", f"{int(best['spread_bps']):,} bps")
    m3.metric("Migration cost", f"${int(best['migration_cost_usd']):,}")
    m4.metric("Break-even", f"{int(best['break_even_days']):,} days")

    display_cols = [
        "route",
        "protocol_route",
        "source_apy_%",
        "dest_apy_%",
        "spread_bps",
        "migration_cost_usd",
        "break_even_days",
        "bridge_tool",
        "quote_source",
    ]

    st.dataframe(
    signals_df[display_cols],
    use_container_width=True,
    hide_index=True
    )

    st.download_button(
        label="Download CSV",
        data=signals_df.to_csv(index=False),
        file_name="usdc_cross_chain_arbitrage_signals.csv",
        mime="text/csv",
    )
