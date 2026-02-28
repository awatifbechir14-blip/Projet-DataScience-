# Système de Surveillance des Données de Pression Artérielle patient avec Kafka, Elasticsearch et Kibana

## 1. Description générale
Ce projet vise à utiliser une architecture Big Data afin de surveiller les données de pressions artérielle des patients en temps réel. Il permet de detecter automatiquement et rapidement les anomalies, les indexe dans Elasticsearch pour les visualiser dans Kibana.

L’architecture repose sur un modèle de streaming. Un module producteur génère des observations de pression artérielle et les publie dans un topic Kafka. Un module consommateur récupère ensuite ces messages, applique des règles d’analyse basées sur des seuils médicaux, puis oriente les données vers un stockage adapté. Cette séparation entre production et consommation illustre le principe fondamental de découplage offert par Kafka : le producteur et le consommateur fonctionnent indépendamment tout en communiquant de manière fiable via le broker.
L’objectif principal du projet est de détecter automatiquement et rapidement les cas d’hypertension ou d’hypotension, d’identifier les patients nécessitant un suivi médical renforcé, et de rendre ces informations exploitables via un système de visualisation.

## 2. Génération des Messages FHIR 
Les données générées sont inspirées du standard FHIR (Fast Healthcare Interoperability Resources), notamment de la ressource Observation utilisée pour représenter des mesures cliniques. Afin de simplifier le traitement côté consumer, un format JSON simplifié a été retenu tout en conservant la sémantique médicale essentielle.
Chaque message contient un identifiant court de patient, un nom généré aléatoirement, une valeur de pression artérielle systolique, une valeur diastolique ainsi qu’un horodatage au format ISO 8601. Cette structure permet de représenter une observation clinique tout en restant simple à manipuler en Python.
Les valeurs sont générées dans des plages volontairement larges. La pression systolique varie entre 70 et 200 mmHg et la pression diastolique entre 40 et 130 mmHg. Ces intervalles dépassent les plages physiologiques normales afin de garantir la présence régulière de cas anormaux dans le flux généré. Cela permet de tester efficacement le module de détection d’anomalies.
La génération repose sur les bibliothèques Python Faker et random. Faker permet de produire des identités réalistes ainsi que des horodatages cohérents, tandis que random assure la variabilité des valeurs physiologiques simulées.

## 3. Kafka
Kafka joue le rôle d’intermédiaire entre le module de génération et le module d’analyse. Les messages sont publiés dans un topic nommé blood_pressure. Kafka garantit l’ordre des messages dans une partition et permet un traitement continu et fiable des données.

### 3.1 Producer
Le producer est responsable de la génération et de l’envoi des observations vers Kafka. Il crée un message au format JSON, l’encode en UTF-8, puis l’envoie au topic blood_pressure à intervalle régulier. L’intervalle d’envoi est configurable via une variable d’environnement, ce qui permet d’ajuster le débit du flux sans modifier le code.
Un mécanisme de callback permet de confirmer l’envoi des messages. Le terminal affiche le topic, la partition et l’offset, ce qui permet de vérifier que les messages sont bien stockés dans Kafka.
Le fonctionnement continu du producer simule un dispositif médical transmettant des données en temps réel. L’augmentation progressive des offsets confirme que le flux est actif et que les données sont correctement persistées dans le broker.
Le consumer s’abonne au même topic et lit les messages en continu. À chaque réception, le message est décodé puis analysé. Les règles d’analyse reposent sur des seuils médicaux classiques. Une pression systolique supérieure à 140 mmHg ou inférieure à 90 mmHg est considérée comme anormale. Une pression diastolique supérieure à 90 mmHg ou inférieure à 60 mmHg est également considérée comme anormale.
Lorsque les valeurs sortent de ces intervalles, le patient est identifié comme présentant une anomalie. Les mesures normales sont sauvegardées localement dans un fichier JSON organisé par date. Les mesures anormales sont sauvegardées localement et indexées dans Elasticsearch afin de permettre leur visualisation dans Kibana.
Cette logique de stockage différencié permet d’optimiser le système : seules les données critiques sont indexées dans le moteur de recherche, tandis que les données normales sont archivées localement.

### 3.2 Consumer
  #### Rôle du Consumer
Dans l'architecture Kafka, le consumer est le composant qui 
reçoit les messages de pressions artérielle envoyé par le Producer dans Kafka
et les traite en transmettant chaque message à la fonction `traiter_donnees()` du fichier `Stockage_traitement_données.py`
qui se charge de la détection des anomalies et du stockage. 
En effet, lorsque Consumer transmet les données sur `traiter_donnees(data)`, ce dernier va appeler `detecter_anomalies()` pour analyser les valeurs: 
   - Si normal ( en respectant les seuils definis) il sauvegarde des données dans le fichier local au format JSON nommé `patients_normaux.json`. 
   - Si anormal ( les seuils definis non respectés ) , il indexe les données dans Elasticsearch qui seront ensuite visible dans Kibana

 #### Fichier du code : `Consumer.py`

  #### Fonctionnement détaillé
1. Au démarrage, le consumer se connecte au topic Kafka `blood_pressure` (le Producer dépose les messages) sur `localhost:9092`
4. Dès qu'un message arrive, il extrait le contenu JSON  via `message.value`
5. Il appelle `traiter_donnees()` pour analyser les données du patient afin de les stocker au bon endroit

    #### Code principal
```python
consumer = KafkaConsumer(
    'blood_pressure',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    data = message.value
    traiter_donnees(data)
```

## 4. Détection des Anomalies (Awatif)

## 5. Traitement des Données (Awatif)

## 6. Elasticsearch et Kibana (Awatif)

## 7. Prérequis et Installation
Le projet nécessite Python 3.9 ou supérieur ainsi que Docker et Docker Compose pour lancer l’infrastructure distribuée. Les dépendances Python principales sont confluent-kafka pour la communication avec Kafka, faker pour la génération des données et elasticsearch pour l’indexation des anomalies.
Après avoir activé un environnement virtuel Python, les dépendances peuvent être installées via pip. L’infrastructure est ensuite lancée à l’aide du fichier docker-compose.yml, qui démarre Zookeeper, Kafka, Elasticsearch et Kibana. Une fois les conteneurs actifs, le topic blood_pressure doit être créé dans Kafka avant de démarrer les scripts Python.

## 8. Comment lancer le projet
Il faut d’abord démarrer l’infrastructure Docker afin d’initialiser Kafka, Elasticsearch et Kibana. Une fois les services opérationnels, le topic Kafka est créé.
Le producer est ensuite lancé dans un premier terminal. Il commence à générer et envoyer des messages en continu. Dans un second terminal, le consumer est lancé afin de lire les messages et d’appliquer la détection d’anomalies.
Kibana est accessible via le navigateur à l’adresse locale prévue par Docker. Après création d’un index pattern correspondant à l’index des anomalies, les données indexées peuvent être explorées et visualisées sous forme de graphiques ou de tableaux de bord.

## 9. Structure des fichiers
Le projet contient un script producer.py responsable de la génération et de l’envoi des données, ainsi qu’un script consumer.py chargé de la réception, de l’analyse et du stockage différencié des mesures. Le fichier docker-compose.yml permet de déployer l’infrastructure complète. Un dossier data contient les mesures normales et anormales sauvegardées localement. Le fichier README décrit l’architecture et les instructions d’exécution du projet.


## 10. Auteurs 
Le projet a été réalisé dans le cadre d’un travail collaboratif. La partie architecture et infrastructure comprend la génération des messages, la mise en place du producer et du consumer, ainsi que l’intégration avec Elasticsearch et Kibana. La partie analyse peut être enrichie par des méthodes statistiques ou des modèles de machine learning afin d’améliorer la détection des anomalies et l’interprétation des résultats.
