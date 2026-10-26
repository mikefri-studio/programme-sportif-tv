import os
import re
import json
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

NB_JOURS_TVSPORTS = 1
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

# 🎨 LOGOS DES CHAÎNES (28 chaînes au total)
CHANNEL_LOGOS = {
    # === CANAL+ (12 chaînes) ===
    "Canal+": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/canal-plus-fr.png",
    "Canal+ Sport": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/canal-plus-sport-fr.png",
    "Canal+ Sport 360": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/canal-plus-sport-360-fr.png",
    "Canal+ Foot": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/canal-plus-foot-fr.png",
    "Canal+ Live": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/canal-plus-live-fr.png",
    "Canal+ Live 1": "https://raw.githubusercontent.com/mikefri/Teslatv01/main/logo/Canal+_Live_1.webp",
    "Canal+ Live 2": "https://raw.githubusercontent.com/mikefri/Teslatv01/main/logo/Canal+_Live_2.webp",
    "Canal+ Live 3": "https://raw.githubusercontent.com/mikefri/Teslatv01/main/logo/Canal+_Live_3.webp",
    "Canal+ Live 4": "https://raw.githubusercontent.com/mikefri/Teslatv01/main/logo/Canal+_Live_4.webp",
    "Canal+ Live 5": "https://raw.githubusercontent.com/mikefri/Teslatv01/main/logo/Canal+_Live_5.webp",
    "Canal+ Live 6": "https://raw.githubusercontent.com/mikefri/Teslatv01/main/logo/Canal+_Live_6.webp",
    "Canal+ Live 7": "https://raw.githubusercontent.com/mikefri/Teslatv01/main/logo/Canal+_Live_7.webp",
    "Canal+ Live 8": "https://raw.githubusercontent.com/mikefri/Teslatv01/main/logo/Canal+_Live_8.webp",
    "Canal+ Première League": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/canal-plus-premiere-league-fr.png",
    
    # === beIN SPORTS (10 chaînes) ===
    "beIN SPORTS": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/bein-sports-fr.png",
    "beIN SPORTS 1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/bein-sports-1-fr.png",
    "beIN SPORTS 2": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/bein-sports-2-fr.png",
    "beIN SPORTS 3": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/bein-sports-3-fr.png",
    # ✨ NOUVEAU : beIN SPORTS 4 à 10 (MAX en réalité)
    "beIN SPORTS 4": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/bein-sports-max-4-fr.png",
    "beIN SPORTS 5": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/bein-sports-max-5-fr.png",
    "beIN SPORTS 6": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/bein-sports-max-6-fr.png",
    "beIN SPORTS 7": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/bein-sports-max-7-fr.png",
    "beIN SPORTS 8": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/bein-sports-max-8-fr.png",
    "beIN SPORTS 9": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/bein-sports-max-9-fr.png",
    "beIN SPORTS 10": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/bein-sports-max-10-fr.png",
    "beIN SPORTS MAX": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/bein-sports-max-fr.png",
    "beIN SPORTS MAX 4": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/bein-sports-max-4-fr.png",
    "beIN SPORTS MAX 5": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/bein-sports-max-5-fr.png",
    
    # === EUROSport (3 chaînes) ===
    "Eurosport": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/eurosport-fr.png",
    "Eurosport 1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/eurosport-1-fr.png",
    "Eurosport 2": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/eurosport-2-fr.png",
    
    # === RMC SPORT (2 chaînes) ===
    "RMC Sport": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/rmc-sport-fr.png",
    "RMC Sport 1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/rmc-sport-1-fr.png",
    
    # === FRANCE TV (3 chaînes) ===
    "France 2": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/france-2-fr.png",
    "France 3": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/france-3-fr.png",
    "France 4": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/france-4-fr.png",
    
    # ✨ NOUVEAU : TF1
    "TF1": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/tf1-fr.png",
    
    # === AUTRES CHAÎNES SPORTIVES ===
    "L'Équipe": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/lequipe-fr.png",
    "L'Equipe": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/lequipe-fr.png",
    "DAZN": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/dazn-fr.png",
    "Ligue 1+": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/ligue-1-plus-fr.png",
    "Sport en France": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/sport-en-france-fr.png",
    "Automoto": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/automoto-la-chaine-fr.png",
    "Equidia": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/equidia-fr.png",
    "MGG TV": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/mgg-tv-fr.png",
    "ABXplore": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/abxplore-fr.png",
    "Golf+": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/golf-plus-fr.png",
    "Infosport+": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/infosport-plus-fr.png",
    "TV5MONDE": "https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/france/tv5-monde-fr.png",
}

KNOWN_CHANNELS = list(CHANNEL_LOGOS.keys())

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

# ✨ NOUVEAU : Règles TV pour les chaînes supplémentaires
TV_RIGHTS = [
    ("ligue 1", ["Ligue 1+", "Canal+ Foot"]),
    ("ligue 2", ["beIN SPORTS 1", "beIN SPORTS 2"]),
    ("premier league", ["Canal+ Sport", "Canal+ Foot"]),
    ("la liga", ["beIN SPORTS 1", "beIN SPORTS 2"]),
    ("bundesliga", ["beIN SPORTS MAX 4", "beIN SPORTS 4"]),
    ("serie a", ["beIN SPORTS 3", "beIN SPORTS 5"]),
    ("champions league", ["Canal+ Sport", "Canal+ Foot", "RMC Sport 1"]),
    ("ligue europa", ["RMC Sport 1"]),
    ("conference league", ["Canal+ Foot"]),
    ("top 14", ["Canal+ Sport"]),
    ("pro d2", ["Canal+ Sport"]),
    ("nba", ["beIN SPORTS 3", "beIN SPORTS 6"]),
    ("euroligue", ["Eurosport 2"]),
    ("atp", ["Eurosport 1"]),
    ("wta", ["Eurosport 1"]),
    ("roland-garros", ["Eurosport 1", "France 2"]),
    ("tour de france", ["France 2", "Eurosport 1"]),
    ("giro", ["Eurosport 1"]),
    ("vuelta", ["Eurosport 1"]),
    ("formule 1", ["Canal+ Sport 360", "Automoto"]),
    ("f1", ["Canal+ Sport 360", "Automoto"]),
    ("nfl", ["beIN SPORTS 1", "beIN SPORTS 7"]),
    ("coupe de france", ["France 2", "TF1", "beIN SPORTS 1"]),
    ("equipe de france", ["TF1", "France 2", "beIN SPORTS 1"]),
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
    """✅ Détection stricte des chaînes avec word boundaries"""
    found = []
    # Trie par longueur décroissante pour prioriser les chaînes les plus spécifiques
    sorted_channels = sorted(KNOWN_CHANNELS, key=len, reverse=True)
    
    for ch in sorted_channels:
        pattern = r'\b' + re.escape(ch) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            found.append(ch)
    
    # Garde uniquement les chaînes les plus précises (évite les doublons comme "Canal+" et "Canal+ Sport")
    result = []
    for ch in found:
        is_subset = False
        for other in found:
            if other != ch and other.startswith(ch) and len(other) > len(ch):
                is_subset = True
                break
        if not is_subset and ch not in result:
            result.append(ch)
    
    return result


def scraperapi_fetch(url):
    api_key = os.environ.get("SCRAPERAPI_KEY")
    if not api_key:
        print("  ❌ SCRAPERAPI_KEY non définie")
        return None
    try:
        params = {"api_key": api_key, "url": url, "premium": "true", "country_code": "fr"}
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
    """✅ Parsing strict avec validation"""
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
        
        # Validation : ignore les blocs trop courts
        if len(text) < 30:
            continue
        if "Sans diffusion TV" in text or "Aucune diffusion TV" in text:
            continue
        
        sport = detect_sport(text)
        if sport == "Multisports" and not any(kw in text.lower() for kw in ["sport", "match", "contre", "vs"]):
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
                if t and len(t) > 3 and ("–" in t or " vs " in t.lower() or "contre" in t.lower()):
                    title = t
                    break
        
        if not title or len(title) < 5:
            continue
        if not ("–" in title or " vs " in title.lower() or "contre" in title.lower()):
            continue
        
        if (date_iso, node.strip(), title) in seen:
            continue
        
        seen.add((date_iso, node.strip(), title))
        
        programs.append({
            "time": node.strip(),
            "sport": sport,
            "competition": detect_competition(text),
            "match": title,
            "is_live": "Direct" in text or "LIVE" in text,
            "channels": channels,
            "date": date_iso,
            "source": "tv-sports.fr"
        })
    
    return programs


def scrape_tvsports():
    """✅ Parse chaque page UNE SEULE fois avec la date du jour"""
    programs = []
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"  📅 Scraping tv-sports.fr (programme du jour)...")
    
    for url in URLS_TVSPORTS:
        html = scraperapi_fetch(url)
        if not html:
            continue
        found = parse_tvsports_html(html, today)
        programs += found
        print(f"     + {len(found)} programmes depuis {url}")
    
    print(f"     ✅ Total tv-sports.fr : {len(programs)} programmes")
    return programs


def scrape_pro_d2_scores():
    """Scrape les scores Pro D2"""
    url = "https://tv-sports.fr/rugby/pro-d2/scores"
    scores = []
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        html = scraperapi_fetch(url)
        if not html:
            print("  ❌ Impossible de scraper les scores Pro D2")
            return []

        soup = BeautifulSoup(html, "html.parser")
        match_cards = soup.find_all(['div', 'article'], class_=lambda x: x and any(kw in x.lower() for kw in ['match', 'game', 'score', 'event']))
        print(f"  📊 Analyse de {len(match_cards)} éléments pour les scores Pro D2...")

        for card in match_cards:
            try:
                teams = []
                logos = []

                team_elems = card.find_all(['div', 'span', 'a'], class_=lambda x: x and 'team' in x.lower())
                for team in team_elems[:2]:
                    name = team.get_text(strip=True)
                    if name and len(name) > 2:
                        teams.append(name)

                logo_elems = card.find_all('img')
                for img in logo_elems[:2]:
                    src = img.get('src', '') or img.get('data-src', '')
                    if src and ('logo' in src.lower() or 'badge' in src.lower() or 'team' in src.lower() or 'club' in src.lower()):
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = 'https://tv-sports.fr' + src
                        logos.append(src)

                score_elem = card.find(['div', 'span'], class_=lambda x: x and 'score' in x.lower())
                score_text = score_elem.get_text(strip=True) if score_elem else ""

                status_elem = card.find(['div', 'span'], class_=lambda x: x and ('status' in x.lower() or 'live' in x.lower() or 'time' in x.lower()))
                status = status_elem.get_text(strip=True).lower() if status_elem else ""
                is_live = "direct" in status or "live" in status or "1ère" in status or "2ème" in status or "mi-temps" in status

                time_elem = card.find(['div', 'span', 'time'], class_=lambda x: x and 'time' in x.lower())
                time_str = time_elem.get_text(strip=True) if time_elem else ""
                if not time_str or not re.match(r"\d{1,2}h\d{2}", time_str):
                    time_str = "TBD"

                if len(teams) >= 2:
                    scores.append({
                        "time": time_str,
                        "sport": "Rugby",
                        "competition": "Pro D2",
                        "match": f"{teams[0]} – {teams[1]}",
                        "is_live": is_live,
                        "channels": ["Canal+ Sport"],
                        "date": today,
                        "home_team": teams[0],
                        "away_team": teams[1],
                        "home_logo": logos[0] if len(logos) > 0 else "",
                        "away_logo": logos[1] if len(logos) > 1 else "",
                        "score": score_text,
                        "source": "tv-sports.fr/scores"
                    })
            except Exception:
                continue

        print(f"  ✅ {len(scores)} scores Pro D2 extraits")
        return scores

    except Exception as e:
        print(f"  ❌ Erreur scraping scores Pro D2: {e}")
        return []


def fetch_thesportsdb(date_iso):
    """✅ N'utilise QUE les chaînes fournies par l'API"""
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
            
            tv = ev.get("strTVStation")
            if not tv or tv.lower() == "null" or tv.strip() == "":
                continue
            
            channels = [c.strip() for c in tv.split(",") if c.strip() and c.strip() in KNOWN_CHANNELS]
            if not channels:
                continue
            
            t = ev.get("strTime") or ""
            time_str = f"{t[:2]}h{t[3:5]}" if re.match(r"\d{2}:\d{2}", t) else "TBD"
            status = ev.get("strStatus") or ""
            is_live = "Live" in status or "Progress" in status
            
            programs.append({
                "time": time_str,
                "sport": sport_fr,
                "competition": competition,
                "match": title,
                "is_live": is_live,
                "channels": channels,
                "date": date_iso,
                "source": "TheSportsDB"
            })
        
        print(f"  ✅ TheSportsDB {date_iso} : {len(programs)} programmes (avec chaînes TV confirmées)")
    except Exception as e:
        print(f"  ❌ TheSportsDB {date_iso} : {e}")
    return programs


def group_by_channel(programs):
    by_channel = {}
    for p in programs:
        entry = {
            "time": p.get("time", "TBD"),
            "sport": p.get("sport", "Multisports"),
            "competition": p.get("competition", ""),
            "match": p.get("match", ""),
            "is_live": p.get("is_live", False),
            "date": p.get("date", ""),
        }
        for key in ["home_team", "away_team", "home_logo", "away_logo", "score", "source"]:
            if key in p:
                entry[key] = p[key]

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
    print(f"📺 {len(CHANNEL_LOGOS)} chaînes configurées")
    print("=" * 60)

    print("\n📡 Phase 1 : tv-sports.fr (via ScraperAPI)")
    programs = scrape_tvsports()

    print("\n📊 Phase 2 : Scores Pro D2")
    pro_d2_scores = scrape_pro_d2_scores()
    programs.extend(pro_d2_scores)

    print("\n📡 Phase 3 : TheSportsDB (complément)")
    for offset in range(NB_JOURS_TOTAL):
        d = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")
        existing = len([p for p in programs if p["date"] == d])
        if existing < 3:
            print(f"  ⚠️  {d} : seulement {existing} programmes → complément TheSportsDB")
            programs += fetch_thesportsdb(d)

    if not programs:
        print("\n⚠️ Aucune donnée trouvée → fichier vide")
        output = {
            "updated_at": datetime.now().isoformat(),
            "source": "aucune donnée disponible",
            "total_matches": 0,
            "total_channels": 0,
            "channels": {},
        }
        with open("data/schedule.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print("💾 data/schedule.json (vide)")
        return

    uniq, seen = [], set()
    for p in programs:
        key = (p["date"], p["time"], p["match"], tuple(sorted(p["channels"])))
        if key not in seen:
            seen.add(key)
            uniq.append(p)

    uniq = [m for m in uniq if m.get("date") and m["date"] >= today_iso]

    channels = group_by_channel(uniq)

    channels_with_logos = {}
    for ch, matches in channels.items():
        channels_with_logos[ch] = {
            "logo": CHANNEL_LOGOS.get(ch, ""),
            "matches": matches,
        }

    total = sum(len(v["matches"]) for v in channels_with_logos.values())
    dates = sorted({m["date"] for v in channels_with_logos.values() for m in v["matches"]})

    sources = set()
    for v in channels_with_logos.values():
        for m in v["matches"]:
            if "source" in m:
                sources.add(m["source"])
    
    source = " + ".join(sorted(sources)) if sources else "inconnue"

    output = {
        "updated_at": datetime.now().isoformat(),
        "source": source,
        "total_matches": total,
        "total_channels": len(channels_with_logos),
        "channels": channels_with_logos,
    }

    with open("data/schedule.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"✅ Terminé : {total} programmes / {len(channels_with_logos)} chaînes / {len(dates)} dates")
    print(f"   Sources : {source}")
    print(f"   Dates : {', '.join(dates)}")
    print(f"   Chaînes détectées : {', '.join(sorted(channels_with_logos.keys()))}")
    print(f"💾 data/schedule.json")


if __name__ == "__main__":
    main()
