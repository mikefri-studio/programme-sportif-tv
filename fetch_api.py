import os
import json
import requests
from datetime import datetime, timedelta

def fetch_tvsports():
    os.makedirs("data", exist_ok=True)
    
    # La clé "3" est la clé de test publique gratuite de TheSportsDB.
    # Tu peux la remplacer par ta propre clé gratuite si tu en demandes une.
    API_KEY = os.environ.get("THESPORTSDB_API_KEY", "123")
    
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    dates_to_fetch = [today, tomorrow]
    
    schedule_by_channel = {}
    total_matches = 0
    
    print(f"🚀 Récupération du programme TV via TheSportsDB...")
    print("=" * 60)
    
    for date_str in dates_to_fetch:
        # Endpoint unique qui renvoie TOUS les événements du jour avec potentiellement la TV
        url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventsday.php?d={date_str}"
        
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            events = data.get("events", [])
            if not events:
                print(f"  ⚠️  Aucun événement trouvé pour le {date_str}")
                continue
                
            print(f"  ✅ {len(events)} événements bruts trouvés pour le {date_str}")
            
            for event in events:
                tv_station = event.get("strTVStation")
                
                # On ignore les événements sans chaîne TV renseignée
                if not tv_station or tv_station.strip() == "" or tv_station.lower() == "null":
                    continue
                
                # Une chaîne peut en lister plusieurs (ex: "Canal+, beIN Sports 1")
                channels = [ch.strip() for ch in tv_station.split(",")]
                
                # Traduction des sports en français
                sport_raw = event.get("strSport", "Sport")
                sport_map = {
                    "Soccer": "Football",
                    "Rugby": "Rugby",
                    "Tennis": "Tennis",
                    "Cycling": "Cyclisme",
                    "Motorsport": "Sports Mécaniques",
                    "Basketball": "Basket-ball"
                }
                sport_fr = sport_map.get(sport_raw, sport_raw)
                
                # On filtre pour ne garder que les sports qui t'intéressent
                if sport_fr not in ["Football", "Rugby", "Tennis", "Cyclisme", "Basket-ball", "Sports Mécaniques"]:
                    continue

                match_title = event.get("strEvent", "Match inconnu")
                league = event.get("strLeague", "Compétition inconnue")
                
                # L'heure est au format "20:45:00", on garde juste "20:45"
                time_str = event.get("strTime", "TBD")[:5]  
                
                # Détection basique du direct
                status = event.get("strStatus", "")
                is_live = "Live" in status or "In Play" in status
                
                match_data = {
                    "time": time_str,
                    "sport": sport_fr,
                    "competition": league,
                    "match": match_title,
                    "is_live": is_live,
                    "date": date_str
                }
                
                # Ajouter le match à chaque chaîne concernée
                for channel in channels:
                    if channel not in schedule_by_channel:
                        schedule_by_channel[channel] = []
                    
                    # Éviter les doublons
                    if match_data not in schedule_by_channel[channel]:
                        schedule_by_channel[channel].append(match_data)
                        total_matches += 1
                        
        except Exception as e:
            print(f"  ❌ Erreur lors de la récupération du {date_str} : {e}")

    # Trier les matchs par heure pour chaque chaîne
    for channel in schedule_by_channel:
        schedule_by_channel[channel].sort(key=lambda x: x["time"])

    # Sauvegarder le résultat
    output = {
        "updated_at": datetime.now().isoformat(),
        "total_matches": total_matches,
        "total_channels": len(schedule_by_channel),
        "channels": schedule_by_channel,
    }
    
    with open("data/schedule.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        
    print("\n" + "=" * 60)
    print(f"✅ Succès ! {total_matches} matchs TV sur {len(schedule_by_channel)} chaînes.")
    print("📁 Fichier sauvegardé : data/schedule.json")

if __name__ == "__main__":
    fetch_tvsports()
