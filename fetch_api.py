import os
import re
import json
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

NB_JOURS_TVSPORTS = 7  # ✅ Scraper tv-sports.fr sur 7 jours (au lieu de 2)
NB_JOURS_TOTAL = 7

URLS_TVSPORTS = [
    "https://tv-sports.fr/",
    "https://tv-sports.fr/football/",
    "https://tv-sports.fr/rugby/",
    "https://tv-sports.fr/tennis/",
    "https://tv-sports.fr/cyclisme/",
    "https://tv-sports.fr/basket/",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
}
TIME_RE = re.compile(r"^\d{1,2}h\d{2}$")

KNOWN_CHANNELS = [
    "Canal+ Sport 360", "Canal+ Première League", "Canal+ Sport", "Canal+ Foot", "Canal+ Live", "Canal+",
    "beIN SPORTS MAX", "beIN SPORTS", "L'Équipe", "L'Equipe",
    "Eurosport 1", "Eurosport 2", "Eurosport", "RMC Sport",
    "France 2", "France 3", "France 4", "DAZN", "Ligue 1+", "Sport en France",
    "Automoto", "Equidia", "MGG TV", "ABXplore", "Golf+", "Infosport+", "TV5MONDE",
]

SPORT_RULES = [
    ("Formule 1", ["Formule 1", "F1"]),
    ("Football", ["Foot", "Football", "Ligue 1", "Premier League", "Liga", "Bundesliga", "Serie A", "Champions League"]),
    ("Rugby", ["Rugby", "Top 14", "Pro D2"]),
    ("Tennis", ["Tennis", "ATP", "WTA"]),
    ("Cyclisme", ["Cyclisme", "Tour de France", "Vuelta", "Giro"]),
    ("Basket-ball", ["Basket", "NBA", "Euroligue", "Pro A"]),
    ("Handball", ["Handball"]),
    ("Moto", ["Moto", "MotoGP"]),
]

LEAGUES = ["Ligue 1", "Ligue 2", "Premier League", "La Liga", "Bundesliga", "Serie A",
           "Champions League", "Ligue Europa", "Top 14", "Pro D2", "NBA", "Euroligue",
           "Pro A", "Tour de France", "Formule 1", "NFL", "Starligue", "ATP", "WTA"]

TV_RIGHTS = [
    ("ligue 1", ["Ligue 1+", "Canal+ Foot"]),
    ("ligue 2", ["beIN SPORTS 1"]),
    ("premier league", ["Canal+ Sport", "Canal+ Foot"]),
    ("la liga", ["beIN SPORTS 1"]),
    ("bundesliga", ["beIN SPORTS MAX 4"]),
    ("serie a", ["beIN SPORTS 3"]),
    ("champions league", ["Canal+ Sport", "Canal+ Foot"]),
    ("ligue europa", ["RMC Sport 1"]),
    ("conference league", ["Canal+ Foot"]),
    ("top 14", ["Canal+ Sport"]),
    ("pro d2", ["Canal+ Sport"]),
    ("nba", ["beIN SPORTS 3"]),
    ("euroligue", ["Eurosport 2"]),
    ("atp", ["Eurosport 1"]),
    ("wta", ["Eurosport 1"]),
    ("roland-garros", ["Eurosport 1", "France 2"]),
    ("tour de france", ["France 2", "Eurosport 1"]),
    ("giro", ["Eurosport 1"]),
    ("vuelta", ["Eurosport 1"]),
    ("formule 1", ["Canal+ Sport 360"]),
    ("f1", ["Canal+ Sport 360"]),
    ("nfl", ["beIN SPORTS 1"]),
]

SPORTSDB_MAP = {
    "Soccer": "Football", "Rugby": "Rugby", "Tennis": "Tennis",
    "Cycling": "Cyclisme", "Basketball": "Basket-ball",
    "Motorsport": "Formule 1", "Handball": "Handball", "Moto": "Moto",
}


def time_key(t):
    m = re.match(r"(\d{1,2})h(\d{2})", str(t))
    return (int(m.group(1)), int(m.group(2))) if m else (99, 99)


def detect_sport(text):
    low = text.lower()
    for sport, kws in SPORT_RULES:
        for kw in kws:
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
    found = [ch for ch in KNOWN_CHANNELS if ch in text]
    return [ch for ch in found
            if not any(o != ch and o.startswith(ch) and len(o) > len(ch) for o in found)]


def channels_from_rights(text):
    low = text.lower()
    for kw, chans in TV_RIGHTS:
        if kw in low:
            return chans
    return []


def scraperapi_fetch(url):
    api_key = os.environ.get("SCRAPERAPI_KEY")
    if not api_key:
        print("  ❌ SCRAPERAPI_KEY non définie")
        return None
    try:
        params = {
            "api_key": api_key,
            "url": url,
            "premium": "true",
            "country_code": "fr",
        }
        r = requests.get("https://api.scraperapi.com/", params=params, timeout=45)
        r.raise_for_status()
        html = r.text
        if "Verify you are human" in html or "challenge-platform" in html:
            print(f"  ⚠️  Cloudflare encore actif sur {url}")
            return None
        return html
    except Exception as e:
        print(f"  ❌ Erreur ScraperAPI sur {url} : {e}")
        return None


def parse_tvsports_html(html, date_iso):
    soup = BeautifulSoup(html, "html.parser")
    programs = []
    seen = set()

    for node in soup.find_all(string=TIME_RE):
        el = node.parent
        if el is None:
            continue
        block = el
        for _ in range(6):
            parent = block.parent
            if parent is None:
                break
            t = parent.get_text(" ", strip=True)
            if len(t) > 800:
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
        if not title or (date_iso, node.strip(), title) in seen:
            continue
        seen.add((date_iso, node.strip(), title))
        programs.append({
            "time": node.strip(), "sport": detect_sport(text),
            "competition": detect_competition(text), "match": title,
            "is_live": "Direct" in text or "LIVE" in text,
            "channels": channels, "date": date_iso,
        })
    return programs


def scrape_tvsports():
    """Scrape tv-sports.fr sur NB_JOURS_TVSPORTS jours."""
    programs = []
    today = datetime.now().strftime("%Y-%m-%d")
    
    # On scrape les URLs une seule fois (elles contiennent plusieurs jours)
    print(f"  📅 Scraping tv-sports.fr sur {NB_JOURS_TVSPORTS} jours...")
    for url in URLS_TVSPORTS:
        html = scraperapi_fetch(url)
        if not html:
            continue
        # Parse pour chaque jour
        for offset in range(NB_JOURS_TVSPORTS):
            d = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")
            found = parse_tvsports_html(html, d)
            programs += found
        print(f"     + {len([p for p in programs if p['date'] >= today])} programmes depuis {url}")
    
    total = len([p for p in programs if p["date"] >= today])
    print(f"     ✅ Total tv-sports.fr : {total} programmes")
    return programs


def fetch_thesportsdb(date_iso):
    programs = []
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/123/eventsday.php?d={date_iso}"
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        events = r.json().get("events") or []
        for ev in events:
            sport_fr = SPORTSDB_MAP.get(ev.get("strSport"))
            if not sport_fr:
                continue
            title = ev.get("strEvent") or ""
            competition = ev.get("strLeague") or ""
            if not title:
                continue
            haystack = f"{competition} {title}"
            tv = ev.get("strTVStation")
            if tv and tv.lower() != "null":
                channels = [c.strip() for c in tv.split(",") if c.strip()]
            else:
                channels = channels_from_rights(haystack)
            if not channels:
                continue
            t = ev.get("strTime") or ""
            time_str = f"{t[:2]}h{t[3:5]}" if re.match(r"\d{2}:\d{2}", t) else "TBD"
            status = ev.get("strStatus") or ""
            is_live = "Live" in status or "Progress" in status
            programs.append({
                "time": time_str, "sport": sport_fr, "competition": competition,
                "match": title, "is_live": is_live, "channels": channels, "date": date_iso,
            })
        print(f"  ✅ TheSportsDB {date_iso} : {len(programs)} programmes")
    except Exception as e:
        print(f"  ❌ TheSportsDB {date_iso} : {e}")
    return programs


def group_by_channel(programs):
    by_channel = {}
    for p in programs:
        entry = {k: p[k] for k in ("time", "sport", "competition", "match", "is_live", "date")}
        for ch in p["channels"]:
            by_channel.setdefault(ch, [])
            if entry not in by_channel[ch]:
                by_channel[ch].append(entry)
    for ch in by_channel:
        by_channel[ch].sort(key=lambda m: (m.get("date", ""), time_key(m["time"])))
    return by_channel


def main():
    os.makedirs("data", exist_ok=True)
    today_iso = datetime.now().strftime("%Y-%m-%d")

    print(f"🚀 Construction du programme sportif sur {NB_JOURS_TOTAL} jours...")
    print("=" * 60)

    # 1. tv-sports.fr sur 7 jours via ScraperAPI
    print("\n📡 Phase 1 : tv-sports.fr (via ScraperAPI)")
    programs = scrape_tvsports()

    # 2. Complément TheSportsDB pour les jours sans données
    print("\n📡 Phase 2 : TheSportsDB (complément)")
    for offset in range(NB_JOURS_TOTAL):
        d = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")
        existing = len([p for p in programs if p["date"] == d])
        if existing < 5:  # Si moins de 5 programmes, on complète
            print(f"  ⚠️  {d} : seulement {existing} programmes → complément TheSportsDB")
            programs += fetch_thesportsdb(d)

    if not programs:
        print("\n️ Aucune donnée → programme de secours")
        for offset in range(NB_JOURS_TOTAL):
            d = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")
            programs += [
                {"time": "20h45", "sport": "Football", "competition": "Ligue 1", "match": "PSG – Marseille", "is_live": False, "channels": ["Canal+ Sport"], "date": d},
                {"time": "21h00", "sport": "Football", "competition": "Premier League", "match": "Liverpool – Manchester City", "is_live": False, "channels": ["beIN SPORTS 1"], "date": d},
                {"time": "21h05", "sport": "Rugby", "competition": "Top 14", "match": "Toulouse – La Rochelle", "is_live": False, "channels": ["Canal+ Sport"], "date": d},
            ]

    uniq, seen = [], set()
    for p in programs:
        key = (p["date"], p["time"], p["match"], tuple(sorted(p["channels"])))
        if key not in seen:
            seen.add(key)
            uniq.append(p)

    uniq = [m for m in uniq if m.get("date") and m["date"] >= today_iso]

    channels = group_by_channel(uniq)
    total = sum(len(v) for v in channels.values())
    dates = sorted({m["date"] for ms in channels.values() for m in ms})

    source_parts = []
    if any(m.get("date") >= today_iso for ms in channels.values() for m in ms):
        source_parts.append("tv-sports.fr")
    source = " + ".join(source_parts) if source_parts else "secours"

    output = {
        "updated_at": datetime.now().isoformat(),
        "source": source,
        "total_matches": total,
        "total_channels": len(channels),
        "channels": channels,
    }

    with open("data/schedule.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"✅ Terminé : {total} programmes / {len(channels)} chaînes / {len(dates)} dates")
    print(f"   Sources : {source}")
    print(f"   Dates : {', '.join(dates)}")
    print(f"💾 data/schedule.json")


if __name__ == "__main__":
    main()
