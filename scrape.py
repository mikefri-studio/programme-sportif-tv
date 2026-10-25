import os
import json
import requests
from datetime import datetime, timedelta

# Ta seule et unique clé API (récupérée depuis les secrets GitHub)
API_KEY = os.environ.get('API_SPORTS_KEY')

# Configuration des endpoints (tous utilisent la même clé)
SPORTS_CONFIG = {
    "football": {
        "url": "https://v3.football.api-sports.io/fixtures",
        "name": "Football",
    },
    "rugby": {
        "url": "https://v1.rugby.api-sports.io/games",
        "name": "Rugby",
    },
    "tennis": {
        "url": "https://v1.tennis.api-sports.io/matches",
        "name": "Tennis",
    },
    "cycling": {
        "url": "https://v1.cycling.api-sports.io/races",
        "name": "Cyclisme",
    },
}

def fetch_sport(sport_key, config, date_str):
    if not API_KEY:
        print(f"  ⚠️ {config['name']}: Clé API manquante dans les secrets GitHub")
        return []

    url = f"{config['url']}?date={date_str}"
    headers = {"x-apisports-key": API_KEY} # Même clé pour tout !

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("errors"):
            # Si l'erreur dit "Not subscribed", c'est que tu n'as pas activé le plan gratuit pour ce sport
            print(f"  ❌ {config['name']}: Erreur → {data['errors']}")
            return []

        items = data.get("response", [])
        print(f"  ✅ {config['name']}: {len(items)} événements trouvés")

        matches_with_tv = []
        for item in items:
            tv_stations = item.get("tv", [])
            if not tv_stations:
                continue # On ignore les matchs sans diffusion TV

            # Extraction des données selon le sport
            if sport_key == "football":
                match_title = f"{item['teams']['home']['name']} – {item['teams']['away']['name']}"
                league = item["league"]["name"]
                match_time = item["fixture"]["date"]
                status = item["fixture"]["status"]["short"]
            elif sport_key == "rugby":
                match_title = f"{item['teams']['home']['name']} – {item['teams']['away']['name']}"
                league = item["league"]["name"]
                match_time = item["game"]["date"]
                status = item["game"]["status"]["short"]
            elif sport_key == "tennis":
                match_title = f"{item['players'][0]['name']} – {item['players'][1]['name']}"
                league = item["tournament"]["name"]
                match_time = item["date"]
                status = item.get("status", {}).get("short", "NS")
            elif sport_key == "cycling":
                match_title = item["race"]["name"]
                league = item.get("country", {}).get("name", "International")
                match_time = item["date"]
                status = item.get("status", {}).get("short", "NS")
            else:
                continue

            # Formatage de l'heure
            try:
                dt = datetime.fromisoformat(match_time.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M")
            except Exception:
                time_str = "TBD"

            is_live = status in ["1H", "2H", "HT", "LIVE", "IP", "1P", "2P", "3P", "4P", "OT"]

            match_data = {
                "time": time_str,
                "sport": config["name"],
                "competition": league,
                "match": match_title,
                "is_live": is_live,
            }

            for channel in tv_stations:
                channel_name = channel.strip()
                if channel_name:
                    matches_with_tv.append((channel_name, match_data))

        return matches_with_tv

    except Exception as e:
        print(f"  ❌ {config['name']}: Erreur de requête → {e}")
        return []


def main():
    os.makedirs("data", exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    dates_to_fetch = [today, tomorrow]

    print(f"🚀 Récupération du programme avec la clé : {API_KEY[:5]}...")
    print("=" * 60)

    schedule_by_channel = {}
    total_matches = 0

    for sport_key, config in SPORTS_CONFIG.items():
        print(f"\n📡 {config['name']}...")
        for date_str in dates_to_fetch:
            matches = fetch_sport(sport_key, config, date_str)
            for channel_name, match_data in matches:
                if channel_name not in schedule_by_channel:
                    schedule_by_channel[channel_name] = []
                if match_data not in schedule_by_channel[channel_name]:
                    schedule_by_channel[channel_name].append(match_data)
                    total_matches += 1

    # Trier les matchs par heure
    for channel in schedule_by_channel:
        schedule_by_channel[channel].sort(key=lambda x: x["time"])

    output = {
        "updated_at": datetime.now().isoformat(),
        "total_matches": total_matches,
        "total_channels": len(schedule_by_channel),
        "channels": schedule_by_channel,
    }

    with open("data/schedule.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"✅ Succès ! {total_matches} matchs sur {len(schedule_by_channel)} chaînes.")

if __name__ == "__main__":
    main()
