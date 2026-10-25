import os
import re
import json
import requests
from datetime import datetime, timedelta

NB_JOURS = 7  # aujourd'hui + 6 jours

SPORTSDB_SPORTS = {
    "Soccer": ("Football", "⚽"),
    "Rugby": ("Rugby", "🏉"),
    "Tennis": ("Tennis", "🎾"),
    "Cycling": ("Cyclisme", "🚴"),
    "Basketball": ("Basket-ball", "🏀"),
    "Motorsport": ("Formule 1", "🏎️"),
    "Handball": ("Handball", "🤾"),
    "Moto": ("Moto", "🏍️"),
    "American Football": ("Football américain", "🏈"),
    "Ice Hockey": ("Hockey", "🏒"),
}

# Droits TV français (appliqués quand TheSportsDB ne donne pas la chaîne)
TV_RIGHTS = [
    ("ligue 1", ["Ligue 1+", "Canal+ Foot"]),
    ("ligue 2", ["beIN SPORTS 1", "beIN SPORTS 2"]),
    ("premier league", ["Canal+ Sport", "Canal+ Foot"]),
    ("la liga", ["beIN SPORTS 1", "beIN SPORTS 2"]),
    ("bundesliga", ["beIN SPORTS MAX 4", "beIN SPORTS MAX 5"]),
    ("serie a", ["beIN SPORTS 3"]),
    ("champions league", ["Canal+ Sport", "Canal+ Foot"]),
    ("europa league", ["RMC Sport 1", "beIN SPORTS 1"]),
    ("conference league", ["Canal+ Foot"]),
    ("top 14", ["Canal+ Sport", "Canal+ Sport 360"]),
    ("pro d2", ["Canal+ Sport"]),
    ("six nations", ["France 2", "France 3"]),
    ("nba", ["beIN SPORTS 3"]),
    ("euroligue", ["Eurosport 2"]),
    ("atp", ["Eurosport 1", "Eurosport 2"]),
    ("wta", ["Eurosport 1", "Eurosport 2"]),
    ("roland-garros", ["Eurosport 1", "France 2"]),
    ("tour de france", ["France 2", "France 3", "Eurosport 1"]),
    ("giro", ["Eurosport 1"]),
    ("vuelta", ["Eurosport 1"]),
    ("formula 1", ["Canal+ Sport 360"]),
    ("formule 1", ["Canal+ Sport 360"]),
    ("f1", ["Canal+ Sport 360"]),
    ("nfl", ["beIN SPORTS 1", "L'Équipe"]),
    ("mlb", ["beIN SPORTS 3"]),
]


def time_key(t):
    m = re.match(r"(\d{1,2})h(\d{2})", str(t))
    return (int(m.group(1)), int(m.group(2))) if m else (99, 99)


def channels_from_rights(text):
    low = text.lower()
    for kw, chans in TV_RIGHTS:
        if kw in low:
            return chans
    return []


def fetch_day(date_iso):
    """Récupère TOUS les sports d'un jour donné via TheSportsDB."""
    programs = []
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/123/eventsday.php?d={date_iso}"
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        events = data.get("events") or []
        
        for ev in events:
            sport_raw = ev.get("strSport") or ""
            if sport_raw not in SPORTSDB_SPORTS:
                continue
            sport_fr, _ = SPORTSDB_SPORTS[sport_raw]
            
            title = ev.get("strEvent") or ""
            competition = ev.get("strLeague") or ""
            if not title:
                continue
                
            # Chaîne : API d'abord, sinon droits TV français
            tv = ev.get("strTVStation")
            if tv and tv.lower() != "null":
                channels = [c.strip() for c in tv.split(",") if c.strip()]
            else:
                channels = channels_from_rights(f"{competition} {title}")
            
            if not channels:
                continue
                
            # Heure au format "14:30:00" → "14h30"
            t = ev.get("strTime") or ""
            if re.match(r"\d{2}:\d{2}", t):
                time_str = f"{t[:2]}h{t[3:5]}"
            else:
                time_str = "TBD"
                
            # Détection du direct
            status = ev.get("strStatus") or ""
            is_live = "Live" in status or "Progress" in status or "In Play" in status
            
            programs.append({
                "time": time_str,
                "sport": sport_fr,
                "competition": competition,
                "match": title,
                "is_live": is_live,
                "channels": channels,
                "date": date_iso,
            })
            
        print(f"  📅 {date_iso} : {len(programs)} programmes")
    except Exception as e:
        print(f"  ❌ Erreur {date_iso} : {e}")
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


def merge_with_existing(new_channels, today_iso, new_dates):
    try:
        with open("data/schedule.json", encoding="utf-8") as f:
            old = json.load(f).get("channels", {})
    except Exception:
        return new_channels
    kept = 0
    for ch, ms in old.items():
        for m in ms:
            d = m.get("date")
            if d and d >= today_iso and d not in new_dates:
                new_channels.setdefault(ch, [])
                if m not in new_channels[ch]:
                    new_channels[ch].append(m)
                    kept += 1
    if kept:
        print(f"  ♻️  {kept} programmes conservés depuis l'ancien JSON")
    return new_channels


def main():
    os.makedirs("data", exist_ok=True)
    today_iso = datetime.now().strftime("%Y-%m-%d")
    
    print(f"🚀 Récupération du programme sportif sur {NB_JOURS} jours (TheSportsDB)...")
    
    all_programs = []
    for offset in range(NB_JOURS):
        d = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")
        all_programs += fetch_day(d)
    
    if not all_programs:
        print("⚠️ Aucune donnée TheSportsDB → programme de secours")
        # Fallback minimal mais multi-jours
        for offset in range(3):
            d = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")
            all_programs += [
                {"time": "20h45", "sport": "Football", "competition": "Ligue 1", "match": "PSG – Marseille", "is_live": False, "channels": ["Canal+ Sport"], "date": d},
                {"time": "21h00", "sport": "Football", "competition": "Premier League", "match": "Liverpool – Manchester City", "is_live": False, "channels": ["beIN SPORTS 1"], "date": d},
                {"time": "21h05", "sport": "Rugby", "competition": "Top 14", "match": "Toulouse – La Rochelle", "is_live": False, "channels": ["Canal+ Sport"], "date": d},
                {"time": "15h00", "sport": "Tennis", "competition": "ATP", "match": "Demi-finale", "is_live": False, "channels": ["Eurosport 1"], "date": d},
                {"time": "16h00", "sport": "Cyclisme", "competition": "Tour", "match": "Étape", "is_live": False, "channels": ["France 2"], "date": d},
            ]
    
    # Dédoublonnage
    uniq, seen = [], set()
    for p in all_programs:
        key = (p["date"], p["time"], p["match"], tuple(sorted(p["channels"])))
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    
    channels = group_by_channel(uniq)
    new_dates = {p["date"] for p in uniq}
    channels = merge_with_existing(channels, today_iso, new_dates)
    
    # Nettoyage du passé
    for ch in list(channels.keys()):
        channels[ch] = [m for m in channels[ch] if not m.get("date") or m["date"] >= today_iso]
        channels[ch].sort(key=lambda m: (m.get("date", ""), time_key(m["time"])))
        if not channels[ch]:
            del channels[ch]
    
    total = sum(len(v) for v in channels.values())
    dates = sorted({m["date"] for ms in channels.values() for m in ms})
    
    output = {
        "updated_at": datetime.now().isoformat(),
        "source": "TheSportsDB + droits TV français",
        "total_matches": total,
        "total_channels": len(channels),
        "dates_covered": len(dates),
        "channels": channels,
    }
    
    with open("data/schedule.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Terminé : {total} programmes / {len(channels)} chaînes / {len(dates)} dates")
    print(f"   Dates : {', '.join(dates)}")
    print(f"💾 Sauvegardé dans data/schedule.json")


if __name__ == "__main__":
    main()
