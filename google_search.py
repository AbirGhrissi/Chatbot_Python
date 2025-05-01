import requests
from urllib.parse import quote
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleSearcher:
    def __init__(self, api_key=None, cse_id=None):
        self.api_key = api_key
        self.cse_id = cse_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.location = "iset sfax"
    def search(self, query, site=None, num_results=3):
        """Effectue une recherche Google"""
        if not self.api_key or not self.cse_id:
            logger.warning("API Google non configurée - utilisation de la recherche web directe")
            return self.fallback_search(query, site)
            
        params = {
            'q': f"{query} {self.location}" ,
            'key': self.api_key,
            'cx': self.cse_id,
            'num': num_results
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=5)
            if response.status_code == 200:
                return self.format_results(response.json())
        except Exception as e:
            logger.error(f"Erreur recherche Google: {str(e)}")
            return self.fallback_search(query, site)
        return []
    
    def fallback_search(self, query, site=None):
        """Solution de repli sans API"""
        full_query = f"{query} {self.location}"
        search_url = f"https://www.google.com/search?q={quote(query)}"
        return [{
            'title': f"Recherche Google: {query}",
            'link': search_url,
            'snippet': f"Cliquez pour voir les résultats de recherche Google pour '{query}'"
        }]
    
    def format_results(self, google_data):
        """Formate les résultats de l'API Google"""
        return google_data.get('items', [])
    
    @staticmethod
    def generate_search_link(query, site=None):
        """Génère un lien de recherche Google classique"""
        query = f"{query} site:{site}" if site else query
        return f"https://www.google.com/search?q={quote(query)}"

if __name__ == '__main__':
    # Configuration (à remplacer par vos clés réelles)
    API_KEY = "AIzaSyARc-noNwxYpnX28_L4IILVl5zqhp3EIOs"
    CSE_ID = "d63b4fdd2d76b4ab6"
    
    # Initialisation
    searcher = GoogleSearcher(api_key=API_KEY, cse_id=CSE_ID)