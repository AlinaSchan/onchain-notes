#!/usr/bin/env python3
"""daily_card.py: the numbers i look at before i post anything.

prices (coingecko), ethereum base fee + blob base fee (any public rpc),
fear & greed (alternative.me), tvl by chain (defillama), btc dominance.
public endpoints only, no api keys, standard library only.

    python daily_card.py            # text card
    python daily_card.py --json     # same thing as json
    python daily_card.py --rpc https://cloudflare-eth.com
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "onchain-notes/0.1 (+https://alinaschanz.life)"}
RPCS = ("https://ethereum-rpc.publicnode.com", "https://eth.drpc.org", "https://rpc.mevblocker.io")
COINS = ("bitcoin", "ethereum", "solana")
TICKER = {"bitcoin": "btc", "ethereum": "eth", "solana": "sol"}


def get(url: str, *, data: dict | None = None, timeout: float = 12.0):
    body = json.dumps(data).encode() if data is not None else None
    headers = dict(UA)
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def prices() -> dict:
    ids = ",".join(COINS)
    d = get(f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true")
    return {c: {"usd": d[c]["usd"], "chg24h": d[c].get("usd_24h_change")} for c in COINS if c in d}


def dominance() -> float | None:
    d = get("https://api.coingecko.com/api/v3/global")
    return d.get("data", {}).get("market_cap_percentage", {}).get("btc")


def fear_greed() -> dict:
    d = get("https://api.alternative.me/fng/?limit=8")
    rows = d.get("data") or []
    now = rows[0] if rows else {}
    week = rows[7] if len(rows) > 7 else {}
    return {
        "value": int(now.get("value", 0)) or None,
        "label": (now.get("value_classification") or "").lower() or None,
        "week_ago": int(week.get("value", 0)) or None,
    }


L2_RPCS = {"base": ("https://mainnet.base.org", "https://base-rpc.publicnode.com"),
           "arbitrum": ("https://arb1.arbitrum.io/rpc", "https://arbitrum-one-rpc.publicnode.com")}
SOL_RPCS = ("https://api.mainnet-beta.solana.com", "https://solana-rpc.publicnode.com")


def l2_fees(rpcs: dict = L2_RPCS) -> dict:
    """next-block base fee on the l2s, in gwei; a chain that does not answer is simply absent."""
    out = {}
    for chain, urls in rpcs.items():
        for url in urls:
            try:
                d = get(url, data={"jsonrpc": "2.0", "id": 1, "method": "eth_feeHistory", "params": ["0x1", "latest", []]})
                out[chain] = int(d["result"]["baseFeePerGas"][-1], 16) / 1e9
                break
            except Exception:
                continue
    return out


def sol_priority_fee(rpcs: tuple = SOL_RPCS) -> float | None:
    """median of the recent prioritization fees, in micro-lamports per compute unit (what solana calls a tip)."""
    for url in rpcs:
        try:
            d = get(url, data={"jsonrpc": "2.0", "id": 1, "method": "getRecentPrioritizationFees", "params": [[]]})
            fees_ = sorted(int(x["prioritizationFee"]) for x in d["result"])
            return float(fees_[len(fees_) // 2]) if fees_ else None
        except Exception:
            continue
    return None


def fees(rpc: str) -> dict:
    """base fee of the next block + blob base fee, in gwei. eth_feeHistory needs no key."""
    d = get(rpc, data={"jsonrpc": "2.0", "id": 1, "method": "eth_feeHistory", "params": ["0x1", "latest", []]})
    r = d["result"]
    base = int(r["baseFeePerGas"][-1], 16) / 1e9  # last entry = next block
    blob = None
    if r.get("baseFeePerBlobGas"):
        blob = int(r["baseFeePerBlobGas"][-1], 16) / 1e9
    return {"base_gwei": base, "blob_gwei": blob, "block": int(r["oldestBlock"], 16)}


def tvl(top: int = 5) -> list[tuple[str, float]]:
    rows = get("https://api.llama.fi/v2/chains")
    rows = sorted((r for r in rows if r.get("tvl")), key=lambda r: -r["tvl"])
    return [(r["name"], float(r["tvl"])) for r in rows[:top]]


def safe(fn, *a):
    try:
        return fn(*a), None
    except (urllib.error.URLError, KeyError, ValueError, TimeoutError, OSError) as exc:
        return None, f"{type(exc).__name__}: {exc}"[:120]


def usd(x: float) -> str:
    return f"${x:,.0f}" if x >= 100 else f"${x:,.2f}"


def big(x: float) -> str:
    return f"${x / 1e9:.1f}b" if x >= 1e9 else f"${x / 1e6:.0f}m"


def pct(x) -> str:
    return "n/a" if x is None else f"{x:+.1f}%"


def main() -> int:
    ap = argparse.ArgumentParser(description="the numbers i look at before i post anything")
    ap.add_argument("--json", action="store_true", help="print json instead of the text card")
    ap.add_argument("--rpc", default=None, help="ethereum json-rpc url (default: try a few public ones)")
    args = ap.parse_args()

    out: dict = {"at": datetime.now(timezone.utc).isoformat(timespec="minutes"), "errors": {}}
    p, err = safe(prices)
    out["prices"], out["errors"]["prices"] = p or {}, err
    dom, err = safe(dominance)
    out["btc_dominance"], out["errors"]["dominance"] = dom, err
    fg, err = safe(fear_greed)
    out["fear_greed"], out["errors"]["fear_greed"] = fg or {}, err
    fee = None
    for rpc in ([args.rpc] if args.rpc else RPCS):
        fee, err = safe(fees, rpc)
        if fee:
            fee["rpc"] = rpc
            break
    out["fees"], out["errors"]["fees"] = fee or {}, err
    t, err = safe(tvl)
    out["tvl"], out["errors"]["tvl"] = t or [], err
    out["errors"] = {k: v for k, v in out["errors"].items() if v}

    if args.json:
        print(json.dumps(out, indent=1))
        return 0

    print(f"-- {out['at']} --")
    for c in COINS:
        if c in out["prices"]:
            row = out["prices"][c]
            print(f"{TICKER.get(c, c[:3]):<5}{usd(row['usd']):>12}  {pct(row['chg24h'])} 24h")
    if fee:
        blob = f"  blob {fee['blob_gwei']:.3g} gwei" if fee.get("blob_gwei") is not None else ""
        print(f"gas  base {fee['base_gwei']:.3g} gwei{blob}  (block {fee['block']})")
    if out["fear_greed"].get("value"):
        fgv = out["fear_greed"]
    l2 = l2_fees()
    sol = sol_priority_fee()
    if l2 or sol is not None:
        parts = [f"{k} {v:.4g} gwei" for k, v in l2.items()]
        if sol is not None:
            parts.append(f"sol tip {sol:,.0f} ulamports/cu")
        print("l2   " + " / ".join(parts))
        print(f"f&g  {fgv['value']} {fgv['label']}  (week ago {fgv['week_ago']})")
    if dom:
        print(f"dom  btc {dom:.1f}%")
    if out["tvl"]:
        print("tvl  " + " / ".join(f"{n.lower()} {big(v)}" for n, v in out["tvl"]))
    for k, v in out["errors"].items():
        print(f"!    {k}: {v}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
