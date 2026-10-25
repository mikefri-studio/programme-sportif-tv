import os
import json
import requests
from datetime import datetime, timedelta

def fetch_sports_data():
    # 1. Récupérer la clé API depuis les secrets GitHub (sécurisé)
    api_key = os.environ.get('API_SPORTS_KEY')
    if not api_key:
        print("❌ Erreur: La variable d'environnement API_SPORTS_KEY n'est pas définie.")
        return

    # 2. Définir la date (aujourd'hui et demain pour avoir les matchs à venir)
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 3. Appeler l'API (Endpoint des matchs du jour)
    url = f"https://v3.football.api-sports.io/fixtures?date={today}"
    headers = {
        'x-apisports-key': api_key
    }
    
    print(f"📡 Interrogation de l'API pour la date : {today}...")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('errors'):
            print(f"❌ Erreur API : {data['errors']}")
            return

        fixtures = data.get('response', [])
        print(f"✅ {len(fixtures)} matchs récupérés. Filtrage des diffusions TV...")

        # 4. Traiter et regrouper les données par chaîne TV
        schedule_by_channel = {}

        for fixture in fixtures:
            # Vérifier si l'API fournit des informations TV pour ce match
            tv_stations = fixture.get('tv', [])
            
            if tv_stations: # Si la liste n'est pas vide
                # Informations du match
                home_team = fixture['teams']['home']['name']
                away_team = fixture['teams']['away']['name']
                league = fixture['league']['name']
                sport = "Football" # Cet endpoint est spécifique au foot, on peut l'adapter
                
                # Heure du match (formatage en heure française)
                match_time = fixture['fixture']['date']
                dt = datetime.fromisoformat(match_time.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M')
                
                match_data = {
                    "time": time_str,
                    "sport": sport,
                    "competition": league,
                    "match": f"{home_team} – {away_team}",
                    "is_live": fixture['fixture']['status']['short'] == '1H' or fixture['fixture']['status']['short'] == '2H'
                }

                # Ajouter à chaque chaîne qui diffuse ce match
                for channel in tv_stations:
                    channel_name = channel.strip()
                    if channel_name not in schedule_by_channel:
                        schedule_by_channel[channel_name] = []
                    
                    # Éviter les doublons si un match est listé 2 fois pour la même chaîne
                    if match_data not in schedule_by_channel[channel_name]:
                        schedule_by_channel[channel_name].append(match_data)

        # 5. Trier les matchs par heure pour chaque chaîne
        for channel in schedule_by_channel:
            schedule_by_channel[channel].sort(key=lambda x: x["time"])

        # 6. Sauvegarder le résultat
        os.makedirs("data", exist_ok=True)
        output = {
            "updated_at": datetime.now().isoformat(),
            "channels": schedule_by_channel
        }
        
        with open("data/schedule.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Succès ! {len(schedule_by_channel)} chaînes avec des programmes enregistrées dans data/schedule.json")

    except Exception as e:
        print(f"❌ Erreur lors de la requête API : {e}")

if __name__ == "__main__":
    fetch_sports_data()
