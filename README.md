# Système de Surveillance des Données de Pression Artérielle patient avec Kafka, Elasticsearch et Kibana

## 1. Description générale
Ce projet vise à utiliser une architecture Big Data afin de surveiller les données de pressions artérielle des patients en temps réel. Il permet de detecter automatiquement et rapidement les anomalies telles que l’hypertension ou l’hypotension puis les indexe dans Elasticsearch  pour les visualiser dans Kibana.

Le système repose sur un pipeline de streaming utilisant Apache Kafka comme intermédiaire entre producer qui gènere des données  et consumer qui traite ces données.
 
**L’architecture suit le flux logique suivant :**
Producer Python envoie les données dans Topic Kafka `blood_pressure` puis le consummer Python lis ces données afin de classer : 
• Les données normales sont archivées localement au format JSON.
• Les données anormales sont indéxées dans Elasticsearch (anomalies) et visualiser sur Kibana

## 2. Génération des Messages FHIR 
La génération des données est inspirée du standard FHIR (Fast Healthcare Interoperability Resources), et plus précisément de la ressource Observation utilisée pour représenter des mesures cliniques.

Afin de simplifier le traitement côté consumer, un format JSON allégé a été retenu. Chaque message contient :

* un identifiant court de patient
* un nom généré aléatoirement
* une valeur de pression systolique
* une valeur de pression diastolique
* un horodatage au format ISO 8601

Exemple de message généré :

```json
{
  "patient_id": "a3f2c1d8",
  "name": "Marie Dupont",
  "systolic": 158,
  "diastolic": 95,
  "timestamp": "2024-03-15T10:23:45"
}
```

Les valeurs sont volontairement générées dans des plages larges :

* systolique : 70 à 200 mmHg
* diastolique : 40 à 130 mmHg

Ces intervalles dépassent les seuils physiologiques normaux afin de produire régulièrement des cas anormaux, ce qui permet de tester efficacement le module d’analyse.

La génération repose sur :

* `Faker` pour créer des identités et des horodatages réalistes
* `random` pour simuler les valeurs de pression
## 3. Kafka
Apache Kafka joue le rôle de broker de messages. Il permet de transporter les observations du producer vers le consumer de manière fiable et ordonnée.

Les messages sont publiés dans un topic nommé `blood_pressure`. Kafka assure la persistance des messages et garantit leur ordre dans chaque partition.


### 3.1 Producer
Le fichier `producer.py` est responsable de la génération et de l’envoi des messages.

Le producer :

* récupère ses paramètres via des variables d’environnement
* génère un message JSON
* encode le message en UTF-8
* envoie le message au topic Kafka
* affiche un callback de confirmation (topic, partition, offset)

L’intervalle d’envoi est configurable via la variable `INTERVAL_SECONDS`, ce qui permet de simuler un flux plus ou moins rapide.

L’augmentation progressive des offsets affichés dans le terminal confirme que les messages sont correctement stockés dans Kafka.
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

### Rôle de détection des anomalies 
Le code realisé dans cette partie permet d'analyser les valeurs de pression artérielle de chaque patient 
reçu depuis Kafka et déterminer si elles sont normales ou anormales en les comparant aux seuils médicaux définis.

### Fichier : `Detection_anamalies.py`

### Seuils médicaux utilisés et types d'anomalies détectées

**Pression systolique :**
- Valeur normale : entre 90 mmHg et 140 mmHg
- Anormale Hypertension systolique : supérieure à 140 mmHg
- Anormale Hypotension systolique : inférieure à 90 mmHg

**Pression diastolique (valeur basse) :**
- Valeur normale : entre 60 mmHg et 90 mmHg
- Anormale Hypertension diastolique : supérieure à 90 mmHg
- Anormale Hypotension diastolique : inférieure à 60 mmHg

### Fonctionnement
1. La fonction `detecter_anomalies()` reçoit les valeurs 
   systolique et diastolique du patient
2. Elle compare chaque valeur avec les seuils médicaux fixés 
3. Elle retourne une liste d'anomalies détectées :
   - Si la liste est vide cela signifie que patient est normal
   - Si la liste est non vide cela signifie que le patient est anormal et  le(s) type(s) d'anomalie(s) sont alors précisés. 

### Code
```python
def detecter_anomalies(systolic, diastolic):
    anomalies = []
    
    # Verification systolique
    if systolic > 140:
        anomalies.append("hypertension_systolique")
    elif systolic < 90: 
        anomalies.append("hypotension_systolique") 
    
    # Vérification diastolique
    if diastolic > 90:
        anomalies.append("hypertension_diastolique") 
    elif diastolic < 60:
        anomalies.append("hypotension_diastolique") 

    return anomalies
```
`anomalies = []` : la liste qui sert à stocker les anomalies 
`anomalies.append("hypertension_systolique")` :  Si la pression systolique est supérieur à 140 mmHg, 
il stocke l'anomalie "hypertension_systolique" dans la liste anomalies
`anomalies.append("hypotension_systolique")` : Si la pression systolique est inférieure à 90 mmHg, 
il stocke l'anomalie "hypotension_systolique" dans la liste anomalies    
`anomalies.append("hypertension_diastolique")`: Si la pression diastolique est supérieure à 90 mmHg, 
il stocke l'anomalie "hypertension_diastolique" dans la liste anomalies
`anomalies.append("hypotension_diastolique")` : Si la pression diastolique est inférieure à 60 mmHg,
il stocke l'anomalie "hypotension_diastolique" dans la liste anomalies
## 5. Traitement des Données (Awatif)

## 6. Elasticsearch et Kibana (Awatif)

## 7. Prérequis et Installation
Le projet nécessite :

* Python 3.9 ou supérieur
* Docker et Docker Compose
* pip

Les dépendances Python sont :

* confluent-kafka
* faker
* elasticsearch

Après activation d’un environnement virtuel Python, les dépendances peuvent être installées avec :

```bash
pip install confluent-kafka faker elasticsearch
```

L’infrastructure complète (Zookeeper, Kafka, Elasticsearch, Kibana) est lancée via :

```bash
docker-compose up -d
```

Une fois les conteneurs actifs, le topic Kafka `blood_pressure` doit être créé avant d’exécuter les scripts Python.

## 8. Comment lancer le projet
1. Démarrer l’infrastructure Docker.
2. Créer le topic Kafka `blood_pressure`.
3. Lancer le producer dans un premier terminal :

```bash
python producer.py
```

4. Lancer le consumer dans un second terminal :

```bash
python consumer.py
```

5. Accéder à Kibana via le navigateur à l’adresse configurée par Docker (généralement [http://localhost:5601](http://localhost:5601)).
6. Créer un index pattern correspondant à `blood_pressure_anomalies` afin de visualiser les anomalies.

## 9. Structure des fichiers
Le projet comprend :

* `producer.py` : génération et envoi des messages
* `consumer.py` : réception, analyse et stockage
* `analysis_module.py` : logique d’analyse développée séparément
* `docker-compose.yml` : déploiement de l’infrastructure
* dossier `data/` : stockage local des mesures normales et anormales
* `README.md` : documentation du projet

## 10. Auteurs 
Le projet a été réalisé dans le cadre d’un travail collaboratif. La partie architecture et infrastructure comprend la génération des messages, la mise en place du producer et du consumer, ainsi que l’intégration avec Elasticsearch et Kibana. La partie analyse peut être enrichie par des méthodes statistiques ou des modèles de machine learning afin d’améliorer la détection des anomalies et l’interprétation des résultats.
