# Système de Surveillance des Données de Pression Artérielle patient avec Kafka, Elasticsearch et Kibana

## 1. Description générale (Awatif + Nabiha )
Ce projet vise à utiliser une architecture Big Data afin de surveiller les données de pressions artérielle des patients en temps réel. Il permet de detecter automatiquement et rapidement les anomalies, les indexe dans Elasticsearch pour les visualiser dans Kibana.

## 2. Génération des Messages FHIR (Nabiha)

## 3. Kafka
### 3.1 Producer (Nabiha)
### 3.2 Consumer (Awatif)
  #### Rôle du Consumer
Dans l'architecture Kafka, le consumer est le composant qui 
reçoit les messages de pressions artérielle envoyé par le Producer dans Kafka
et les traite en transmettant chaque message à la fonction `traiter_donnees()` du fichier `Stockage_traitement_données.py`
qui se charge de la détection des anomalies et du stockage. 
En effet, lorsque Consumer transmet les données sur `traiter_donnees(data)`, ce dernier va :
   - Appeler `detecter_anomalies()` pour analyser les valeurs
   - Si normal ( en respectant les seuils defini) il sauvegarde des données dans le fichier local au format JSON nommé `patients_normaux.json`. 
   - Si anormal, il indexe les données dans Elasticsearch qui seront ensuite visible dans Kibana

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

## 7. Prérequis et Installation (ensemble)

## 8. Comment lancer le projet (ensemble)

## 9. Structure des fichiers (ensemble)

## 10. Auteurs (ensemble)
