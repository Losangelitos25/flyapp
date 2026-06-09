"""
Plugin: Flybondi
Busca vuelos low-cost en flybondi.com usando su API interna.
Sin key requerida. Solo rutas que opera Flybondi (principalmente domésticos AR + regionales).
"""

import urllib.request
import urllib.parse
import json
import datetime


# Rutas que opera Flybondi (origen → destinos disponibles)
FLYBONDI_ROUTES = {
    "AEP": ["BRC", "IGR", "MDZ", "COR", "TUC", "SLA", "NQN", "USH", "MDQ", "RGL", "REL", "PMY"],
    "EZE": ["BRC", "IGR", "MDZ", "COR", "TUC", "SLA", "NQN", "USH", "MDQ", "GRU", "SCL", "MVD"],
    "COR": ["AEP", "BRC", "MDZ", "SLA", "IGR", "USH"],
    "MDZ": ["AEP", "EZE", "COR", "BRC", "SLA"],
    "BRC": ["AEP", "EZE", "COR", "MDZ"],
    "IGR": ["AEP", "EZE", "COR"],
    "SLA": ["AEP", "EZE", "COR", "MDZ"],
    "TUC": ["AEP", "EZE"],
    "USH": ["AEP", "EZE"],
    "GRU": ["EZE"],
    "SCL": ["EZE"],
    "MVD": ["EZE"],
}


def search(route: dict) -> dict | None:
    """
    Busca el vuelo más barato en Flybondi para la ruta dada.
    Acepta el mismo formato de ruta que google_flights.py
    """
    origin      = route.get("origin", "AEP")
    destination = route.get("scope_value") or route.get("destination", "BRC")
    date_from   = route.get("date_from")
    date_to     = route.get("date_to")
    passengers  = route.get("passengers", 1)

    # Verificar que Flybondi opere esta ruta
    available = FLYBONDI_ROUTES.get(origin, [])
    if destination not in available:
        print(f"  ⚠️  Flybondi no opera {origin}→{destination}. Rutas disponibles desde {origin}: {', '.join(available)}")
        return None

    print(f"  🟡 Flybondi: buscando {origin} → {destination}")

    start = datetime.date.fromisoformat(date_from)
    end   = datetime.date.fromisoformat(date_to)
    delta = (end - start).days
    step  = max(1, min(3, delta // 6)) if delta > 0 else 1
    dates = [start + datetime.timedelta(days=i) for i in range(0, delta + 1, step)]

    best = None

    for dep_date in dates:
        result = _fetch_flybondi(origin, destination, dep_date, passengers)
        if result is None:
            continue
        if best is None or result["price_usd"] < best["price_usd"]:
            best = {**result, "best_dest": destination, "source": "Flybondi"}

    if best:
        print(f"  ✅ Flybondi mejor precio: USD {best['price_usd']:.0f} ({best['best_date']})")
    else:
        print(f"  ⚠️  Flybondi: sin resultados para {origin}→{destination}")

    return best


def _fetch_flybondi(origin: str, destination: str, dep_date: datetime.date, passengers: int) -> dict | None:
    """
    Consulta la API interna de Flybondi.
    Endpoint público (no requiere autenticación).
    """
    date_str = dep_date.strftime("%Y-%m-%d")
    url = (
        f"https://api.flybondi.com/v1/flights/search"
        f"?origin={origin}&destination={destination}"
        f"&departureDate={date_str}&adults={passengers}&currency=USD"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; flight-monitor/1.0)",
                "Accept": "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return _parse_flybondi_response(data, date_str)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # Sin vuelos ese día, normal
        print(f"  ⚠️  Flybondi HTTP {e.code} para {date_str}")
        return None
    except Exception as e:
        # Fallback: intentar scraping simple
        return _scrape_flybondi_fallback(origin, destination, dep_date, passengers)


def _parse_flybondi_response(data: dict, date_str: str) -> dict | None:
    """Parsea la respuesta JSON de la API de Flybondi."""
    try:
        flights = data.get("flights") or data.get("results") or data.get("data") or []
        if not flights:
            return None

        best_price = None
        for flight in flights:
            # La API puede devolver precio en distintos campos
            price = (
                flight.get("price")
                or flight.get("totalPrice")
                or flight.get("fare", {}).get("total")
                or flight.get("amount")
            )
            if price is None:
                continue
            try:
                price_float = float(str(price).replace(",", "").replace("$", "").strip())
            except ValueError:
                continue

            if best_price is None or price_float < best_price:
                best_price = price_float

        if best_price is None:
            return None

        return {
            "price_usd": best_price,
            "best_date": date_str,
            "airline": "Flybondi",
        }
    except Exception:
        return None


def _scrape_flybondi_fallback(origin: str, destination: str, dep_date: datetime.date, passengers: int) -> dict | None:
    """
    Fallback: consulta la URL de búsqueda de Flybondi y extrae precio del HTML.
    Menos confiable pero funciona si la API falla.
    """
    date_str = dep_date.strftime("%d/%m/%Y")
    url = (
        f"https://www.flybondi.com/ar/es/buscar-vuelos"
        f"?from={origin}&to={destination}&departure={date_str}&adults={passengers}&cabin=economy"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Buscar precio en el HTML (patrones comunes)
        import re
        patterns = [
            r'"price"\s*:\s*(\d+(?:\.\d+)?)',
            r'"totalPrice"\s*:\s*(\d+(?:\.\d+)?)',
            r'USD\s*(\d+(?:[.,]\d+)?)',
            r'\$\s*(\d+(?:[.,]\d+)?)',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, html)
            prices = []
            for m in matches:
                try:
                    p = float(m.replace(",", ""))
                    if 10 < p < 5000:  # filtro de sanidad
                        prices.append(p)
                except ValueError:
                    pass
            if prices:
                return {
                    "price_usd": min(prices),
                    "best_date": dep_date.isoformat(),
                    "airline": "Flybondi",
                }
    except Exception:
        pass

    return None


def get_available_routes(origin: str) -> list[str]:
    """Retorna los destinos disponibles desde un origen."""
    return FLYBONDI_ROUTES.get(origin.upper(), [])
