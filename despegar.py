"""
Plugin: Despegar
Busca vuelos en despegar.com usando su API interna.
Funciona para vuelos domésticos e internacionales desde Argentina.
"""

import urllib.request
import urllib.parse
import json
import datetime
import re


def search(route: dict) -> dict | None:
    """
    Busca el vuelo más barato en Despegar para la ruta dada.
    Acepta el mismo formato de ruta que google_flights.py
    """
    origin      = route.get("origin", "EZE")
    destination = route.get("scope_value") or route.get("destination", "MAD")
    date_from   = route.get("date_from")
    date_to     = route.get("date_to")
    passengers  = route.get("passengers", 1)

    print(f"  🔵 Despegar: buscando {origin} → {destination}")

    start = datetime.date.fromisoformat(date_from)
    end   = datetime.date.fromisoformat(date_to)
    delta = (end - start).days
    step  = max(1, min(4, delta // 6)) if delta > 0 else 1
    dates = [start + datetime.timedelta(days=i) for i in range(0, delta + 1, step)]

    best = None

    for dep_date in dates:
        result = _fetch_despegar(origin, destination, dep_date, passengers)
        if result is None:
            continue
        if best is None or result["price_usd"] < best["price_usd"]:
            best = {**result, "best_dest": destination, "source": "Despegar"}

    if best:
        print(f"  ✅ Despegar mejor precio: USD {best['price_usd']:.0f} ({best['best_date']})")
    else:
        print(f"  ⚠️  Despegar: sin resultados para {origin}→{destination}")

    return best


def _fetch_despegar(origin: str, destination: str, dep_date: datetime.date, passengers: int) -> dict | None:
    """
    Consulta la API interna de Despegar.
    Usa el endpoint de búsqueda de vuelos de ida.
    """
    date_str = dep_date.strftime("%Y-%m-%d")

    # API endpoint de Despegar (observada en el tráfico del sitio)
    url = "https://www.despegar.com.ar/api/flights/v2/search"
    params = {
        "from": origin,
        "to": destination,
        "departureDate": date_str,
        "adults": passengers,
        "children": 0,
        "infants": 0,
        "cabin": "Y",           # Economy
        "currency": "USD",
        "market": "AR",
        "lang": "es_AR",
    }

    full_url = url + "?" + urllib.parse.urlencode(params)

    try:
        req = urllib.request.Request(
            full_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "es-AR,es;q=0.9",
                "Referer": "https://www.despegar.com.ar/",
                "x-market": "AR",
            }
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read())
            return _parse_despegar_response(data, date_str)

    except urllib.error.HTTPError as e:
        if e.code in (404, 204):
            return None
        # Intentar fallback por scraping
        return _scrape_despegar_fallback(origin, destination, dep_date, passengers)
    except Exception:
        return _scrape_despegar_fallback(origin, destination, dep_date, passengers)


def _parse_despegar_response(data: dict, date_str: str) -> dict | None:
    """Parsea la respuesta JSON de Despegar."""
    try:
        # Despegar puede devolver distintas estructuras según versión de API
        clusters = (
            data.get("clusters")
            or data.get("results")
            or data.get("flights")
            or data.get("data", {}).get("clusters")
            or []
        )

        if not clusters:
            return None

        best_price = None
        best_airline = "Desconocida"

        for cluster in clusters:
            # Precio puede estar en distintos lugares
            price = None
            if isinstance(cluster, dict):
                price = (
                    cluster.get("price", {}).get("total")
                    or cluster.get("totalFare")
                    or cluster.get("fare", {}).get("total")
                    or cluster.get("priceDetail", {}).get("total")
                    or cluster.get("amount")
                )
                airline = (
                    cluster.get("airline")
                    or cluster.get("segments", [{}])[0].get("airline", "Desconocida")
                    if cluster.get("segments") else "Desconocida"
                )
            else:
                continue

            if price is None:
                continue
            try:
                price_float = float(str(price).replace(",", "").replace("$", "").strip())
            except ValueError:
                continue

            if best_price is None or price_float < best_price:
                best_price = price_float
                best_airline = airline

        if best_price is None:
            return None

        return {
            "price_usd": best_price,
            "best_date": date_str,
            "airline": f"{best_airline} (Despegar)",
        }
    except Exception:
        return None


def _scrape_despegar_fallback(origin: str, destination: str, dep_date: datetime.date, passengers: int) -> dict | None:
    """
    Fallback: busca precio en la URL pública de Despegar.
    """
    date_str = dep_date.strftime("%Y-%m-%d")
    url = (
        f"https://www.despegar.com.ar/vuelos/resultados/ida/"
        f"{origin}/{destination}/{date_str}/{passengers}/0/0/economy/usd"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "es-AR,es;q=0.9",
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Buscar JSON embebido en el HTML (Despegar usa Next.js / SSR)
        json_patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
            r'"totalFare"\s*:\s*(\d+(?:\.\d+)?)',
            r'"price"\s*:\s*\{\s*"total"\s*:\s*(\d+(?:\.\d+)?)',
            r'USD\s*(\d+(?:[.,]\d+)?)',
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            prices = []
            for m in matches:
                # Si es un objeto JSON grande, intentar parsearlo
                if m.startswith("{"):
                    try:
                        obj = json.loads(m)
                        _extract_prices_from_obj(obj, prices)
                    except Exception:
                        pass
                else:
                    try:
                        p = float(m.replace(",", ""))
                        if 10 < p < 10000:
                            prices.append(p)
                    except ValueError:
                        pass

            if prices:
                return {
                    "price_usd": min(prices),
                    "best_date": dep_date.isoformat(),
                    "airline": "Despegar",
                }

    except Exception:
        pass

    return None


def _extract_prices_from_obj(obj, prices: list, depth: int = 0):
    """Recursivamente extrae valores numéricos que parecen precios de vuelos."""
    if depth > 5:
        return
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key.lower() in ("total", "totalfare", "price", "amount", "fare") and isinstance(val, (int, float)):
                if 10 < val < 10000:
                    prices.append(float(val))
            else:
                _extract_prices_from_obj(val, prices, depth + 1)
    elif isinstance(obj, list):
        for item in obj[:20]:  # limitar para no explotar
            _extract_prices_from_obj(item, prices, depth + 1)
