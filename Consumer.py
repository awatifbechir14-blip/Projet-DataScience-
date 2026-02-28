# consumer permet de lire et des stockés les données fournis par ""producer" via kafka
import json 
from kafka import KafkaConsumer
from Stockage_traitement_données import traiter_donnees # Importation de la fonction de traitement des données depuis le fichier Stockage_traitement_données.py
# Connexion à Kafka
consumer = KafkaConsumer(
    'blood_pressure', 
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')))
print("Consumer démarré... En attente de messages dans Kafka")
for message in consumer:
    data = message.value
    print(f"Reçu : {data}")
    try:
        traiter_donnees(data)
    except Exception as e:
        print(f"ERREUR : {e}")
