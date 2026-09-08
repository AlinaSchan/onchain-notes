#!/usr/bin/env python3
"""gas_now.py: what a transaction costs on ethereum mainnet right now, in cents.

    python gas_now.py
    python gas_now.py --eth 2500     # skip the price lookup

standard library only, public rpc, no keys.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request

RPCS = ("https://ethereum-rpc.publicnode.com", "https://cloudflare-eth.com", "https://eth.llamarpc.com")
UA = {"User-Agent": "onchain-notes/0.1 (+https://alinaschanz.life)", "Content-Type": "application/json"}
# rough gas used by the usual things people do
ACTIONS = (("eth transfer", 21_000), ("erc20 transfer", 65_000), ("uniswap swap", 150_000), ("nft mint", 200_000))


def rpc(url: str, method: str, params: list):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=payload, headers=UA)
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.loads(r.read())["result"]


def eth_price() -> float:
    req = urllib.request.Request(
        "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd",
        headers={"User-Agent": UA["User-Agent"]},
    )
    with urllib.request.urlopen(req, timeout=12) as r:
        return float(json.loads(r.read())["ethereum"]["usd"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eth", type=float, default=None, help="eth price in usd (default: coingecko)")
    ap.add_argument("--tip", type=float, default=0.01, help="priority fee in gwei to assume if the rpc gives none")
    args = ap.parse_args()
    hist = None
    last_err = None
    for url in RPCS:
        try:
            hist = rpc(url, "eth_feeHistory", ["0x14", "latest", [50]])  # 20 blocks, median tip
            break
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    if hist is None:
        print(f"no rpc answered: {last_err}", file=sys.stderr)
        return 1
    base = int(hist["baseFeePerGas"][-1], 16) / 1e9
    tips = [int(b[0], 16) / 1e9 for b in hist.get("reward") or [] if b]
    tip = sorted(tips)[len(tips) // 2] if tips else args.tip
    price = args.eth or eth_price()
    gwei = base + tip
    print(f"base fee {base:.3g} gwei / median tip last 20 blocks {tip:.3g} gwei / eth ${price:,.0f}")
    for name, gas in ACTIONS:
        cost = gas * gwei * 1e-9 * price
        print(f"{name:<15}{gas:>8,} gas  {cost * 100:>7.2f} cents")
    return 0


if __name__ == "__main__":
    sys.exit(main())
