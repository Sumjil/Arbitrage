import pandas as pd
import altair as alt
import streamlit as st

from helpers.api import load_historical_apy


def render_historical_apy_chart(filtered):
    st.markdown("### Historical APY")

    historical_candidates = filtered.sort_values("tvlUsd", ascending=False).head(8)
    historical_frames = []

    with st.spinner("Loading historical APY data..."):
        for _, row in historical_candidates.iterrows():
            hist = load_historical_apy(row["pool"])

            if hist.empty:
                continue

            hist = hist[["date", "apy"]].copy()
            hist["label"] = row["chain"] + " / " + row["project"]
            historical_frames.append(hist)

    if not historical_frames:
        st.warning("No historical APY data found.")
        return

    historical_df = pd.concat(historical_frames, ignore_index=True)
    historical_df = historical_df.dropna(subset=["date", "apy"])

    chart = (
        alt.Chart(historical_df)
        .mark_line()
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("apy:Q", title="APY, %"),
            color=alt.Color("label:N", title="Chain / Protocol"),
            tooltip=[
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("label:N", title="Pool"),
                alt.Tooltip("apy:Q", title="APY", format=".2f"),
            ],
        )
        .properties(height=430)
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)
