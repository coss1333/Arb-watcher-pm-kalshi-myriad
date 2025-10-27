#!/usr/bin/env python3
import os, time, yaml
from dotenv import load_dotenv
from fetchers.polymarket import fetch_markets as fetch_pm
from fetchers.kalshi import fetch_markets as fetch_k
from fetchers.myriad import fetch_markets as fetch_my
from matcher import pairwise_match, find_arbs
from notifier import send_alert

def load_config():
    with open("config.yaml","r",encoding="utf-8") as f:
        return yaml.safe_load(f)

def gather_all(min_liquidity_usd: float):
    by_pf = {"polymarket": [], "kalshi": [], "myriad": []}
    try:
        by_pf["polymarket"] = fetch_pm(min_liquidity_usd=min_liquidity_usd)
    except Exception as e:
        print("Polymarket fetch error:", e)
    try:
        by_pf["kalshi"] = fetch_k(min_liquidity_usd=min_liquidity_usd)
    except Exception as e:
        print("Kalshi fetch error:", e)
    try:
        by_pf["myriad"] = fetch_my(min_liquidity_usd=min_liquidity_usd)
    except Exception as e:
        print("Myriad fetch error:", e)
    return by_pf

def format_msg(arb):
    title = arb["title"]
    yplat = arb["buy_yes_on"]
    nplat = arb["buy_no_on"]
    y = arb["yes_price"]; n = arb["no_price"]
    edge = arb["edge_percent"]
    urls = arb.get("urls", [])
    links = "\n".join(urls)
    return (
        f"⚖️ Арбитраж найден\n"
        f"Тема: {title}\n"
        f"Покупаем YES на: {yplat} @ {y:.3f}\n"
        f"Покупаем NO  на: {nplat} @ {n:.3f}\n"
        f"Ожидаемая доходность: {edge:.2f}% (после учёта указанных комиссий)\n"
        + (f"Ссылки:\n{links}" if links else "")
    )

def run_once(cfg):
    by_pf = gather_all(min_liquidity_usd=cfg.get("min_liquidity_usd", 0))
    excl = [e.lower() for e in cfg.get("exclude_keywords", [])]
    for pf, items in by_pf.items():
        by_pf[pf] = [m for m in items if not any(k in m.title for k in excl)]
    groups = pairwise_match(by_pf, sim_threshold=int(cfg.get("title_similarity_threshold", 88)))
    arbs = find_arbs(groups, fees_percent=cfg.get("fees_percent", {}), min_edge_percent=float(cfg.get("min_edge_percent", 0.2)))
    for a in arbs:
        send_alert(format_msg(a))
    if not arbs:
        print("No arbs found on this run.")

def main():
    load_dotenv()
    cfg = load_config()
    once = os.getenv("RUN_ONCE", "1") == "1"
    if once:
        run_once(cfg)
        return
    poll = int(cfg.get("poll_seconds", 60))
    while True:
        try:
            run_once(cfg)
        except Exception as e:
            print("Run error:", e)
        time.sleep(poll)

if __name__ == "__main__":
    main()
