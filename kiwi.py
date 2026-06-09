"""
Plugin: Kiwi (Tequila API)
Documentación: https://tequila.kiwi.com/portal/docs/tequila_api/search_api

Requiere:
  - API key gratuita en https://tequila.kiwi.com/portal/login
  - Variable de entorno: KIWI_API_KEY

Habilitar en config.json:
  "plugins": {
    "kiwi": { "enabled": true }
  }
"""

import os
import requests
from datetime import datetime

API_URL = "https://api.tequila.kiwi.com/v2/search"


def search(route: dict) -> dict | None:
    """
    Retorna el vuelo más barato encontrado para la ruta dada.

    Parámetros esperados en `route`:
      origin       : IATA de origen, ej. "EZE"
      destination  : IATA de destino, ej. "MAD"  (o scope_value si scope_type == "airport")
      date_from    : "YYYY-MM-DD"
      date_to      : "YYYY-MM-DD"
      passengers   : int (default 1)

    Retorna dict con claves:
      price_usd, best_date, best_dest, airline, source
    o None si no hay resultados.
    """
    api_key = os.environ.get("KIWI_API_KEY", "")
    if not api_key:
        print("  ⚠️  Kiwi: falta KIWI_API_KEY en variables de entorno")
        return None

    origin      = route.get("origin", "EZE")
    destination = route.get("scope_value") or route.get("destination", "")
    date_from   = route.get("date_from", "")
    date_to     = route.get("date_to", date_from)
    passengers  = int(route.get("passengers", 1))

    if not destination or not date_from:
        print("  ⚠️  Kiwi: faltan destination o date_from en la ruta")
        return None

    # Kiwi espera fechas en formato DD/MM/YYYY
    def to_kiwi_date(s):
        return datetime.strptime(s, "%Y-%m-%d").strftime("%d/%m/%Y")

    params = {
        "fly_from":        origin,
        "fly_to":          destination,
        "date_from":       to_kiwi_date(date_from),
        "date_to":         to_kiwi_date(date_to),
        "adults":          passengers,
        "curr":            "USD",
        "sort":            "price",
        "asc":             1,
        "limit":           1,
        "flight_type":     "oneway",
        "one_for_city":    1,
        "max_stopovers":   2,
    }

    headers = {
        "apikey": api_key,
        "accept": "application/json",
    }

    try:
        resp = requests.get(API_URL, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"  ⚠️  Kiwi: error de red → {e}")
        return None

    flights = data.get("data", [])
    if not flights:
        return None

    best = flights[0]

    price_usd = float(best.get("price", 0))
    best_date = best.get("local_departure", "")[:10]  # "YYYY-MM-DDTHH:MM:SS" → "YYYY-MM-DD"
    best_dest = best.get("flyTo", destination)

    # Nombre de aerolínea: tomamos el primer tramo
    airlines = best.get("airlines", [])
    airline = airlines[0] if airlines else "Desconocida"

    return {
        "price_usd": price_usd,
        "best_date": best_date,
        "best_dest": best_dest,
        "airline":   airline,
        "source":    "Kiwi",
    }
