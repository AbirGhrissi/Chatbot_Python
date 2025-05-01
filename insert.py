import csv

# Définir les données à insérer dans le fichier CSV
data = [
    ["question", "réponse", "catégorie", "source"],
    ["comment postuler pour un master ?", "Pour postuler à un master, vous devez vous rendre sur notre plateforme d'inscription en ligne et suivre les instructions...", "fr", "https://isetsf.rnu.tn/fr/inscriptions"],
    ["quelles sont les conditions d'admission ?", "Les conditions d'admission pour les masters incluent une licence en informatique...", "fr", "https://isetsf.rnu.tn/fr/conditions-admission"],
    ["où se trouve l’ISET de Sfax ?", "L'ISET de Sfax est situé à la route Mahdia, km 2,5, à Sfax, en Tunisie.", "fr", "https://isetsf.rnu.tn/fr/institut/localisation"],
    ["quels sont les avantages du programme de master ?", "Le programme de master de l’ISET de Sfax vous offre une formation de haute qualité dans des domaines comme les technologies de l’information, avec des possibilités d’internat et des partenariats avec des entreprises de renom.", "fr", "https://isetsf.rnu.tn/fr/formation/master"],
    ["quelles sont les spécialisations en master informatique ?", "Le master en informatique propose des spécialisations en :\n• Développement des systèmes informatiques (DSI)\n• Réseaux et systèmes informatiques (RSI)\n• Génie logiciel et nouvelles technologies (GLNT)", "fr", "https://isetsf.rnu.tn/fr/formation/master-informatique"],
    ["qu’est-ce que le master DSI ?", "Le master en Développement des Systèmes Informatiques (DSI) est destiné à former des experts capables de concevoir, développer et gérer des systèmes informatiques complexes dans divers environnements.", "fr", "https://isetsf.rnu.tn/fr/formation/dsi"],
    ["quelles sont les modalités de financement ?", "Il existe plusieurs options de financement pour les étudiants, y compris des bourses d’études, des prêts étudiants et des partenariats avec des entreprises.", "fr", "https://isetsf.rnu.tn/fr/financement"],
    ["quels sont les projets étudiants à l'ISET de Sfax ?", "Les étudiants de l’ISET de Sfax sont impliqués dans de nombreux projets innovants dans le domaine des technologies, y compris des projets de recherche, des hackathons et des stages en entreprises.", "fr", "https://isetsf.rnu.tn/fr/projets-etudiants"],
    ["qui sont les responsables de l’ISET ?", "Le responsable de l'ISET de Sfax est le Directeur Bassem JALLOULI, assisté par des responsables de département et des coordinateurs pour chaque programme de formation.", "fr", "https://isetsf.rnu.tn/fr/institut/responsables"],
    ["quelles sont les formations proposées en informatique ?", "Les formations proposées en informatique à l'ISET de Sfax incluent :\n• Licence en technologies de l'informatique\n• Master en informatique\n• Formation continue et à distance", "fr", "https://isetsf.rnu.tn/fr/formation/informatique"],
    ["y a-t-il des clubs étudiants à l'ISET ?", "Oui, l'ISET de Sfax offre plusieurs clubs étudiants dans des domaines scientifiques, culturels, sportifs et humanitaires, tels que le Club Futur Licencier.", "fr", "https://isetsf.rnu.tn/fr/etudiants/clubs"],
    ["quelles sont les dates limites d'inscription ?", "Les inscriptions au master doivent être complétées avant le 15 septembre. Les candidatures tardives peuvent être examinées au cas par cas.", "fr", "https://isetsf.rnu.tn/fr/inscriptions"],
    ["comment contacter le service des admissions ?", "Vous pouvez contacter le service des admissions par email à admissions@isetsf.rnu.tn ou par téléphone au +216 74 000 000.", "fr", "https://isetsf.rnu.tn/fr/contact"],
    ["le master est-il ouvert aux étudiants étrangers ?", "Oui, les étudiants étrangers peuvent postuler sous réserve de validation de leur diplôme équivalent et des formalités administratives.", "fr", "https://isetsf.rnu.tn/fr/etudiants-internationaux"],
    ["proposez-vous des cours en ligne ?", "Certains modules de master sont proposés en ligne via notre plateforme d'apprentissage à distance, en complément des cours en présentiel.", "fr", "https://isetsf.rnu.tn/fr/formation/elearning"],
    ["quel est le coût du master ?", "Les frais d’inscription pour le master sont de 500 dinars par an pour les étudiants tunisiens. Pour les étudiants étrangers, les frais sont de 1500 dinars par an.", "fr", "https://isetsf.rnu.tn/fr/formation/master"],
    ["comment est structuré le programme de master ?", "Le programme est structuré en 4 semestres comprenant des cours théoriques, des travaux pratiques, un projet de recherche et un stage de fin d'études.", "fr", "https://isetsf.rnu.tn/fr/formation/structure-master"],
    ["y a-t-il un stage obligatoire ?", "Oui, un stage de fin d'études d'une durée minimale de 4 mois est obligatoire pour l'obtention du diplôme de master.", "fr", "https://isetsf.rnu.tn/fr/stages"],
    ["quelles entreprises collaborent avec l’ISET ?", "Nous collaborons avec plusieurs entreprises telles que Telnet, Ooredoo, Vermeg, ainsi que des startups locales pour offrir des stages et des projets professionnels.", "fr", "https://isetsf.rnu.tn/fr/partenaires"],
    ["quel est le taux d'insertion professionnelle après le master ?", "Le taux d'insertion professionnelle des diplômés du master est supérieur à 85 % dans les 6 mois suivant l'obtention du diplôme.", "fr", "https://isetsf.rnu.tn/fr/statistiques"],
    ["quelles compétences vais-je acquérir ?", "Vous développerez des compétences en développement logiciel avancé, administration de réseaux, sécurité informatique, gestion de projets IT et recherche appliquée.", "fr", "https://isetsf.rnu.tn/fr/formation/competences"],
]

file_name = 'iset_site_data.csv'

# Ouvrir le fichier CSV en mode ajout ('a') et insérer les données
with open(file_name, mode='a', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerows(data)

print(f"Les données ont été ajoutées dans le fichier {file_name}")
