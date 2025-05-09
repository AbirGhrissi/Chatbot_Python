import csv

# Fonction pour créer le fichier CSV avec les en-têtes
def create_votes_csv():
    try:
        # Vérifiez si le fichier existe déjà pour éviter de le créer à chaque exécution
        with open('votes.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Écriture des en-têtes du fichier CSV
            writer.writerow(['hash', 'likes', 'dislikes'])
        print("Le fichier votes.csv a été créé avec succès.")
    except Exception as e:
        print(f"Erreur lors de la création du fichier: {e}")

# Appelez cette fonction une seule fois lors du démarrage de l'application
create_votes_csv()
