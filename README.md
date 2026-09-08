# onchain-notes

[![ci](https://github.com/alinaschanz/onchain-notes/actions/workflows/ci.yml/badge.svg)](https://github.com/alinaschanz/onchain-notes/actions/workflows/ci.yml)
![python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab)
![license mit](https://img.shields.io/badge/license-MIT-2b7a74)

small scripts i use to look at chains before i post anything. public data only,
no api keys, nothing but the python standard library.

i am alina, i live in berlin and i post the numbers on [x](https://x.com/alinaschanz)
and the longer notes on [alinaschanz.life](https://alinaschanz.life).

## what is here

| script | what it does |
| --- | --- |
| `daily_card.py` | prices (coingecko), ethereum base fee + blob fee (public rpc), base and arbitrum base fees, the solana priority fee, fear & greed (alternative.me), tvl by chain (defillama), btc dominance. one card, one screen. |
| `gas_now.py` | what a transfer / swap / mint costs on mainnet right now, in cents. base fee plus the median tip of the last 20 blocks. |

## run

```
python daily_card.py
python daily_card.py --json
python gas_now.py
```

python 3.10 or newer. no `pip install` needed. tests: `python -m pytest -q`.

## sample

```
$ python daily_card.py
-- 2026-09-07T22:17+00:00 --
btc       $79,139  -0.7% 24h
eth        $2,488  -0.4% 24h
sol          $104  -1.4% 24h
gas  base 0.0483 gwei  blob 0.00271 gwei  (block 25928407)
f&g  71 greed  (week ago 62)
dom  btc 59.1%
tvl  ethereum $49.6b / solana $5.9b / bsc $5.7b / base $5.6b / tron $5.5b
```

```
$ python gas_now.py
base fee 0.0483 gwei / median tip last 20 blocks 0.0222 gwei / eth $2,488
eth transfer     21,000 gas     0.37 cents
erc20 transfer   65,000 gas     1.14 cents
uniswap swap    150,000 gas     2.63 cents
nft mint        200,000 gas     3.51 cents
```

## sources

- prices, dominance, charts: [coingecko](https://www.coingecko.com/en/api) public api
- fees: any ethereum json-rpc, `eth_feeHistory` (defaults to publicnode, drpc, mevblocker)
- sentiment: [alternative.me fear & greed](https://alternative.me/crypto/fear-and-greed-index/)
- tvl: [defillama](https://defillama.com/docs/api)

## why

most of what i post is a screenshot of one of these plus a sentence. keeping the
scripts public means anyone can check the number instead of trusting the sentence.

not financial advice. numbers, not calls.

## see also

the same idea, grown into proper packages:

- [gasweek](https://github.com/alinaschanz/gasweek): base fee by hour of day over the last week, table and svg
- [bigmoves](https://github.com/alinaschanz/bigmoves): large stablecoin, weth and wbtc transfers, with exchange labels
- [stablepeg](https://github.com/alinaschanz/stablepeg): are the stablecoins still a dollar, read from uniswap and curve
- [ens-lookup](https://github.com/alinaschanz/ens-lookup): ens names to addresses and back, text records included

## license

[mit](LICENSE)
