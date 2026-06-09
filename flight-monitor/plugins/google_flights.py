"""
Plugin: Google Flights
Soporta destino fijo (IATA) y destino abierto (región/país/continente/provincia).
Usa fast-flights. Devuelve el precio más bajo encontrado.
"""

import datetime
from plugins.destinations import get_airports_for_scope
from plugins.currency import convert_to_usd


def search(route: dict) -> dict | None:
    """
    Punto de entrada principal. Acepta un dict de ruta del config.json.
    Soporta:
      - route["destination"] = "MAD"                          → destino fijo
      - route["scope_type"] + route["scope_value"]            → destino abierto
        ej: scope_type="continent", scope_value="Europa"

    Devuelve:
        {"price_usd": float, "best_date": str, "best_dest": str, "airline": str}
    """
    origin     = route.get("origin", "EZE")
    date_from  = route.get("date_from")
    date_to    = route.get("date_to")
    passengers = route.get("passengers", 1)

    # Resolver lista de destinos
    scope_type  = route.get("scope_type", "airport")
    scope_value = route.get("scope_value") or route.get("destination", "")

    if scope_type == "airport" and not scope_value:
        scope_value = route.get("destination", "")

    destinations = get_airports_for_scope(scope_type, scope_value)

    if not destinations:
        print(f"  ⚠️  Sin destinos para scope_type={scope_type} scope_value={scope_value}")
        return None

    print(f"  📍 Buscando en {len(destinations)} destino(s): {', '.join(destinations[:6])}{'...' if len(destinations) > 6 else ''}")

    best = None

    for dest_iata in destinations:
        result = search_google_flights(origin, dest_iata, date_from, date_to, passengers)
        if result is None:
            continue
        if best is None or result["price_usd"] < best["price_usd"]:
            best = {**result, "best_dest": dest_iata}

    return best


def search_google_flights(origin: str, destination: str, date_from: str, date_to: str, passengers: int = 1) -> dict | None:
    """
    Busca vuelos para un par O→D específico en un rango de fechas.
    Devuelve el precio más bajo encontrado.
    """
    try:
        from fast_flights import FlightData, Passengers, get_flights
    except ImportError:
        print("  ⚠️  fast-flights no instalado. Usando mock.")
        return _mock_result(origin, destination, date_from)

    best = None
    start = datetime.date.fromisoformat(date_from)
    end   = datetime.date.fromisoformat(date_to)
    delta = (end - start).days

    # Samplear cada 4 días para no sobrecargar
    step  = max(1, min(4, delta // 6)) if delta > 0 else 1
    dates = [start + datetime.timedelta(days=i) for i in range(0, delta + 1, step)]

    for dep_date in dates:
        try:
            result = get_flights(
                FlightData(
                    date=dep_date.strftime("%Y-%m-%d"),
                    from_airport=origin,
                    to_airport=destination,
                ),
                passengers=Passengers(adults=passengers),
                trip="one-way",
                fetch_mode="fallback",
            )
            if not result or not result.flights:
                continue
            for flight in result.flights:
                price = _parse_price(flight.price)
                if price is None:
                    continue
                if best is None or price < best["price_usd"]:
                    best = {
                        "price_usd": price,
                        "best_date": dep_date.isoformat(),
                        "airline":   getattr(flight, "name", "Desconocida"),
                    }
        except Exception as e:
            # Silenciar errores por destino individual para no interrumpir el loop
            pass

    return best


def _parse_price(price_str: str) -> float | None:
    if not price_str:
        return None
    clean = (price_str
             .replace(",", "")
             .replace(".", "")
             .replace("$", "")
             .replace("USD", "")
             .replace("US", "")
             .replace("€", "")
             .replace("EUR", "")
             .strip())
    try:
        return float(clean)
    except ValueError:
        return None


def _mock_result(origin, destination, date_from) -> dict:
    import random
    return {
        "price_usd": round(random.uniform(350, 1400), 2),
        "best_date": date_from,
        "airline":   "MOCK Airlines",
    }
