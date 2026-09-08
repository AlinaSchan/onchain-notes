"""pure-function tests: formatting and response parsing, no network."""
import daily_card as dc
import gas_now


def test_usd_formats_big_and_small():
    assert dc.usd(79172.0) == "$79,172"
    assert dc.usd(2488.46) == "$2,488"
    assert dc.usd(0.9931) == "$0.99"


def test_big_formats_billions_and_millions():
    assert dc.big(49_595_600_420) == "$49.6b"
    assert dc.big(842_000_000) == "$842m"


def test_pct_handles_none():
    assert dc.pct(None) == "n/a"
    assert dc.pct(-0.83) == "-0.8%"
    assert dc.pct(1.24) == "+1.2%"


def test_l2_fees_and_sol_tip_parse_and_skip_dead_chains(monkeypatch):
    answers = {"https://a": {"result": {"baseFeePerGas": ["0x1", "0x3b9aca00"]}},
               "https://s": {"result": [{"slot": 1, "prioritizationFee": 5000}, {"slot": 2, "prioritizationFee": 100}, {"slot": 3, "prioritizationFee": 900}]}}

    def fake_get(url, **kw):
        if url in answers:
            return answers[url]
        raise OSError("down")

    monkeypatch.setattr(dc, "get", fake_get)
    assert dc.l2_fees({"base": ("https://dead", "https://a"), "arbitrum": ("https://dead",)}) == {"base": 1.0}
    assert dc.sol_priority_fee(("https://dead", "https://s")) == 900.0
    assert dc.sol_priority_fee(("https://dead",)) is None


def test_tickers_cover_every_coin():
    assert set(dc.TICKER) == set(dc.COINS)


def test_fees_reads_next_block_base_fee_and_blob_fee(monkeypatch):
    fake = {"result": {"oldestBlock": "0x18b7c67", "baseFeePerGas": ["0x2faf080", "0x2e90edd"],
                       "baseFeePerBlobGas": ["0x1", "0x2"]}}
    monkeypatch.setattr(dc, "get", lambda url, **kw: fake)
    out = dc.fees("https://rpc.example")
    assert out["block"] == 0x18B7C67
    assert abs(out["base_gwei"] - 0x2E90EDD / 1e9) < 1e-12  # last entry = next block
    assert out["blob_gwei"] == 2 / 1e9


def test_fees_without_blob_field_is_fine(monkeypatch):
    fake = {"result": {"oldestBlock": "0x10", "baseFeePerGas": ["0x3b9aca00", "0x3b9aca00"]}}
    monkeypatch.setattr(dc, "get", lambda url, **kw: fake)
    assert dc.fees("x")["blob_gwei"] is None
    assert dc.fees("x")["base_gwei"] == 1.0


def test_fear_greed_picks_today_and_a_week_ago(monkeypatch):
    rows = [{"value": str(70 + i), "value_classification": "Greed"} for i in range(8)]
    monkeypatch.setattr(dc, "get", lambda url, **kw: {"data": rows})
    fg = dc.fear_greed()
    assert fg == {"value": 70, "label": "greed", "week_ago": 77}


def test_safe_returns_error_text_instead_of_raising():
    def boom():
        raise ValueError("nope")

    val, err = dc.safe(boom)
    assert val is None and err.startswith("ValueError")


def test_gas_now_actions_are_sane():
    gas = dict(gas_now.ACTIONS)
    assert gas["eth transfer"] == 21_000
    assert gas["eth transfer"] < gas["erc20 transfer"] < gas["uniswap swap"] < gas["nft mint"]
