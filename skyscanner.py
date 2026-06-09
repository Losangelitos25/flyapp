"""
Plugin: Skyscanner
Busca vuelos via la API pública/interna de Skyscanner.
Sin API key de pago. Usa el endpoint de búsqueda del sitio.
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

    print(f"  🔵 Skyscanner: buscando {origin} → {destination}")

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
            best = {**result, "best_dest": destination, "source": "Skyscanner"}

    if best:
        print(f"  ✅ Skyscanner mejor precio: USD {best['price_usd']:.0f} ({best['best_date']})")
    else:
        print(f"  ⚠️  Skyscanner: sin resultados para {origin}→{destination}")

    return best


def _fetch(origin, destination, dep_date, passengers):
    date_str = dep_date.strftime("%Y-%m-%d")

    # Endpoint interno del buscador de Skyscanner
    url = (
        "https://www.skyscanner.com.ar/g/conductor/v1/fps3/search/"
        f"?market=AR&locale=es-AR&currency=USD"
        f"&queryLegs=%5B%7B%22originPlaceId%22%3A%7B%22iata%22%3A%22{origin}%22%7D"
        f"%2C%22destinationPlaceId%22%3A%7B%22iata%22%3A%22{destination}%22%7D"
        f"%2C%22date%22%3A%7B%22year%22%3A{dep_date.year}%2C%22month%22%3A{dep_date.month}%2C%22day%22%3A{dep_date.day}%7D%7D%5D"
        f"&adults={passengers}&childrenAges=&cabinClass=economy&excludedAgentsIds=&includedAgentsIds="
    )

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "es-AR,es;q=0.9",
            "Referer": "https://www.skyscanner.com.ar/",
            "x-skyscanner-channelid": "website",
            "x-skyscanner-market": "AR",
            "x-skyscanner-currency": "USD",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
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
        # Skyscanner devuelve itinerarios en distintas estructuras
        itineraries = (
            data.get("itineraries") or
            data.get("content", {}).get("results", {}).get("itineraries") or
            data.get("results", {}).get("itineraries") or
            {}
        )

        best_price = None
        best_airline = "Skyscanner"

        if isinstance(itineraries, dict):
            items = itineraries.values()
        elif isinstance(itineraries, list):
            items = itineraries
        else:
            return None

        for item in items:
            if not isinstance(item, dict):
                continue
            price = (
                item.get("price", {}).get("raw") or
                item.get("price", {}).get("amount") or
                item.get("cheapestPrice", {}).get("raw") or
                _deep_get(item, "pricingOptions", 0, "price", "raw")
            )
            if price is None:
                continue
            try:
                p = float(str(price).replace(",", "").strip())
            except ValueError:
                continue
            if best_price is None or p < best_price:
                best_price = p

        if best_price is None:
            return None

        return {"price_usd": best_price, "best_date": date_str, "airline": best_airline}
    except Exception:
        return None


def _deep_get(obj, *keys):
    for k in keys:
        try:
            obj = obj[k]
        except (KeyError, IndexError, TypeError):
            return None
    return obj


def _scrape_fallback(origin, destination, dep_date, passengers):
    date_str = dep_date.strftime("%Y-%m-%d")
    url = (
        f"https://www.skyscanner.com.ar/vuelos/{origin}/{destination}/{date_str}/"
        f"?adults={passengers}&currency=USD&locale=es-AR&market=AR"
    )
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "es-AR,es;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Buscar JSON embebido (Skyscanner usa React SSR)
        match = re.search(r'window\.__SKYSCANNER_REDUX_STATE__\s*=\s*({.+?});\s*</script>', html, re.DOTALL)
        if match:
            try:
                state = json.loads(match.group(1))
                prices = []
                _extract_prices_from_obj(state, prices)
                if prices:
                    return {"price_usd": min(prices), "best_date": dep_date.isoformat(), "airline": "Skyscanner"}
            except Exception:
                pass

        prices = _extract_prices_from_html(html)
        if prices:
            return {"price_usd": min(prices), "best_date": dep_date.isoformat(), "airline": "Skyscanner"}
    except Exception:
        pass
    return None


def _extract_prices_from_html(html):
    prices = []
    for pattern in [
        r'"raw"\s*:\s*(\d+(?:\.\d+)?)',
        r'"amount"\s*:\s*(\d+(?:\.\d+)?)',
        r'USD\s*(\d+(?:[.,]\d+)?)',
        r'"price"\s*:\s*(\d+(?:\.\d+)?)',
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
            if k in ("raw", "amount", "total", "price") and isinstance(v, (int, float)):
                if 10 < v < 8000:
                    prices.append(float(v))
            else:
                _extract_prices_from_obj(v, prices, depth + 1)
    elif isinstance(obj, list):
        for item in obj[:30]:
            _extract_prices_from_obj(item, prices, depth + 1)
