import streamlit as st


def apply_light_style():
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        h1, h2, h3 {
            letter-spacing: -0.03em;
        }

        div[data-testid="stMetric"] {
            background: #ffffff;
            padding: 18px 20px;
            border-radius: 18px;
            border: 1px solid rgba(49, 51, 63, 0.12);
            box-shadow: 0 8px 28px rgba(15, 23, 42, 0.05);
        }

        div[data-testid="stDataFrame"] {
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(49, 51, 63, 0.12);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
