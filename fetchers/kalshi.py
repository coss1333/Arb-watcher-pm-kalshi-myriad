import os, requests
from typing import List
from ..matcher import NormalizedMarket, clean_title

API = "https://trades-api.kalshi.com/v2"

def _session():
    email = os.getenv("KALSHI_EMAIL")
    password = os.getenv("KALSHI_PASSWORD")
    s = requests.Session()
    if not email or not password:
        return None
    r = s.post(f"{API}/log_in", json={"email": email, "password": password}, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"Kalshi login failed: {r.text}")
    return s

def fetch_markets(min_liquidity_usd: float = 0) -> List[NormalizedMarket]:
    s = _session()
    if s is None:
        return []
    r = s.get(f"{API}/markets", timeout=30)
    r.raise_for_status()
    data = r.json().get("markets", [])
    out = []
    for m in data:
        if m.get("type") != "binary":
            continue
        title = m.get("title") or m.get("event_ticker") or ""
        yes = m.get("yes_bid") or m.get("last_trade_price")
        no = m.get("no_bid")
        if yes is not None:
            yes = float(yes)
        if no is not None:
            no = float(no)
        liq = m.get("volume") or 0
        if liq < min_liquidity_usd:
            continue
        url = f"https://kalshi.com/markets/{m.get('ticker','')}"
        out.append(NormalizedMarket(
            platform="kalshi",
            event_id=m.get("id") or m.get("ticker") or "",
            title=clean_title(title),
            yes_price=yes,
            no_price=no if no is not None else (1.0 - yes if yes is not None else None),
            liquidity_usd=float(liq) if liq is not None else None,
            url=url
        ))
    return out
