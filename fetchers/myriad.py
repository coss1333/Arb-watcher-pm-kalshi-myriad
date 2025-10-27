# Placeholder Myriad fetcher: set MYRIAD_API_BASE to a valid endpoint if available.
import os, requests
from typing import List
from ..matcher import NormalizedMarket, clean_title

API = os.getenv("MYRIAD_API_BASE", "").rstrip("/")

def fetch_markets(min_liquidity_usd: float = 0) -> List[NormalizedMarket]:
    if not API:
        return []
    r = requests.get(f"{API}/markets", timeout=30)
    r.raise_for_status()
    data = r.json()
    out = []
    for m in data:
        if m.get("type") != "binary":
            continue
        title = m.get("title") or ""
        yes = m.get("yes_price")
        no = m.get("no_price") if m.get("no_price") is not None else (1.0 - yes if yes is not None else None)
        liq = m.get("liquidity_usd") or 0
        if liq < min_liquidity_usd:
            continue
        url = m.get("url")
        out.append(NormalizedMarket(
            platform="myriad",
            event_id=str(m.get("id")),
            title=clean_title(title),
            yes_price=float(yes) if yes is not None else None,
            no_price=float(no) if no is not None else None,
            liquidity_usd=float(liq) if liq is not None else None,
            url=url
        ))
    return out
