from datetime import datetime
import requests
from typing import Optional, Dict, List
from extensions import logger

class CTSService:
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout

    def format_time(self, time_str: str) -> str:
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            return dt.strftime('%H:%M')
        except Exception:
            return time_str

    def get_stop_monitoring(self, stop_code: str, api_token: str, vehicle_mode: str = None) -> Optional[List[Dict]]:
        """Récupère les prochains passages à un arrêt"""
        if not stop_code or not api_token:
            logger.error("Code d'arrêt ou token API manquant")
            return None

        try:
            # Construction des paramètres avec limite à 6 passages
            params = {
                "MonitoringRef": stop_code,
                "VehicleMode": vehicle_mode if vehicle_mode != "undefined" else None,
                "PreviewInterval": "PT30M",
                "MaximumStopVisits": 6,  # Limité à 6 passages
                "MinimumStopVisitsPerLine": 2  # 2 passages minimum par ligne
            }

            # Utilisation de l'authentification Basic avec mot de passe vide
            response = requests.get(
                f"{self.base_url}/v1/siri/2.0/stop-monitoring",
                params=params,
                auth=(api_token, ""),
                timeout=self.timeout
            )

            logger.info(f"Appel API CTS pour l'arrêt {stop_code}, statut: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"Erreur API CTS {response.status_code}: {response.text}")
                return None

            data = response.json()
            return self._process_monitoring_data(data)

        except Exception as e:
            logger.error(f"Erreur lors de l'appel à l'API CTS: {str(e)}")
            return None

    def _process_monitoring_data(self, data: Dict) -> List[Dict]:
        """Traite et transforme les données de monitoring"""
        try:
            visits = []
            monitored_visits = data.get("ServiceDelivery", {}).get("StopMonitoringDelivery", [{}])[0].get("MonitoredStopVisit", [])

            # Trie les visites par heure d'arrivée
            def get_arrival_time(visit):
                return visit.get("MonitoredVehicleJourney", {}).get("MonitoredCall", {}).get("ExpectedArrivalTime", "")
            
            monitored_visits.sort(key=get_arrival_time)
            
            # Ne garde que les 6 premiers passages
            for visit in monitored_visits[:6]:
                journey = visit.get("MonitoredVehicleJourney", {})
                monitored_call = journey.get("MonitoredCall", {})
                
                # Vérification des données essentielles
                if not all([journey.get("PublishedLineName"), 
                          journey.get("DestinationName"),
                          monitored_call.get("ExpectedArrivalTime")]):
                    continue

                processed_visit = {
                    "line": journey["PublishedLineName"],
                    "destination": journey["DestinationName"],
                    "arrival_time": self.format_time(monitored_call["ExpectedArrivalTime"]),
                    "vehicle_mode": journey.get("VehicleMode", "undefined"),
                    "is_real_time": monitored_call.get("Extension", {}).get("IsRealTime", False)
                }
                visits.append(processed_visit)

            return visits

        except Exception as e:
            logger.error(f"Erreur de traitement des données: {str(e)}")
            return []
