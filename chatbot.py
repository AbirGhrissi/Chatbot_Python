import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import string
from unidecode import unidecode
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Téléchargement des ressources NLTK
try:
    nltk.download('stopwords')
    nltk.download('punkt')
except Exception as e:
    logger.error(f"Erreur lors du téléchargement NLTK: {str(e)}")
    raise

# Initialisation
STOPWORDS = set(stopwords.words('french'))
stemmer = SnowballStemmer('french')
SYNONYMS = {
    'directeur': ['responsable', 'président', 'dirigeant'],
    'inscription': ['admission', 'enregistrement', 'candidature'],
    'master': ['mastère', 'formation', 'diplôme'],
    'distance': ['en ligne', 'remote', 'digital']
}

def expand_synonyms(text):
    for word, syns in SYNONYMS.items():
        for syn in syns:
            text = text.replace(syn, word)
    return text

def nettoyer_texte(texte):
    try:
        if not isinstance(texte, str):
            return ""
            
        # Normalisation du texte
        texte = unidecode(texte.lower())  # Supprime les accents
        texte = re.sub(r'[^\w\s]', ' ', texte)  # Supprime la ponctuation
        texte = re.sub(r'\d+', '', texte)  # Supprime les chiffres
        texte = re.sub(r'\s+', ' ', texte).strip()  # Espaces multiples
        
        # Expansion des synonymes
        texte = expand_synonyms(texte)
        
        # Tokenization et stemming
        tokens = [stemmer.stem(t) for t in texte.split() 
                if t not in STOPWORDS and len(t) > 2]
        
        return ' '.join(tokens)
    except Exception as e:
        logger.error(f"Erreur nettoyage texte: {str(e)}")
        return ""

def charger_donnees(path="iset_site_data.csv"):
    try:
        df = pd.read_csv(path, encoding='utf-8')
        
        # Vérification des colonnes requises
        required_columns = ['Question', 'Réponse', 'Catégorie', 'URL']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Fichier CSV doit contenir les colonnes: {required_columns}")
        
        # Nettoyage des données
        df = df.dropna(subset=['Réponse'])
        df = df.drop_duplicates(subset=['Réponse'])
        df = df[df['Réponse'].str.len() > 20]  # Supprime réponses trop courtes
        
        # Prétraitement
        df['Question_clean'] = df['Question'].apply(nettoyer_texte)
        df['Reponse_clean'] = df['Réponse'].apply(nettoyer_texte)
        
        logger.info(f"Données chargées avec succès. {len(df)} entrées valides.")
        return df
        
    except Exception as e:
        logger.error(f"Erreur chargement données: {str(e)}")
        raise

def entrainer_model(df):
    try:
        # Configuration optimisée du vectorizer
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.85,
            stop_words=list(STOPWORDS)
        )
        
        # Combinaison question+réponse pour meilleure représentation
        df['full_text'] = df['Question_clean'] + " " + df['Reponse_clean']
        X = vectorizer.fit_transform(df['full_text'])
        
        logger.info(f"Modèle entraîné. Vocabulaire: {len(vectorizer.get_feature_names_out())} termes")
        return vectorizer, X
        
    except Exception as e:
        logger.error(f"Erreur entraînement modèle: {str(e)}")
        raise