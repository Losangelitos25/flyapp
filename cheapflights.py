"""
Plugin: CheapFlights
Busca vuelos en cheapflights.com.ar (powered by Kayak).
Sin API key. Usa el endpoint interno del buscador.
"""

import urllib.request
import urllib.parse
import json
import datetime
import re


def search(route: dict) -> dict | None:
    origin      = route.get("origin", "EZE")
    destination = route.get("scope_value") or route.get("destination", "MAD")
    date_from   = route.get("date_from")
    date_to     = route.get("date_to")
    passengers  = route.get("passengers", 1)

    print(f"  🟣 CheapFlights: buscando {origin} → {destination}")

    start = datetime.date.fromisoformat(date_from)
    end   = datetime.date.fromisoformat(date_to)
    delta = (end - start).days
    step  = max(1, min(4, delta // 6)) if delta > 0 else 1
    dates = [start + datetime.timedelta(days=i) for i in range(0, delta + 1, step)]

    best = None

    for dep_date in dates:
        result = _fetch(origin, destination, dep_date, passengers)
        if result is None:
            continue
        if best is None or result["price_usd"] < best["price_usd"]:
            best = {**result, "best_dest": destination, "source": "CheapFlights"}

    if best:
        print(f"  ✅ CheapFlights mejor precio: USD {best['price_usd']:.0f} ({best['best_date']})")
    else:
        print(f"  ⚠️  CheapFlights: sin resultados para {origin}→{destination}")

    return best


def _fetch(origin, destination, dep_date, passengers):
    date_str = dep_date.strftime("%Y-%m-%d")

    # CheapFlights usa la infraestructura de Kayak internamente
    # Endpoint de búsqueda de vuelos de ida
    url = (
        "https://www.cheapflights.com.ar/api/search/flight"
        f"?origin={origin}&destination={destination}"
        f"&departureDate={date_str}&adults={passengers}"
        f"&currency=USD&market=AR&locale=es-AR&cabin=economy"
    )

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "es-AR,es;q=0.9",
            "Referer": "https://www.cheapflights.com.ar/",
        })
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read())
            return _parse(data, date_str)
    except urllib.error.HTTPError as e:
        if e.code in (404, 204):
            return None
        return _scrape_fallback(origin, destination, dep_date, passengers)
    except Exception:
        return _scrape_fallback(origin, destination, dep_date, passengers)


def _parse(data, date_str):
    try:
        results = (
            data.get("results") or data.get("flights") or
            data.get("data") or data.get("itineraries") or []
        )
        if not results:
            return None

        best_price = None
        best_airline = "CheapFlights"

        items = results.values() if isinstance(results, dict) else results

        for r in items:
            if not isinstance(r, dict):
                continue
            price = (
                r.get("price") or r.get("totalPrice") or
                r.get("fare", {}).get("total") or
                r.get("amount") or r.get("lowestPrice")
            )
            if price is None:
                continue
            try:
                p = float(str(price).replace(",", "").replace("$", "").strip())
            except ValueError:
                continue
            if best_price is None or p < best_price:
                best_price = p
                best_airline = r.get("airline", r.get("carrier", "CheapFlights"))

        if best_price is None:
            return None

        return {"price_usd": best_price, "best_date": date_str, "airline": best_airline}
    except Exception:
        return None


def _scrape_fallback(origin, destination, dep_date, passengers):
    date_str_url = dep_date.strftime("%Y-%m-%d")
    url = (
        f"https://www.cheapflights.com.ar/vuelos/{origin}-{destination}/{date_str_url}"
        f"?adults={passengers}&currency=USD"
    )

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "es-AR,es;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Buscar JSON embebido
        for pattern in [
            r'window\.__STATE__\s*=\s*({.+?});</script>',
            r'window\.__INITIAL_DATA__\s*=\s*({.+?});</script>',
        ]:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    obj = json.loads(match.group(1))
                    prices = []
                    _extract_prices_from_obj(obj, prices)
                    if prices:
                        return {"price_usd": min(prices), "best_date": dep_date.isoformat(), "airline": "CheapFlights"}
                except Exception:
                    pass

        prices = _extract_prices_from_html(html)
        if prices:
            return {"price_usd": min(prices), "best_date": dep_date.isoformat(), "airline": "CheapFlights"}
    except Exception:
        pass
    return None


def _extract_prices_from_html(html):
    prices = []
    for pattern in [
        r'"price"\s*:\s*(\d+(?:\.\d+)?)',
        r'"totalPrice"\s*:\s*(\d+(?:\.\d+)?)',
        r'"lowestPrice"\s*:\s*(\d+(?:\.\d+)?)',
        r'USD\s*(\d+(?:[.,]\d+)?)',
    ]:
        for m in re.findall(pattern, html):
            try:
                p = float(m.replace(",", ""))
                if 10 < p < 8000:
                    prices.append(p)
            except ValueError:
                pass
    return prices


def _extract_prices_from_obj(obj, prices, depth=0):
    if depth > 6:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("price", "totalPrice", "lowestPrice", "amount", "fare") and isinstance(v, (int, float)):
                if 10 < v < 8000:
                    prices.append(float(v))
            else:
                _extract_prices_from_obj(v, prices, depth + 1)
    elif isinstance(obj, list):
        for item in obj[:30]:
            _extract_prices_from_obj(item, prices, depth + 1)
