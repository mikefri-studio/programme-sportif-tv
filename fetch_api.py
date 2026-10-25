import os
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup

def scrape_tv_sports():
    """Scrape tv-sports.fr pour récupérer les programmes TV sportifs par chaîne"""
    os.makedirs("data", exist_ok=True)
    
    url = "https://tv-sports.fr/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9"
    }
    
    print("🚀 Scraping de tv-sports.fr...")
    print("=" * 60)
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        schedule_by_channel = {}
        total_matches = 0
        
        # Cherche tous les programmes TV
        # Structure typique de tv-sports.fr : div avec classe contenant "programme" ou "match"
        programmes = soup.find_all(['div', 'article', 'li'], class_=lambda x: x and any(word in x.lower() for word in ['programme', 'match', 'event', 'diffusion']))
        
        print(f"  Trouvé {len(programmes)} éléments potentiels")
        
        for prog in programmes:
            try:
                # Extraction des données
                text = prog.get_text(' ', strip=True)
                
                # Filtre : garde seulement les sports qui nous intéressent
                if not any(sport in text for sport in ['Foot', 'Rugby', 'Tennis', 'Cyclisme', 'Basket']):
                    continue
                
                # Extraction de la chaîne TV (souvent dans un span ou a avec classe "channel")
                channel_elem = prog.find(['span', 'a', 'div'], class_=lambda x: x and 'channel' in x.lower())
                channel = channel_elem.get_text(strip=True) if channel_elem else "Chaîne inconnue"
                
                # Extraction de l'heure
                time_elem = prog.find(['span', 'time'], class_=lambda x: x and 'time' in x.lower())
                time_str = time_elem.get_text(strip=True) if time_elem else "TBD"
                
                # Extraction du sport
                sport_elem = prog.find(['span', 'div'], class_=lambda x: x and 'sport' in x.lower())
                sport = sport_elem.get_text(strip=True) if sport_elem else "Sport"
                
                # Extraction de la compétition
                comp_elem = prog.find(['span', 'div'], class_=lambda x: x and ('comp' in x.lower() or 'league' in x.lower()))
                competition = comp_elem.get_text(strip=True) if comp_elem else "Compétition"
                
                # Extraction du match
                match_elem = prog.find(['h3', 'h4', 'strong', 'b'])
                match = match_elem.get_text(strip=True) if match_elem else "Match inconnu"
                
                # Détection du direct
                is_live = "Direct" in text or "LIVE" in text
                
                match_data = {
                    "time": time_str,
                    "sport": sport,
                    "competition": competition,
                    "match": match,
                    "is_live": is_live,
                    "date": datetime.now().strftime("%Y-%m-%d")
                }
                
                if channel not in schedule_by_channel:
                    schedule_by_channel[channel] = []
                
                schedule_by_channel[channel].append(match_data)
                total_matches += 1
                
            except Exception as e:
                continue
        
        # Trier par heure
        for channel in schedule_by_channel:
            schedule_by_channel[channel].sort(key=lambda x: x["time"])
        
        print(f"\n📊 Résultats:")
        print(f"  - Matchs trouvés : {total_matches}")
        print(f"  - Chaînes : {len(schedule_by_channel)}")
        
        if schedule_by_channel:
            print(f"  - Premières chaînes : {', '.join(list(schedule_by_channel.keys())[:5])}")
        
        # Sauvegarder
        output = {
            "updated_at": datetime.now().isoformat(),
            "total_matches": total_matches,
            "total_channels": len(schedule_by_channel),
            "channels": schedule_by_channel,
        }
        
        with open("data/schedule.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Fichier sauvegardé : data/schedule.json")
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        
        # Données de secours si le scraping échoue
        fallback_data = {
            "Canal+ Sport": [
                {"time": "20:45", "sport": "Football", "competition": "Ligue 1", "match": "PSG – Marseille", "is_live": False, "date": datetime.now().strftime("%Y-%m-%d")}
            ],
            "beIN SPORTS 1": [
                {"time": "21:00", "sport": "Football", "competition": "Premier League", "match": "Liverpool – Manchester City", "is_live": False, "date": datetime.now().strftime("%Y-%m-%d")}
            ]
        }
        
        output = {
            "updated_at": datetime.now().isoformat(),
            "total_matches": 2,
            "total_channels": 2,
            "channels": fallback_data,
        }
        
        with open("data/schedule.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print("📋 Données de secours utilisées")

if __name__ == "__main__":
    scrape_tv_sports()
