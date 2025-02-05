import requests
from typing import Optional, Dict
from extensions import logger

class WeatherService:
    def __init__(self, base_url: str = "https://api.openweathermap.org/data/2.5", timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout

    def get_current_weather(self, city: str, api_key: str) -> Optional[Dict]:
        """Récupère les données météorologiques actuelles pour une ville"""
        if not city or not api_key:
            logger.error("Ville ou clé API manquante")
            return None

        try:
            params = {
                "q": city,
                "appid": api_key,
                "units": "metric",
                "lang": "fr"
            }

            response = requests.get(
                f"{self.base_url}/weather",
                params=params,
                timeout=self.timeout
            )

            logger.info(f"Appel API météo pour {city}, statut: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"Erreur API météo {response.status_code}: {response.text}")
                return None

            data = response.json()
            return self._process_weather_data(data)

        except requests.exceptions.Timeout:
            logger.error("Timeout de la requête météo")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de requête météo: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue météo: {str(e)}")
            return None

    def _process_weather_data(self, data: Dict) -> Dict:
        """Traite et transforme les données météorologiques"""
        try:
            return {
                'temp': round(data['main']['temp']),
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'humidity': data['main'].get('humidity'),
                'pressure': data['main'].get('pressure'),
                'wind_speed': data['wind'].get('speed'),
                'feels_like': round(data['main'].get('feels_like', 0))
            }
        except Exception as e:
            logger.error(f"Erreur de traitement des données météo: {str(e)}")
            return {}
