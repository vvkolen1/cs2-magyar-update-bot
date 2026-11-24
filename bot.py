import os
import json
import re
import html
import requests
from pathlib import Path
from datetime import datetime, timezone

STEAM_NEWS_API = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash"]
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
DISCORD_API = "https://discord.com/api/v10"
STATE_PATH = Path("state.json")


def clean_steam_markup(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n\n", text)
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"\[url=[^\]]+\](.*?)\[/url\]", r"\1", text, flags=re.I | re.S)
    text = re.sub(r"\[/?(?:b|i|u|h[1-6]|list|olist|quote|code)\]", "", text, flags=re.I)
    text = re.sub(r"\[img\].*?\[/img\]", "", text, flags=re.I | re.S)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def read_state():
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_state(state):
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_news():
    r = requests.get(
        STEAM_NEWS_API,
        params={"appid": 730, "count": 20, "maxlength": 0},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("appnews", {}).get("newsitems", [])



def translate(title, body):
    key = os.environ.get("GEMINI_API_KEY")

    if not key:
        raise RuntimeError("Hiányzik a GEMINI_API_KEY!")

    prompt = f"""Fordítsd le pontosan és természetes magyarra ezt a hivatalos CS2 hírt.
Ne találj ki adatot. Őrizd meg a pályaneveket és szakkifejezéseket.
Kizárólag JSON legyen a válasz:
{{"title":"magyar cím","body":"magyar fordítás"}}

EREDETI CÍM:
{title}

EREDETI SZÖVEG:
{body[:20000]}
"""

    errors = []

    for model in GEMINI_MODELS:
        url = f"{GEMINI_API_BASE}{model}:generateContent"

        try:
            response = requests.post(
                url,
                params={"key": key},
                json={
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.2,
                        "responseMimeType": "application/json",
                        "maxOutputTokens": 8192
                    }
                },
                timeout=90
            )

            response.raise_for_status()

            data = response.json()

            raw = data["candidates"][0]["content"]["parts"][0]["text"]
            result = json.loads(raw)

            hu_title = result["title"].strip()
            hu_body = result["body"].strip()

            if not hu_title or not hu_body:
                raise ValueError("Üres Gemini-fordítás!")

            logging.info("Gemini fordítás sikeres: %s", model)

            return hu_title, hu_body

        except (
            requests.RequestException,
            KeyError,
            IndexError,
            ValueError,
            TypeError
        ) as error:

            errors.append(f"{model}: {error}")

            logging.warning(
                "Gemini modell nem működik: %s",
                model
            )

    raise RuntimeError(
        "Egyik Gemini modell sem tudott fordítani: "
        + " | ".join(errors)
    )



def post_discord(title, body, link, published):
    token = os.environ["DISCORD_BOT_TOKEN"]
    channel = os.environ["DISCORD_CHANNEL_ID"]
    embed = {
        "title": ("🇭🇺 " + title)[:256],
        "description": body[:3900],
        "url": link or "https://store.steampowered.com/news/app/730",
        "color": 0xD32F2F,
        "footer": {"text": "CS2 Magyar Szerver • AI-fordítás"},
    }
    if published:
        try:
            embed["timestamp"] = datetime.fromtimestamp(
                int(published), tz=timezone.utc
            ).isoformat()
        except (ValueError, TypeError, OSError):
            pass
    r = requests.post(
        f"{DISCORD_API}/channels/{channel}/messages",
        headers={"Authorization": f"Bot {token}"},
        json={
            "content": "🔔 **Új hivatalos CS2 hír!**",
            "embeds": [embed],
            "allowed_mentions": {"parse": []},
        },
        timeout=30,
    )
    r.raise_for_status()


def main():
    for env_name in ("DISCORD_BOT_TOKEN", "DISCORD_CHANNEL_ID", "GEMINI_API_KEY"):
        if not os.environ.get(env_name):
            raise RuntimeError(f"Hiányzó környezeti változó: {env_name}")

    news = fetch_news()
    if not news:
        print("Most nem érkezett Steam-hír.")
        return

    state = read_state()
    newest_id = str(news[0].get("gid", ""))

    # Első futás: a jelenlegi legfrissebb hírt megjegyzi, nem küld régi híreket.
    if not state.get("last_gid"):
        write_state({"last_gid": newest_id})
        print("Első futás kész: kezdőállapot mentve.")
        return

    previous_id = str(state["last_gid"])
    unseen = []
    for item in news:
        gid = str(item.get("gid", ""))
        if gid == previous_id:
            break
        if gid:
            unseen.append(item)

    # Régebbi új hírtől a frissebb felé küld.
    for item in reversed(unseen):
        original_title = clean_steam_markup(item.get("title", "CS2 frissítés"))
        original_body = clean_steam_markup(item.get("contents", ""))
        if not original_body:
            original_body = "A hivatalos hír nem tartalmaz szöveges leírást."
        hu_title, hu_body = translate(original_title, original_body)
        post_discord(
            hu_title,
            hu_body,
            item.get("url"),
            item.get("date"),
        )
        print("Elküldve:", item.get("gid"), hu_title)

    if unseen:
        write_state({"last_gid": newest_id})
    else:
        print("Nincs új CS2 hír.")


if __name__ == "__main__":
    main()
