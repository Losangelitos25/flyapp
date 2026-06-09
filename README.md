# ✈️ Flight Monitor

Bot de monitoreo de precios de vuelos. Corre automáticamente en GitHub Actions y manda alertas por Telegram cuando baja el precio.

## Características

- 🔍 Busca en Google Flights sin API key
- 📉 Detecta bajas de precio y avisa por Telegram
- 📅 Informa feriados argentinos cercanos a tu vuelo
- 🌐 Dashboard web (GitHub Pages) para ver historial de precios
- ⚙️ Configuración de rutas y plugins desde el dashboard
- 🔌 Arquitectura modular: fácil agregar nuevas fuentes

## Setup rápido (15 minutos)

### 1. Subir al repo

```bash
git clone https://github.com/TU_USUARIO/flight-monitor
# Copiar todos los archivos
git add . && git commit -m "init" && git push
```

### 2. Crear bot de Telegram

1. Abrí Telegram y buscá `@BotFather`
2. Mandá `/newbot` y seguí las instrucciones
3. Copiá el token que te da (formato: `123456:ABC-DEF...`)

### 3. Obtener tu Chat ID

1. Buscá `@userinfobot` en Telegram
2. Mandá cualquier mensaje → te responde con tu ID

### 4. Cargar secreto en GitHub

- Ir a tu repo → **Settings** → **Secrets and variables** → **Actions**
- Click en **New repository secret**
- Nombre: `TELEGRAM_TOKEN`
- Valor: el token del paso 2

### 5. Activar GitHub Pages

- Settings → **Pages**
- Branch: `main`, carpeta: `/dashboard`
- Guardá. En ~1 minuto tenés el dashboard en `https://TU_USUARIO.github.io/flight-monitor/`

### 6. Configurar rutas

Editá `config.json` o usá el dashboard:

```json
{
  "routes": [
    {
      "id": "eze-mad",
      "label": "Buenos Aires → Madrid",
      "origin": "EZE",
      "destination": "MAD",
      "date_from": "2025-11-01",
      "date_to": "2025-11-30",
      "max_price_usd": 700,
      "passengers": 1,
      "enabled": true
    }
  ]
}
```

### 7. Primer run manual

- Ir a **Actions** → **Flight Monitor** → **Run workflow**

---

## Estructura del proyecto

```
flight-monitor/
├── .github/
│   └── workflows/
│       └── monitor.yml       # GitHub Actions (corre cada 6 hs)
├── plugins/
│   ├── google_flights.py     # Fuente principal de precios
│   ├── holidays_ar.py        # Feriados nacionales
│   └── notifier.py           # Bot de Telegram
├── dashboard/
│   ├── index.html            # App web (GitHub Pages)
│   └── prices.json           # Historial de precios (auto-generado)
├── monitor.py                # Script principal
├── config.json               # Tu configuración
└── requirements.txt
```

## Agregar plugins

Creá un archivo en `plugins/`, por ejemplo `plugins/skyscanner.py`:

```python
def search_skyscanner(origin, destination, date_from, date_to, passengers):
    # Tu lógica acá
    return {"price_usd": 650.0, "best_date": "2025-11-15", "airline": "Iberia"}
```

Luego habilitalo en `config.json`:
```json
"plugins": {
  "skyscanner": { "enabled": true }
}
```

## Frecuencia de chequeo

Editá el cron en `.github/workflows/monitor.yml`:

```yaml
- cron: '0 0,6,12,18 * * *'   # cada 6 horas
- cron: '0 */3 * * *'          # cada 3 horas
- cron: '0 8,20 * * *'         # 2 veces al día (8 y 20 UTC)
```

GitHub Actions da **2000 minutos gratis/mes**. Corriendo cada 6 hs usás ~12 min/mes.

## Costos

| Servicio | Costo |
|---|---|
| GitHub Actions | Gratis (2000 min/mes) |
| GitHub Pages | Gratis |
| Telegram Bot | Gratis |
| Google Flights | Gratis (sin API key) |
| **Total** | **$0** |
