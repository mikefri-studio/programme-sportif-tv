import os
import re
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup

URL = "https://tv-sports.fr/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

TIME_RE = re.compile(r"^\d{1,2}h\d{2}$")

# Chaînes françaises connues (les plus spécifiques d'abord)
KNOWN_CHANNELS = [
    "Canal+ Sport 360", "Canal+ Première League", "Canal+ Sport", "Canal+ Foot", "Canal+ Live", "Canal+",
    "beIN SPORTS MAX", "beIN SPORTS",
    "L'Équipe", "L'Equipe",
    "Eurosport 1", "Eurosport 2", "Eurosport",
    "RMC Sport", "France 2", "France 3", "France 4",
    "DAZN", "Ligue 1+", "Sport en France", "Automoto", "Equidia", "MGG TV", "ABXplore",
    "Golf+", "Infosport+", "TV5MONDE", "Tipik", "RTS 1", "RTS 2", "VOOsport", "Club RTL", "VTM 2",
]

SPORT_RULES = [
    ("Formule 1", ["Formule 1", "F1"]),
    ("Football", ["Foot", "Football", "Ligue 1", "Premier League", "Liga", "Bundesliga", "Serie A", "Champions League", "Europa"]),
    ("Rugby", ["Rugby", "Top 14", "Pro D2"]),
    ("Tennis", ["Tennis", "ATP", "WTA"]),
    ("Cyclisme", ["Cyclisme", "Tour de France", "Vuelta", "Giro", "Classique"]),
    ("Basket-ball", ["Basket", "NBA", "Euroligue", "Pro A"]),
    ("Handball", ["Handball"]),
    ("Moto", ["Moto", "MotoGP"]),
]

LEAGUES = ["Ligue 1", "Ligue 2", "Premier League", "La Liga", "Bundesliga", "Serie A",
           "Champions League", "Ligue Europa", "Top 14", "Pro D2", "NBA", "Euroligue",
           "Pro A", "Tour de France", "Formule 1", "NFL", "Starligue", "ATP", "WTA"]

# Programme de secours (utilisé uniquement si le scraping échoue)
FALLBACK = {
    "Canal+ Sport": [
        {"time": "20h45", "sport": "Football", "competition": "Ligue 1", "match": "PSG – Marseille", "is_live": False},
        {"time": "21h05", "sport": "Rugby", "competition": "Top 14", "match": "Toulouse – La Rochelle", "is_live": False},
    ],
    "beIN SPORTS 1": [
        {"time": "18h30", "sport": "Football", "competition": "Premier League", "match": "Liverpool – Manchester City", "is_live": False},
        {"time": "21h00", "sport": "Football", "competition": "La Liga", "match": "Real Madrid – Barcelone", "is_live": False},
    ],
    "L'Équipe": [
        {"time": "14h30", "sport": "Tennis", "competition": "ATP", "match": "Demi-finale simple messieurs", "is_live": False},
        {"time": "20h00", "sport": "Rugby", "competition": "Top 14", "match": "Racing 92 – Stade Français", "is_live": False},
    ],
    "Eurosport 1": [
        {"time": "15h00", "sport": "Cyclisme", "competition": "Tour de Lombardie", "match": "Course en ligne", "is_live": False},
        {"time": "19h00", "sport": "Tennis", "competition": "WTA", "match": "Finale dames", "is_live": False},
    ],
    "RMC Sport 1": [
        {"time": "21h00", "sport": "Football", "competition": "Champions League", "match": "Bayern Munich – Arsenal", "is_live": False},
    ],
    "France 2": [
        {"time": "21h10", "sport": "Rugby", "competition": "Top 14", "match": "Clermont – Toulon", "is_live": False},
    ],
}


def time_key(t):
    m = re.match(r"(\d{1,2})h(\d{2})", t)
    return (int(m.group(1)), int(m.group(2))) if m else (99, 99)


def detect_sport(text):
    low = text.lower()
    for sport, keywords in SPORT_RULES:
        for kw in keywords:
            if kw.lower() in low:
                return sport
    return "Multisports"


def detect_competition(text):
    low = text.lower()
    for league in LEAGUES:
        if league.lower() in low:
            return league
    return ""


def detect_channels(text):
    found = []
    for ch in KNOWN_CHANNELS:
        if ch in text and ch not in found:
            found.append(ch)
    # Garde uniquement les noms les plus précis ("Canal+ Sport" au lieu de "Canal+")
    cleaned = [ch for ch in found
               if not any(o != ch and o.startswith(ch) and len(o) > len(ch) for o in found)]
    return cleaned


def extract_programs(soup):
    programs = []
    seen = set()
    for node in soup.find_all(string=TIME_RE):
        el = node.parent
        if el is None:
            continue
        # Remonte l'arbre HTML pour isoler la "carte" du programme
        block = el
        for _ in range(6):
            parent = block.parent
            if parent is None:
                break
            t = parent.get_text(" ", strip=True)
            if len(t) > 600:
                break
            block = parent
            if len(t) >= 60:
                break
        text = block.get_text(" ", strip=True)
        if "Sans diffusion TV" in text or "Aucune diffusion TV" in text:
            continue
        channels = detect_channels(text)
        if not channels:
            continue
        title = ""
        for tag in block.find_all(["h1", "h2", "h3", "h4"]):
            t = tag.get_text(strip=True)
            if t and len(t) > 3:
                title = t
                break
        if not title:
            for tag in block.find_all(["strong", "b"]):
                t = tag.get_text(strip=True)
                if t and len(t) > 3:
                    title = t
                    break
        if not title:
            continue
        time_str = node.strip()
        if (time_str, title) in seen:
            continue
        seen.add((time_str, title))
        programs.append({
            "time": time_str,
            "sport": detect_sport(text),
            "competition": detect_competition(text),
            "match": title,
            "is_live": "Direct" in text,
            "channels": channels,
        })
    return programs


def group_by_channel(programs):
    by_channel = {}
    today = datetime.now().strftime("%Y-%m-%d")
    for p in programs:
        entry = {
            "time": p["time"], "sport": p["sport"], "competition": p["competition"],
            "match": p["match"], "is_live": p["is_live"], "date": today,
        }
        for ch in p["channels"]:
            by_channel.setdefault(ch, [])
            if entry not in by_channel[ch]:
                by_channel[ch].append(entry)
    for ch in by_channel:
        by_channel[ch].sort(key=lambda x: time_key(x["time"]))
    return by_channel


def main():
    os.makedirs("data", exist_ok=True)
    programs = []
    try:
        r = requests.get(URL, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        programs = extract_programs(soup)
        print(f"✅ Scraping tv-sports.fr OK : {len(programs)} programmes avec chaîne TV")
    except Exception as e:
        print(f"❌ Erreur scraping : {e}")

    if programs:
        channels = group_by_channel(programs)
        source = "tv-sports.fr"
    else:
        print("⚠️ Aucun programme scrapé → programme de secours utilisé")
        channels = FALLBACK
        source = "donnees-de-secours"

    for ch in channels:
        channels[ch].sort(key=lambda x: time_key(x["time"]))

    total = sum(len(v) for v in channels.values())
    output = {
        "updated_at": datetime.now().isoformat(),
        "source": source,
        "total_matches": total,
        "total_channels": len(channels),
        "channels": channels,
    }
    with open("data/schedule.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"💾 data/schedule.json : {total} matchs / {len(channels)} chaînes (source : {source})")


if __name__ == "__main__":
    main()
