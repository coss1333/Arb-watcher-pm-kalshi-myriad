from dataclasses import dataclass
from typing import Optional, Dict, List
from rapidfuzz import fuzz

@dataclass
class NormalizedMarket:
    platform: str                # 'polymarket' | 'kalshi' | 'myriad'
    event_id: str
    title: str                   # canonical cleaned title
    yes_price: Optional[float]   # price in [0,1] for YES
    no_price: Optional[float]    # price in [0,1] for NO
    liquidity_usd: Optional[float]
    url: Optional[str]

def clean_title(t: str) -> str:
    t = t.strip().lower()
    repl = {
        "will ": "",
        "does ": "",
        "do ": "",
        "the ": "",
        "?": "",
        "%": " percent",
        "  ": " "
    }
    for k,v in repl.items():
        t = t.replace(k, v)
    return " ".join(t.split())

def pairwise_match(markets_by_platform: Dict[str, List[NormalizedMarket]], sim_threshold: int = 88):
    # Return groups of potentially same events across platforms by fuzzy title match.
    all_items = []
    for pf, items in markets_by_platform.items():
        for m in items:
            all_items.append(m)
    groups: List[List[NormalizedMarket]] = []
    used = set()
    for i, m in enumerate(all_items):
        if i in used:
            continue
        group = [m]
        used.add(i)
        for j, n in enumerate(all_items):
            if j <= i or j in used:
                continue
            if m.platform == n.platform:
                continue
            score = fuzz.token_set_ratio(m.title, n.title)
            if score >= sim_threshold:
                group.append(n)
                used.add(j)
        if len(group) >= 2:
            groups.append(group)
    return groups

def arbitrage_from_pair(yes_a: float, no_b: float, fee_a: float, fee_b: float):
    # yes_a, no_b in [0,1], fees fractional (0.01 = 1%).
    if not (0 < yes_a < 1 and 0 < no_b < 1):
        return None
    if fee_a >= 1 or fee_b >= 1:
        return None
    x = 1.0 / (1.0 - fee_a)
    y = 1.0 / (1.0 - fee_b)
    total_cost = x * yes_a + y * no_b
    edge = 1.0 - total_cost
    return edge

def find_arbs(groups, fees_percent: Dict[str, float], min_edge_percent: float):
    # Return a list of arbitrage opportunities across platforms with computed edge.
    arbs = []
    for group in groups:
        for i in range(len(group)):
            for j in range(len(group)):
                if i == j: 
                    continue
                a = group[i]; b = group[j]
                if a.yes_price is None or b.no_price is None:
                    continue
                fee_a = fees_percent.get(a.platform, 0.0) / 100.0
                fee_b = fees_percent.get(b.platform, 0.0) / 100.0
                edge = arbitrage_from_pair(a.yes_price, b.no_price, fee_a, fee_b)
                if edge is None: 
                    continue
                if edge*100.0 >= min_edge_percent:
                    arbs.append({
                        "title": a.title,
                        "buy_yes_on": a.platform,
                        "buy_no_on": b.platform,
                        "yes_price": a.yes_price,
                        "no_price": b.no_price,
                        "edge_percent": edge*100.0,
                        "urls": list({u for u in [a.url, b.url] if u})
                    })
    # de-duplicate
    seen = set()
    uniq = []
    for arb in arbs:
        key = (arb["title"], arb["buy_yes_on"], arb["buy_no_on"])
        if key in seen: 
            continue
        seen.add(key)
        uniq.append(arb)
    return sorted(uniq, key=lambda x: -x["edge_percent"])
