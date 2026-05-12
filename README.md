# Cross-chain arbitrage dashboard — refactored version

Run from this folder:

```bash
streamlit run app.py
```

## Structure

```text
app.py                         # main Streamlit page
config.py                      # chains, protocols, selected asset, cache path
helpers/cache.py               # JSON cache + hash key generation
helpers/api.py                 # DeFiLlama + LI.FI API calls
helpers/calculations.py        # filtering, spread, break-even, arbitrage table
components/style.py            # CSS styling
components/charts.py           # historical APY chart
```
