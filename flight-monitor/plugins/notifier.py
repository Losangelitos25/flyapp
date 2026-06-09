"""
Plugin: Notifier
Envía mensajes por Telegram usando el Bot API.
"""

import urllib.request
import urllib.parse
import json


def send_telegram(token: str, chat_id: str, message: str) -> bool:
    """
    Manda un mensaje de texto por Telegram (Markdown).
    No requiere librerías externas, usa solo urllib.
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }

    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                print(f"  📨 Telegram OK → {chat_id}")
                return True
            else:
                print(f"  ❌ Telegram error: {result}")
                return False
    except Exception as e:
        print(f"  ❌ Error enviando Telegram: {e}")
        return False
