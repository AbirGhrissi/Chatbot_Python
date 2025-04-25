from flask import Flask, request, jsonify
from chatbot import charger_donnees, entrainer_model, nettoyer_texte
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging
from datetime import datetime

app = Flask(__name__)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation globale
app.df = None
app.vectorizer = None
app.X = None

def init_app():
    try:
        logger.info("Chargement des données...")
        app.df = charger_donnees()
        app.vectorizer, app.X = entrainer_model(app.df)
        logger.info(f"Modèle chargé avec {len(app.df)} entrées")
    except Exception as e:
        logger.error(f"Erreur initialisation: {str(e)}")
        raise

def format_response(text):
    """Nettoie et formate les réponses pour l'affichage"""
    if not isinstance(text, str):
        return ""
    text = ' '.join(text.split())  # Supprime les espaces multiples
    if len(text) > 500:
        return text[:497] + "..."
    return text

@app.route('/chat', methods=['POST'])
def chat():
    start_time = datetime.now()
    
    try:
        # Vérifier que le modèle est chargé
        if app.vectorizer is None or app.X is None:
            init_app()
            if app.vectorizer is None:
                raise RuntimeError("Modèle non initialisé")
        
        # Récupération de la question
        user_input = request.json.get("message", "").strip()
        if not user_input:
            return jsonify({"reponse": "Veuillez poser une question.", "score": 0})
        
        # Nettoyage et vectorisation
        clean_question = nettoyer_texte(user_input)
        question_vec = app.vectorizer.transform([clean_question])
        
        # Calcul des similarités
        similarities = cosine_similarity(question_vec, app.X)
        top_indices = np.argsort(similarities[0])[-5:][::-1]  # Top 5 résultats
        
        # Préparation des réponses
        responses = []
        seen_responses = set()
        
        for idx in top_indices:
            score = similarities[0][idx]
            if score > 0.25:  # Seuil minimal
                raw_response = app.df.iloc[idx]["Réponse"]
                clean_response = format_response(raw_response)
                
                # Éviter les doublons
                response_hash = hash(clean_response[:100])
                if response_hash not in seen_responses:
                    seen_responses.add(response_hash)
                    
                    responses.append({
                        "reponse": clean_response,
                        "score": float(score),
                        "source": app.df.iloc[idx]["URL"],
                        "categorie": app.df.iloc[idx]["Catégorie"]
                    })
        
        # Tri par score décroissant
        responses.sort(key=lambda x: x['score'], reverse=True)
        
        # Formatage de la réponse finale
        if not responses:
            return jsonify({
                "reponse": "Je n'ai pas trouvé de réponse précise. Essayez de reformuler.",
                "score": 0
            })
        
        best_score = responses[0]['score']
        if best_score > 0.6 or len(responses) == 1:
            return jsonify(responses[0])
        else:
            return jsonify({
                "message": "Plusieurs réponses possibles :",
                "reponses": responses[:3],  # Limite à 3 meilleures réponses
                "query": user_input
            })
            
    except Exception as e:
        logger.exception(f"Erreur lors du traitement: {str(e)}")
        return jsonify({
            "reponse": "Une erreur est survenue. Veuillez réessayer.",
            "error": str(e),
            "score": 0
        })
    
    finally:
        logger.info(f"Temps de traitement: {datetime.now() - start_time}")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "OK" if app.vectorizer is not None else "ERROR",
        "data_points": len(app.df) if app.df is not None else 0,
        "model_ready": app.vectorizer is not None
    })

if __name__ == '__main__':
    init_app()
    app.run(host='0.0.0.0', port=5000, debug=True)