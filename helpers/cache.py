import json
import hashlib


def load_json_cache(path):
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_json_cache(path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def make_quote_cache_key(from_chain, to_chain, asset, amount, from_token, to_token):
    raw_key = {
        "from_chain": from_chain,
        "to_chain": to_chain,
        "asset": asset.upper(),
        "amount": float(amount),
        "from_token": from_token.lower(),
        "to_token": to_token.lower(),
    }

    encoded = json.dumps(raw_key, sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
