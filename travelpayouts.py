"""
Plugin: TravelPayouts (Aviasales Data API)
Documentación: https://www.travelpayouts.com/developers/api

Requiere:
  - Token gratuito en https://www.travelpayouts.com/developers/api
  - Variable de entorno: TRAVELPAYOUTS_TOKEN

Habilitar en config.json:
  "plugins": {
    "travelpayouts": { "enabled": true }
  }

Nota: esta API devuelve precios de caché (no tiempo real).
Son actualizados cada ~12 hs y son muy precisos para monitoreo.
El endpoint `prices/cheap` retorna los vuelos más baratos para
una ruta en un mes dado, ideal para nuestro caso de uso.
"""

import os
import requests
from datetime import datetime

# Precios de caché por mes (más confiable y sin límite de calls)
API_URL = "https://api.travelpayouts.com/v1/prices/cheap"


def search(route: dict) -> dict | None:
    """
    Retorna el vuelo más barato encontrado para la ruta dada.

    Parámetros esperados en `route`:
      origin       : IATA de origen, ej. "EZE"
      destination  : IATA de destino, ej. "MAD"  (o scope_value si scope_type == "airport")
      date_from    : "YYYY-MM-DD"
      date_to      : "YYYY-MM-DD"  (opcional; se usa el mismo mes que date_from)
      passengers   : int — la API no filtra por pasajeros; se devuelve precio por persona

    Retorna dict con claves:
      price_usd, best_date, best_dest, airline, source
    o None si no hay resultados.
    """
    token = os.environ.get("TRAVELPAYOUTS_TOKEN", "")
    if not token:
        print("  ⚠️  TravelPayouts: falta TRAVELPAYOUTS_TOKEN en variables de entorno")
        return None

    origin      = route.get("origin", "EZE")
    destination = route.get("scope_value") or route.get("destination", "")
    date_from   = route.get("date_from", "")

    if not destination or not date_from:
        print("  ⚠️  TravelPayouts: faltan destination o date_from en la ruta")
        return None

    # La API acepta "YYYY-MM" para depart_date
    try:
        depart_month = datetime.strptime(date_from, "%Y-%m-%d").strftime("%Y-%m")
    except ValueError:
        depart_month = date_from[:7]

    params = {
        "origin":       origin,
        "destination":  destination,
        "depart_date":  depart_month,
        "currency":     "usd",
        "token":        token,
        "limit":        30,   # hasta 30 resultados; elegimos el más barato
    }

    try:
        resp = requests.get(API_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"  ⚠️  TravelPayouts: error de red → {e}")
        return None

    if not data.get("success"):
        print(f"  ⚠️  TravelPayouts: respuesta no exitosa → {data}")
        return None

    flights_by_dest = data.get("data", {})
    if not flights_by_dest:
        return None

    # Estructura: { "MAD": { "0": { price, airline, departure_at, ... } } }
    # Aplanamos todos los vuelos de todos los destinos devueltos
    all_flights = []
    for dest_iata, numbered_flights in flights_by_dest.items():
        for _, flight in numbered_flights.items():
            flight["_dest"] = dest_iata
            all_flights.append(flight)

    if not all_flights:
        return None

    best = min(all_flights, key=lambda f: float(f.get("price", 999999)))

    price_usd = float(best.get("price", 0))
    best_dest = best.get("_dest", destination)
    airline   = best.get("airline", "Desconocida")

    # departure_at: "2025-11-14T06:00:00" → "2025-11-14"
    raw_date  = best.get("departure_at", "")
    best_date = raw_date[:10] if raw_date else ""

    return {
        "price_usd": price_usd,
        "best_date": best_date,
        "best_dest": best_dest,
        "airline":   airline,
        "source":    "TravelPayouts",
    }
