import json
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup

def scrape_data():
    # Créer le dossier data s'il n'existe pas
    os.makedirs("data", exist_ok=True)
    
    url = "https://tv-sports.fr/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        programmes = []
        
        # ⚠️ À ADAPTER : Voici un exemple basé sur la structure typique.
        # Vous devrez inspecter le code source (F12) du site cible pour trouver les bonnes classes.
        # for item in soup.find_all('div', class_='programme-item'):
        #     channel = item.find('span', class_='channel-name').text.strip()
        #     time = item.find('span', class_='time').text.strip()
        #     sport = item.find('span', class_='sport').text.strip()
        #     competition = item.find('span', class_='competition').text.strip()
        #     match = item.find('h3').text.strip()
        #     programmes.append({...})

        # Pour tester le site immédiatement, voici des données fictives réalistes :
        programmes = [
            {"channel": "Canal+ Sport", "time": "20h37", "sport": "Football", "competition": "Ligue 1", "match": "PSG – Lyon", "is_live": True},
            {"channel": "beIN SPORTS 1", "time": "21h00", "sport": "Formule 1", "competition": "Grand Prix des États-Unis", "match": "La course", "is_live": True},
            {"channel": "L'Équipe", "time": "14h30", "sport": "Football", "competition": "Ligue 1", "match": "Monaco – Lille", "is_live": True},
            {"channel": "Canal+ Sport", "time": "23h00", "sport": "Rugby", "competition": "Top 14", "match": "Toulouse – La Rochelle", "is_live": False}
        ]
        
        # Regrouper les matchs par chaîne
        by_channel = {}
        for p in programmes:
            ch = p["channel"]
            if ch not in by_channel:
                by_channel[ch] = []
            by_channel[ch].append(p)
            
        # Trier les matchs par heure pour chaque chaîne
        for ch in by_channel:
            by_channel[ch].sort(key=lambda x: x["time"])

        output = {
            "updated_at": datetime.now().isoformat(),
            "channels": by_channel
        }
        
        # Sauvegarder dans le fichier JSON
        with open("data/schedule.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
            
        print("✅ Données mises à jour avec succès.")
        
    except Exception as e:
        print(f"❌ Erreur lors du scraping : {e}")

if __name__ == "__main__":
    scrape_data()
