"""
Plugin: Feriados Argentina
Obtiene feriados nacionales via Nager.Date (API pública, sin key).
Útil para saber si vale la pena volar en una fecha puntual.
"""

import urllib.request
import json
import datetime


def get_upcoming_holidays(days_ahead: int = 90, country: str = "AR") -> list[dict]:
    """
    Devuelve lista de feriados en los próximos `days_ahead` días.
    Cada item: {"date": "2025-10-12", "name": "Día de la Raza"}
    """
    today = datetime.date.today()
    years = {today.year, (today + datetime.timedelta(days=days_ahead)).year}
    holidays = []

    for year in years:
        url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country}"
        try:
            with urllib.request.urlopen(url, timeout=8) as resp:
                data = json.loads(resp.read())
                for h in data:
                    h_date = datetime.date.fromisoformat(h["date"])
                    if today <= h_date <= today + datetime.timedelta(days=days_ahead):
                        holidays.append({
                            "date": h["date"],
                            "name": h.get("localName", h.get("name", "Feriado")),
                        })
        except Exception as e:
            print(f"  ⚠️  No se pudo obtener feriados {year}: {e}")

    holidays.sort(key=lambda x: x["date"])
    return holidays
