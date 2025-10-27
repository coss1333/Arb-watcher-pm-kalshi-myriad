import requests
from typing import List
from ..matcher import NormalizedMarket, clean_title

BASE = "https://clob.polymarket.com"

def fetch_markets(min_liquidity_usd: float = 0) -> List[NormalizedMarket]:
    url = f"{BASE}/markets?limit=1000&active=true"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json().get("data", [])
    out = []
    for m in data:
        q = m.get("question") or m.get("title") or ""
        yes = m.get("last_price")
        if yes is None:
            continue
        liq = m.get("liquidity", 0) or 0
        if liq < min_liquidity_usd:
            continue
        url_market = f"https://polymarket.com/event/{m.get('event_id','')}" if m.get("event_id") else "https://polymarket.com/"
        out.append(NormalizedMarket(
            platform="polymarket",
            event_id=str(m.get("id")),
            title=clean_title(q),
            yes_price=float(yes),
            no_price=1.0 - float(yes),
            liquidity_usd=float(liq),
            url=url_market
        ))
    return out
