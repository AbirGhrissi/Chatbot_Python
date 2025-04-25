import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
import re
import logging
from tqdm import tqdm

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SiteCrawler:
    def __init__(self, base_url, max_pages=100):
        self.visited = set()
        self.data = []
        self.base_url = base_url
        self.max_pages = max_pages
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def is_internal_link(self, link):
        parsed = urlparse(link)
        base_parsed = urlparse(self.base_url)
        return parsed.netloc == "" or parsed.netloc == base_parsed.netloc

    def is_valid_content(self, text):
        if not text or len(text) < 40:
            return False
        if re.search(r"cliquez ici|en savoir plus|plus d'infos|©|mentions légales", text, re.IGNORECASE):
            return False
        return True

    def clean_text(self, text):
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def extract_page_content(self, url, soup):
        title = soup.title.string.strip() if soup.title else "Page ISET"
        page_data = []

        # Extraction des sections principales
        sections = []
        for h2 in soup.find_all(['h1', 'h2', 'h3']):
            section_title = self.clean_text(h2.get_text())
            content = []
            next_node = h2.next_sibling
            
            while next_node:
                if next_node.name in ['h1', 'h2', 'h3']:
                    break
                if next_node.name in ['p', 'ul', 'ol']:
                    text = self.clean_text(next_node.get_text())
                    if self.is_valid_content(text):
                        content.append(text)
                next_node = next_node.next_sibling
            
            if content:
                sections.append({
                    'title': section_title,
                    'content': '\n'.join(content)
                })

        # Formatage des données
        for section in sections:
            question = f"{title} - {section['title']}"
            self.data.append([
                question,
                section['content'],
                urlparse(url).path.strip("/").split("/")[0] or "accueil",
                url + "#" + re.sub(r'[^a-z0-9]+', '-', section['title'].lower())
            ])

    def crawl(self, url=None):
        if len(self.visited) >= self.max_pages:
            return
            
        url = url or self.base_url
        if url in self.visited:
            return
            
        self.visited.add(url)
        logger.info(f"Exploration: {url}")

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logger.warning(f"Erreur accès {url}: {str(e)}")
            return

        soup = BeautifulSoup(response.content, "html.parser")
        self.extract_page_content(url, soup)

        # Exploration des liens
        for link in soup.find_all("a", href=True):
            if len(self.visited) >= self.max_pages:
                break
                
            href = link['href']
            if href.startswith('mailto:') or href.startswith('tel:'):
                continue
                
            absolute_url = urljoin(url, href)
            if self.is_internal_link(absolute_url) and absolute_url not in self.visited:
                self.crawl(absolute_url)

    def save_data(self, filename="iset_site_data.csv"):
        df = pd.DataFrame(self.data, columns=["Question", "Réponse", "Catégorie", "URL"])
        df.drop_duplicates(subset=["Réponse"], inplace=True)
        df.to_csv(filename, index=False, encoding="utf-8")
        logger.info(f"Fichier créé avec {len(df)} lignes: {filename}")

if __name__ == '__main__':
    crawler = SiteCrawler(base_url="https://isetsf.rnu.tn/fr", max_pages=100)
    crawler.crawl()
    crawler.save_data()