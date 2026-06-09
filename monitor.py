#!/usr/bin/env python3
"""
Flight Monitor - Los Angelitos Travel Tracker
Corre via GitHub Actions. Busca precios, guarda historial, manda alertas.
"""

import json
import os
import datetime
import sys
from pathlib import Path

# ── Importar plugins habilitados ──────────────────────────────────────────────
from plugins.google_flights import search_google_flights
from plugins.holidays_ar import get_upcoming_holidays
from plugins.notifier import send_telegram

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent
CONFIG_FILE = ROOT / "config.json"
PRICES_FILE = ROOT / "dashboard" / "prices.json"

# ── Cargar configuración ──────────────────────────────────────────────────────
def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)

# ── Cargar / inicializar historial ────────────────────────────────────────────
def load_prices():
    if PRICES_FILE.exists():
        with open(PRICES_FILE) as f:
            return json.load(f)
    return {}

def save_prices(data):
    PRICES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PRICES_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ── Lógica principal ──────────────────────────────────────────────────────────
def run():
    config = load_config()
    prices = load_prices()
    now    = datetime.datetime.utcnow().isoformat()
    alerts = []

    plugins_cfg = config.get("plugins", {})
    notif_cfg   = config.get("notifications", {})
    tg_cfg      = notif_cfg.get("telegram", {})

    # Leer token de Telegram desde variable de entorno (secreto en GitHub)
    tg_token   = os.environ.get("TELEGRAM_TOKEN", "")
    tg_chat_id = tg_cfg.get("chat_id", "")

    # Feriados AR (informativo en alertas)
    holidays = []
    if plugins_cfg.get("holidays_ar", {}).get("enabled"):
        holidays = get_upcoming_holidays(days_ahead=90)

    for route in config.get("routes", []):
        if not route.get("enabled"):
            continue

        route_id  = route["id"]
        label     = route["label"]
        origin    = route["origin"]
        dest      = route["destination"]
        max_price = route["max_price_usd"]
        date_from = route["date_from"]
        date_to   = route["date_to"]
        pax       = route.get("passengers", 1)

        print(f"\n🔍 Buscando: {label} ({date_from} → {date_to})")

        # Buscar precio actual
        result = None
        if plugins_cfg.get("google_flights", {}).get("enabled"):
            result = search_google_flights(origin, dest, date_from, date_to, pax)

        if result is None:
            print(f"  ⚠️  No se pudo obtener precio para {route_id}")
            continue

        current_price = result["price_usd"]
        best_date     = result["best_date"]
        airline       = result.get("airline", "Aerolínea desconocida")

        print(f"  💵 Precio actual: USD {current_price} | Mejor fecha: {best_date}")

        # Guardar en historial
        if route_id not in prices:
            prices[route_id] = {
                "label": label,
                "origin": origin,
                "destination": dest,
                "max_price_usd": max_price,
                "history": []
            }

        prices[route_id]["last_check"] = now
        prices[route_id]["current_price"] = current_price
        prices[route_id]["best_date"] = best_date
        prices[route_id]["airline"] = airline
        prices[route_id]["history"].append({
            "timestamp": now,
            "price_usd": current_price,
            "best_date": best_date,
            "airline": airline
        })

        # Mantener historial de los últimos 90 puntos
        prices[route_id]["history"] = prices[route_id]["history"][-90:]

        # ¿Disparar alerta?
        should_alert = False
        reason = ""

        if current_price <= max_price:
            should_alert = True
            reason = f"🟢 Precio por debajo de tu umbral (USD {max_price})"
        elif notif_cfg.get("notify_every_check"):
            should_alert = True
            reason = f"ℹ️ Actualización periódica (USD {max_price} es tu umbral)"

        # Detectar baja respecto al check anterior
        hist = prices[route_id]["history"]
        if len(hist) >= 2:
            prev_price = hist[-2]["price_usd"]
            drop = prev_price - current_price
            if drop > 0 and drop >= 20:
                should_alert = True
                reason = f"📉 Bajó USD {drop:.0f} desde el último check (antes: USD {prev_price:.0f})"

        if should_alert:
            # Armar mensaje
            holiday_note = ""
            for h in holidays:
                holiday_note = f"\n📅 Feriado cercano: {h['name']} el {h['date']}"
                break

            msg = (
                f"✈️ *Alerta de vuelo*\n"
                f"*{label}*\n"
                f"💵 USD {current_price:.0f} · {airline}\n"
                f"📆 Mejor fecha: {best_date}\n"
                f"{reason}"
                f"{holiday_note}\n"
                f"🔗 [Ver en Google Flights](https://www.google.com/travel/flights/search?q={origin}+to+{dest})"
            )
            alerts.append(msg)
            print(f"  🔔 ALERTA: {reason}")

    # Guardar historial actualizado
    save_prices(prices)
    print(f"\n✅ Historial guardado: {len(prices)} ruta(s)")

    # Mandar alertas por Telegram
    if tg_token and tg_chat_id and alerts:
        for msg in alerts:
            send_telegram(tg_token, tg_chat_id, msg)
        print(f"📨 {len(alerts)} alerta(s) enviada(s) por Telegram")
    elif alerts:
        print("⚠️  Hay alertas pero TELEGRAM_TOKEN o chat_id no configurado")
        for a in alerts:
            print(a)

    return len(alerts)

if __name__ == "__main__":
    count = run()
    sys.exit(0)
