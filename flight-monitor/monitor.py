#!/usr/bin/env python3
"""
Flight Monitor — orquestador principal.
Soporta rutas de destino fijo y alertas de precio abierto (región/país/continente).
"""

import json, os, datetime, sys
from pathlib import Path

from plugins.google_flights import search
from plugins.holidays_ar    import get_upcoming_holidays
from plugins.notifier       import send_telegram
from plugins.currency       import convert_to_usd, convert_from_usd, format_price

ROOT        = Path(__file__).parent
CONFIG_FILE = ROOT / "config.json"
PRICES_FILE = ROOT / "dashboard" / "prices.json"


def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)

def load_prices():
    if PRICES_FILE.exists():
        with open(PRICES_FILE) as f:
            return json.load(f)
    return {}

def save_prices(data):
    PRICES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PRICES_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run():
    config = load_config()
    prices = load_prices()
    now    = datetime.datetime.utcnow().isoformat()
    alerts = []

    plugins_cfg = config.get("plugins", {})
    notif_cfg   = config.get("notifications", {})
    tg_token    = os.environ.get("TELEGRAM_TOKEN", "")
    tg_chat_id  = notif_cfg.get("telegram", {}).get("chat_id", "")

    holidays = []
    if plugins_cfg.get("holidays_ar", {}).get("enabled"):
        holidays = get_upcoming_holidays(days_ahead=90)

    for route in config.get("routes", []):
        if not route.get("enabled"):
            continue

        route_id   = route["id"]
        label      = route["label"]
        origin     = route.get("origin", "EZE")
        currency   = route.get("currency", "USD").upper()
        max_amount = float(route.get("max_price", route.get("max_price_usd", 9999)))
        max_usd    = convert_to_usd(max_amount, currency)

        # Resolver label de destino para mostrar
        scope_type  = route.get("scope_type", "airport")
        scope_value = route.get("scope_value") or route.get("destination", "")
        dest_label  = scope_value if scope_type == "airport" else f"{scope_type.title()}: {scope_value}"

        print(f"\n🔍 {label}  ({origin} → {dest_label}, umbral {format_price(max_usd, currency)})")

        result = None
        if plugins_cfg.get("google_flights", {}).get("enabled", True):
            result = search(route)

        if result is None:
            print(f"  ⚠️  Sin resultados")
            continue

        price_usd  = result["price_usd"]
        best_date  = result["best_date"]
        best_dest  = result.get("best_dest", scope_value)
        airline    = result.get("airline", "Desconocida")

        # Guardar historial
        if route_id not in prices:
            prices[route_id] = {
                "label": label, "origin": origin,
                "scope_type": scope_type, "scope_value": scope_value,
                "currency": currency, "max_price": max_amount,
                "history": []
            }

        prices[route_id].update({
            "last_check":    now,
            "current_price_usd": price_usd,
            "current_price_display": format_price(price_usd, currency),
            "best_date":     best_date,
            "best_dest":     best_dest,
            "airline":       airline,
        })
        prices[route_id]["history"].append({
            "timestamp": now,
            "price_usd": price_usd,
            "best_date": best_date,
            "best_dest": best_dest,
            "airline":   airline,
        })
        prices[route_id]["history"] = prices[route_id]["history"][-90:]

        print(f"  💵 {format_price(price_usd, currency)} (USD {price_usd:.0f}) · {best_dest} · {airline}")

        # ── Lógica de alerta ──────────────────────────────────────────────────
        should_alert = False
        reasons      = []

        if price_usd <= max_usd:
            should_alert = True
            reasons.append(f"🟢 Bajo tu umbral de {format_price(max_usd, currency)}")

        hist = prices[route_id]["history"]
        if len(hist) >= 2:
            prev = hist[-2]["price_usd"]
            drop = prev - price_usd
            if drop >= 20:
                should_alert = True
                reasons.append(f"📉 Bajó {format_price(drop, currency)} desde el último check")

        if notif_cfg.get("notify_every_check"):
            should_alert = True

        if should_alert:
            hol_note = ""
            for h in holidays[:1]:
                hol_note = f"\n📅 Feriado próximo: {h['name']} ({h['date']})"

            # Armar precios en las tres monedas
            prices_line = (
                f"USD {price_usd:.0f}"
                f" · €{convert_from_usd(price_usd, 'EUR'):.0f}"
                f" · ARS ${convert_from_usd(price_usd, 'ARS'):,.0f}"
            )

            msg = (
                f"✈️ *{label}*\n"
                f"*{origin} → {best_dest}*\n"
                f"💵 {prices_line}\n"
                f"📆 Mejor fecha: {best_date}\n"
                f"🏷 {airline}\n"
                + "\n".join(reasons)
                + hol_note
                + f"\n\n🔗 [Ver vuelos](https://www.google.com/travel/flights/search?q={origin}+to+{best_dest})"
            )
            alerts.append(msg)
            print(f"  🔔 ALERTA generada")

    save_prices(prices)
    print(f"\n✅ {len(prices)} ruta(s) guardada(s)")

    if tg_token and tg_chat_id and alerts:
        for msg in alerts:
            send_telegram(tg_token, tg_chat_id, msg)
        print(f"📨 {len(alerts)} alerta(s) por Telegram")
    elif alerts and not tg_token:
        print("⚠️  Configurá TELEGRAM_TOKEN para recibir alertas")

    return len(alerts)


if __name__ == "__main__":
    sys.exit(0 if run() >= 0 else 1)
