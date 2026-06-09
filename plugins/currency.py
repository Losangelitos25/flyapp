"""
currency.py — Conversión de moneda via exchangerate-api (open, sin key).
Fallback a valores hardcodeados si no hay internet.
"""

import urllib.request
import json
import datetime

_cache = {}
_cache_ts = {}
CACHE_MINUTES = 60


def get_rate_to_usd(currency: str) -> float:
    """
    Devuelve cuántos USD equivale 1 unidad de `currency`.
    Ej: get_rate_to_usd("EUR") → 1.08  (1 EUR = 1.08 USD)
         get_rate_to_usd("ARS") → 0.00095
         get_rate_to_usd("USD") → 1.0
    """
    currency = currency.upper()
    if currency == "USD":
        return 1.0

    now = datetime.datetime.utcnow()
    cached_at = _cache_ts.get(currency)
    if cached_at and (now - cached_at).seconds < CACHE_MINUTES * 60 and currency in _cache:
        return _cache[currency]

    # Intentar obtener tasa en vivo
    try:
        url = f"https://open.er-api.com/v6/latest/USD"
        with urllib.request.urlopen(url, timeout=8) as resp:
            data = json.loads(resp.read())
            rates = data.get("rates", {})
            if currency in rates:
                # rates[currency] = cuántas unidades de currency vale 1 USD
                rate_usd_to_cur = rates[currency]
                rate_cur_to_usd = 1.0 / rate_usd_to_cur
                _cache[currency] = rate_cur_to_usd
                _cache_ts[currency] = now
                return rate_cur_to_usd
    except Exception as e:
        print(f"  ⚠️  No se pudo obtener tasa {currency}: {e}")

    # Fallback: tasas aproximadas hardcodeadas
    fallback = {
        "EUR": 1.08,
        "ARS": 0.00095,   # ~1050 ARS por USD (actualizar si hace falta)
        "BRL": 0.20,
        "CLP": 0.0011,
        "COP": 0.00025,
    }
    return fallback.get(currency, 1.0)


def convert_to_usd(amount: float, from_currency: str) -> float:
    """Convierte `amount` en `from_currency` a USD."""
    rate = get_rate_to_usd(from_currency)
    return round(amount * rate, 2)


def convert_from_usd(amount_usd: float, to_currency: str) -> float:
    """Convierte `amount_usd` USD a `to_currency`."""
    rate = get_rate_to_usd(to_currency)
    if rate == 0:
        return amount_usd
    return round(amount_usd / rate, 2)


def format_price(amount_usd: float, display_currency: str) -> str:
    """
    Formatea un precio en USD como string en la moneda deseada.
    Ej: format_price(650.0, "EUR") → "€601"
         format_price(650.0, "ARS") → "$684,210"
    """
    symbols = {"USD": "USD ", "EUR": "€", "ARS": "$"}
    sym = symbols.get(display_currency, display_currency + " ")
    converted = convert_from_usd(amount_usd, display_currency)
    if display_currency == "ARS":
        return f"{sym}{converted:,.0f}"
    return f"{sym}{converted:,.0f}"
