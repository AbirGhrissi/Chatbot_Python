import requests 
import aiohttp
import asyncio
from flask import Flask, request, jsonify, render_template
from chatbot import charger_donnees, entrainer_model, nettoyer_texte
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging
from datetime import datetime
import csv
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from functools import lru_cache
import hashlib
from google_search import GoogleSearcher
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
import time
from nltk.tokenize import word_tokenize
from collections import defaultdict
import os

app = Flask(__name__)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration globale
ISET_URL = "https://isetsf.rnu.tn"
CSV_FILE = 'iset_site_data.csv'
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
REQUEST_TIMEOUT = 3  # seconds
GOOGLE_TIMEOUT = 5  # seconds
MAX_CONCURRENT_REQUESTS = 5
MAX_PAGES_TO_CRAWL = 8
CSV_FILE_VOTE = 'votes.csv'
# Initialisation globale
app.df = None
app.vectorizer = None
app.X = None
app.votes = defaultdict(lambda: {'likes': 0, 'dislikes': 0})

# Configuration des requêtes HTTP (pour les parties synchrones)
session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(
    max_retries=retry,
    pool_connections=20,
    pool_maxsize=20
)
session.mount("http://", adapter)
session.mount("https://", adapter)
session.headers.update({
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
})

# Initialiser le chercheur Google
google_searcher = GoogleSearcher(
    api_key="AIzaSyARc-noNwxYpnX28_L4IILVl5zqhp3EIOs",
    cse_id="d63b4fdd2d76b4ab6"
)

# Cache pour les recherches Google
@lru_cache(maxsize=100)
def cached_google_search(query, site=None):
    query_hash = hashlib.md5(f"{query}_{site}".encode()).hexdigest()
    return google_searcher.search(query, site)

# Décoration pour mesurer les temps d'exécution
def log_execution_time(func):
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        logger.info(f"{func.__name__} executed in {time.time()-start:.2f}s")
        return result
    return async_wrapper

def init_app():
    try:
        logger.info("Chargement des données...")
        app.df = charger_donnees()
        app.vectorizer, app.X = entrainer_model(app.df)
        app.votes = load_votes()
        logger.info(f"Modèle chargé avec {len(app.df)} entrées")
    except Exception as e:
        logger.error(f"Erreur initialisation: {str(e)}")
        raise
async def fetch_page(session, url):
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as response:
            if response.status == 200:
                return await response.text()
            return None
    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching {url}")
        return None
    except Exception as e:
        logger.warning(f"Error fetching {url}: {str(e)}")
        return None

async def extract_page_content_async(url):
    async with aiohttp.ClientSession() as session:
        html = await fetch_page(session, url)
        if not html:
            return None
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Supprimer les éléments inutiles
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe', 'noscript']):
            element.decompose()
        
        # Extraction optimisée
        title = soup.find('h1') or soup.find('title')
        title_text = title.get_text(strip=True) if title else "Page sans titre"
        
        sections = {}
        current_section = "Contenu"
        content = []
        
        for element in soup.find_all(['p', 'h2', 'h3', 'h4']):
            if element.name in ['h2', 'h3', 'h4']:
                if content:
                    sections[current_section] = ' '.join(content)
                    content = []
                current_section = element.get_text(strip=True)
            else:
                content.append(element.get_text(strip=True))
        
        if content:
            sections[current_section] = ' '.join(content)
        
        if not sections:
            main_content = soup.find('main') or soup
            sections['Contenu'] = ' '.join(main_content.get_text(' ', strip=True).split())
        
        return {
            'title': title_text,
            'url': url,
            'sections': sections,
            'full_text': ' '.join(sections.values())
        }
def load_votes():
    try:
        with open('votes.csv', mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            votes = defaultdict(lambda: {'likes': 0, 'dislikes': 0})
            for row in reader:
                votes[row['hash']] = {'likes': int(row['likes']), 'dislikes': int(row['dislikes'])}
            return votes
    except FileNotFoundError:
        return defaultdict(lambda: {'likes': 0, 'dislikes': 0})

def save_votes(votes):
    with open('votes.csv', mode='w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['hash', 'likes', 'dislikes'])
        writer.writeheader()
        for hash, data in votes.items():
            writer.writerow({'hash': hash, 'likes': data['likes'], 'dislikes': data['dislikes']})
@log_execution_time
async def process_page_async(url, question):
    try:
        page_data = await extract_page_content_async(url)
        if not page_data:
            return None
            
        relevant_sections = intelligent_search(question, page_data)
        if not relevant_sections:
            return None
            
        best_section = relevant_sections[0]
        return {
            'url': url,
            'title': page_data['title'],
            'section': best_section['section'],
            'extract': best_section['content'][:500] + '...',
            'score': best_section['score'] * 0.8 + analyze_page_relevance(url, question) * 0.2
        }
    except Exception as e:
        logger.error(f"Error processing {url}: {str(e)}")
        return None

def get_important_pages():
    return [
        f"{ISET_URL}/fr",
        f"{ISET_URL}/frformations-top",
        f"{ISET_URL}/fr/admission",
        f"{ISET_URL}/fr/calendrier-academique",
        f"{ISET_URL}/fr/contactez-nous",
        f"{ISET_URL}/fr/actualites",
        f"{ISET_URL}/fr/reglement-interieur",
        f"{ISET_URL}/fr/emploi-du-temps"
    ]

async def crawl_known_pages_async(base_url, max_depth=1):
    visited = set()
    to_visit = [(base_url, 0)]
    found_urls = []
    
    async with aiohttp.ClientSession() as session:
        while to_visit and len(found_urls) < MAX_PAGES_TO_CRAWL:
            url, depth = to_visit.pop()
            if url in visited or depth > max_depth:
                continue
                
            html = await fetch_page(session, url)
            if not html:
                continue
                
            soup = BeautifulSoup(html, 'html.parser')
            visited.add(url)
            
            for link in soup.find_all('a', href=True):
                if len(found_urls) >= MAX_PAGES_TO_CRAWL:
                    break
                    
                href = link['href']
                full_url = urljoin(base_url, href)
                
                if (full_url.startswith(base_url) and 
                    not any(ext in full_url for ext in ['.pdf', '.jpg', '.png']) and
                    '/fr/' in full_url.lower() and
                    full_url not in visited):
                    
                    found_urls.append(full_url)
                    if depth < max_depth:
                        to_visit.append((full_url, depth + 1))
    
    return list(set(found_urls))

from nltk.tokenize import word_tokenize

def intelligent_search(question, page_data):
    # Tokenize et nettoyer la question
    question_words = set(
        word.lower() for word in word_tokenize(question) 
        if word.lower() not in STOPWORDS and len(word) > 2
    )
    
    best_sections = []
    
    for section_name, section_content in page_data['sections'].items():
        content_lower = section_content.lower()
        
        # Compter le nombre de mots de la question présents dans la section
        matches = sum(1 for word in question_words if word in content_lower)
        
        # Score basé sur le pourcentage de correspondance
        if matches > 0:
            score = (matches / len(question_words)) * 100  # Score en %
            
            # Seuil minimal pour éviter le bruit (ex: au moins 50% de correspondance)
            if score >= 50:  
                best_sections.append({
                    'section': section_name,
                    'content': section_content,
                    'score': score
                })
    
    # Tri par score décroissant
    return sorted(best_sections, key=lambda x: x['score'], reverse=True)
def analyze_page_relevance(url, question):
    path = url.split('/')[-1].lower()
    question_terms = [term for term in question.split() if len(term) > 3]
    
    url_score = sum(1 for term in question_terms if term in path)
    important_pages = ['contact', 'calendrier', 'admission', 'formation', 'actualites', 'reglement', 'emploi']
    bonus = 2 if any(page in path for page in important_pages) else 0
    
    return url_score + bonus

@log_execution_time
async def search_in_iset_site(question):
    important_urls = get_important_pages()
    crawled_urls = await crawl_known_pages_async(ISET_URL)
    all_urls = list(set(important_urls + crawled_urls))[:MAX_PAGES_TO_CRAWL]
    
    if not all_urls:
        return "Impossible de trouver des URLs à explorer."
    
    results = await asyncio.gather(*[
        process_page_async(url, question) 
        for url in all_urls
    ])
    
    valid_results = [res for res in results if res is not None]
    
    if not valid_results:
        return "Aucune information pertinente trouvée. Essayez avec d'autres termes."
    
    valid_results.sort(key=lambda x: x['score'], reverse=True)
    
    return [
        {
            'url': res['url'],
            'extract': f"{res['title']} > {res['section']}\n{res['extract']}",
            'score': res['score']
        }
        for res in valid_results[:3]  # Top 3 résultats
    ]

def format_response(text):
    if not isinstance(text, str):
        return ""
    text = ' '.join(text.split())
    return text[:500] + "..." if len(text) > 500 else text

def is_greeting(text):
    greetings = ['hi', 'hello', 'salut', 'hey', 'bonjour','bonsoir']
    return text.lower() in greetings

def store_in_csv(question, answer):
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now(), question, str(answer)])
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['hash', 'likes', 'dislikes'])
        writer.writeheader()

@app.route('/vote', methods=['POST'])
def vote():
    try:
        data = request.json
        response_hash = str(data.get('hash'))  # Convertir en string pour être sûr
        vote_type = data.get('type')
        site_data = data.get('site_data')  # Dictionnaire avec Question, Réponse, URL

        if not response_hash or vote_type not in ['like', 'dislike'] or not isinstance(site_data, dict):
            return jsonify({'status': 'error', 'message': 'Invalid input'}), 400

        # ----------- Mise à jour du fichier votes.csv -----------
        votes = []
        found = False

        try:
            with open(CSV_FILE_VOTE, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['hash'] == response_hash:
                        if vote_type == 'like':
                            row['likes'] = str(int(row['likes']) + 1)
                        else:
                            row['dislikes'] = str(int(row['dislikes']) + 1)
                        found = True
                    votes.append(row)
        except FileNotFoundError:
            pass

        if not found:
            votes.append({
                'hash': response_hash,
                'likes': '1' if vote_type == 'like' else '0',
                'dislikes': '1' if vote_type == 'dislike' else '0'
            })

        with open(CSV_FILE_VOTE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['hash', 'likes', 'dislikes'])
            writer.writeheader()
            writer.writerows(votes)

        # ----------- Mise à jour du fichier iset_site_data.csv -----------
        already_exists = False
        site_rows = []

        try:
            with open(CSV_FILE, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['hash'] == response_hash:
                        already_exists = True
                    site_rows.append(row)
        except FileNotFoundError:
            pass  # fichier inexistant, on le créera plus bas

        if not already_exists:
            site_rows.append({
                'Question': site_data.get('Question', ''),
                'Réponse': site_data.get('Réponse', ''),
                'URL': site_data.get('URL', ''),
                'hash': response_hash
            })

            with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Question', 'Réponse', 'URL', 'hash'])
                writer.writeheader()
                writer.writerows(site_rows)

        return jsonify({'status': 'success'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
@app.route('/get_votes', methods=['GET'])
def get_votes():
    try:
        response_hash = request.args.get('hash')
        if not response_hash:
            return jsonify({'status': 'error', 'message': 'Hash missing'}), 400

        votes = {'likes': 0, 'dislikes': 0}
        
        try:
            with open(CSV_FILE_VOTE, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['hash'] == response_hash:
                        votes['likes'] = int(row.get('likes', 0))
                        votes['dislikes'] = int(row.get('dislikes', 0))
                        break
        except FileNotFoundError:
            pass

        return jsonify(votes)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
@app.route('/chat', methods=['POST'])
async def chat():
    start_time = datetime.now()
    
    try:
        if app.vectorizer is None or app.X is None:
            init_app()
        
        user_input = request.json.get("message", "").strip()
        if not user_input:
            return jsonify({"reponse": "Veuillez poser une question.", "score": 0})
        if is_greeting(user_input):
            return jsonify({"reponse": "Salut 👋 ! Comment puis-je vous aider aujourd'hui ?", "score": 1})
        
        clean_question = nettoyer_texte(user_input)
        question_vec = app.vectorizer.transform([clean_question])
        
        # Recherche dans la base de données locale
        similarities = cosine_similarity(question_vec, app.X)
        top_indices = np.argsort(similarities[0])[-5:][::-1]
        
        responses = []
        seen_responses = set()
        
        for idx in top_indices:
            score = similarities[0][idx]
            if score > 0.25:
                raw_response = app.df.iloc[idx]["Réponse"]
                clean_response = format_response(raw_response)
                
                response_hash = hash(clean_response[:100])
                if response_hash not in seen_responses:
                    seen_responses.add(response_hash)
                    responses.append({
                        "reponse": clean_response,
                        "score": float(score),
                        "source": app.df.iloc[idx]["URL"],
                        "categorie": app.df.iloc[idx]["Catégorie"],
                        "type": "local_db",
                        "hash": hash(clean_response[:100])  # Ajout du hash pour identifier la réponse
                    })

                    # Triez les réponses en fonction des votes avant de les renvoyer
                    responses.sort(key=lambda x: (
                        app.votes[str(x.get('hash', 0))]['likes'] - app.votes[str(x.get('hash', 0))]['dislikes'],
                        x['score']
                    ), reverse=True)
        
        # Si aucune réponse pertinente trouvée localement
        if not responses or all(resp['score'] < 0.5 for resp in responses):
            logger.info("Lancement de la recherche intelligente sur le site...")
            search_result = await search_in_iset_site(user_input)
            
            if isinstance(search_result, str):
                if not responses:
                    logger.info("Lancement de la recherche Google...")
                    google_results = cached_google_search(user_input, "isetsf.rnu.tn")
                    
                    if google_results:
                        formatted_google = []
                        for i, res in enumerate(google_results[:3], 1):
                            formatted_google.append(
                                f"<div class='google-result'>"
                                f"<h4>Résultat Google ({i}):</h4>"
                                f"<h5><a href='{res['link']}' target='_blank'>{res.get('title', 'Sans titre')}</a></h5>"
                                f"<p>{res.get('snippet', '')}</p>"
                                f"</div>"
                            )
                        
                        return jsonify({
                            "reponse": (
                                "<h3>Voici ce que j'ai trouvé via Google :</h3>"
                                f"{''.join(formatted_google)}"
                                f"<p class='more-results'>"
                                f"<a href='{GoogleSearcher.generate_search_link(user_input, site='isetsf.rnu.tn')}' "
                                f"target='_blank'>Voir plus de résultats Google</a>"
                                f"</p>"
                            ),
                            "score": 0.8,
                            "type": "google_search"
                        })
                    
                    return jsonify({
                        "reponse": (
                            f"Je n'ai pas trouvé d'information précise sur '{user_input}'. "
                            "Essayez avec des termes plus spécifiques ou consultez "
                            f"<a href='{ISET_URL}' target='_blank'>le site de l'ISET</a> directement."
                        ),
                        "score": 0.1
                    })
            else:
                formatted_results = []
                for i, res in enumerate(search_result[:3], 1):
                    clean_extract = BeautifulSoup(res['extract'], 'html.parser').get_text()
                    
                    formatted_results.append({
                        "reponse": (
                            f"<div class='search-result'>"
                            f"<h4>Résultat du site ISET ({i}):</h4>"
                            f"<p>{clean_extract}</p>"
                            f"<small>Source: <a href='{res['url']}' target='_blank'>{res['url']}</a></small>"
                            f"</div>"
                        ),
                        "score": res['score'] * 0.9,
                        "source": res['url'],
                        "categorie": "site_ISET",
                        "type": "site_search"
                    })
                
                responses.extend(formatted_results)
                store_in_csv(user_input, search_result)
        
        # Trier et formater les réponses
        responses.sort(key=lambda x: x['score'], reverse=True)
        
        if not responses:
            return jsonify({
                "reponse": "Je n'ai pas trouvé de réponse pertinente. Pourriez-vous reformuler votre question ?",
                "score": 0
            })
        
        best_response = responses[0]
        
        if best_response.get('type') == 'site_search' and best_response['score'] > 0.7:
            return jsonify({
                "reponse": f"<h3>Réponse trouvée sur le site de l'ISET :</h3>{best_response['reponse']}",
                "score": best_response['score'],
                "source": best_response['source'],
                "type": "site_result"
            })
        elif len(responses) > 1 and (responses[0]['score'] - responses[1]['score']) < 0.2:
            formatted_options = []
            for i, resp in enumerate(responses[:3], 1):
                source = f"<small>Source: <a href='{resp['source']}' target='_blank'>{resp['source']}</a></small>"
                content = resp['reponse'] if resp.get('type') == 'site_search' else f"<p>{resp['reponse']}</p>{source}"
                formatted_options.append(
                    f"<div class='response-option'>"
                    f"<h4>Option {i} (score: {resp['score']:.2f})</h4>"
                    f"{content}"
                    f"</div>"
                )
            
            return jsonify({
                "reponse": (
                    "<h3>Plusieurs réponses possibles :</h3>"
                    "<div class='multiple-responses'>"
                    f"{''.join(formatted_options)}"
                    "</div>"
                ),
                "score": best_response['score'],
                "type": "multiple_options"
            })
        else:
            content = best_response['reponse']
            if best_response.get('type') == 'local_db':
                source = f"<small>Source: <a href='{best_response['source']}' target='_blank'>{best_response['source']}</a></small>"
                content = f"<p>{content}</p>{source}"
            
            return jsonify({
                "reponse": content,
                "score": best_response['score'],
                "source": best_response.get('source', ''),
                "type": "single_response"
            })
            
    except Exception as e:
        logger.exception(f"Erreur lors du traitement: {str(e)}")
        return jsonify({
            "reponse": (
                "Une erreur technique est survenue. Notre équipe a été notifiée. "
                "Vous pouvez essayer de reformuler votre question ou "
                f"consulter <a href='{ISET_URL}' target='_blank'>le site de l'ISET</a> directement."
            ),
            "error": str(e),
            "score": 0
        })
    
    finally:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Temps total de traitement: {processing_time:.2f} secondes")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "OK" if app.vectorizer is not None else "ERROR",
        "data_points": len(app.df) if app.df is not None else 0,
        "model_ready": app.vectorizer is not None
    })

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    init_app()
    app.run(host='0.0.0.0', port=5000, debug=True)