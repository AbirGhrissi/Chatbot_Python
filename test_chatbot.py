import requests
import json
from time import sleep

BASE_URL = "http://localhost:5000/chat"

def test_question(question):
    print(f"\nQuestion: {question}")
    response = requests.post(BASE_URL, json={"message": question})
    
    if response.status_code == 200:
        data = response.json()
        print("Statut: Succès")
        
        if 'reponses' in data:
            print(f"Message: {data['message']}")
            for i, rep in enumerate(data['reponses'], 1):
                print(f"\nRéponse {i}:")
                print(f"Score: {rep['score']:.2f}")
                print(f"Catégorie: {rep.get('categorie', 'N/A')}")
                print(f"Source: {rep['source']}")
                print(f"Contenu:\n{rep['reponse']}")
        else:
            print(f"Score: {data['score']:.2f}")
            print(f"Source: {data.get('source', 'N/A')}")
            print(f"Réponse:\n{data['reponse']}")
    else:
        print(f"Statut: Erreur {response.status_code}")
        print(response.text)

# Questions de test supplémentaires
QUESTIONS = [
    "qui est le directeur",
    "inscription distance",
    "master informatique",
    "clubs étudiants",
    "contacts école",
    "comment postuler pour un master ?", 
    "quelles sont les conditions d'admission ?",
    "où se trouve l'ISET de Sfax ?",
    "quels sont les avantages du programme de master ?", 
    "quelles sont les spécialisations en master informatique ?", 
    "qu’est-ce que le master DSI ?",
    "quelles sont les modalités de financement ?", 
    "quels sont les projets étudiants à l'ISET de Sfax ?", 
    "qui sont les responsables de l'ISET ?", 
    "quelles sont les formations proposées en informatique ?",
    "y a-t-il des clubs étudiants à l'ISET ?", 
    "rentrée scolaire"
]

if __name__ == "__main__":
    print("Démarrage des tests du chatbot ISET Sfax...\n")
    
    for question in QUESTIONS:
        test_question(question)
        sleep(1)  # Pause entre les requêtes
        
    print("\nTests terminés.")
