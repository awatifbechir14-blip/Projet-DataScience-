# importation des bibliothèques nécessaires 

import json
from datetime import datetime
from elasticsearch import Elasticsearch
from Detection_anamalies import detecter_anomalies # Importation de la fonction de détection d'anomalies depuis le fichier Detection_anamalies.py

connection_elasticsearch= Elasticsearch('http://localhost:9200')


##############################################################
#  Fonction pour stocker les patients normaux en Jason
###############################################################

def stocker_patient_normal(Données_patient_normal): 
    with open("patients_normaux.json", "a") as fichier: # Ouvre le fichier "patients_normaux.json" en mode ajout ("a") pour stocker les données des patients normaux
        json.dump(Données_patient_normal, fichier) # Utilise json.dump() pour écrire les données du patient dans le fichier JSON
        fichier.write("\n") # Ajoute une nouvelle ligne après chaque enregistrement pour séparer les patients
        print(f"Normal — sauvegardé en JSON")  


###############################################################
#  Fonction pour stocker les anomalies dans Elasticsearch
###############################################################

def stocker_patient_anormal(Données_patient_anormal, anomalies):
    document = {
        "patient_id": Données_patient_anormal["patient_id"],
        "name": Données_patient_anormal["name"],
        "systolic_pressure": Données_patient_anormal["systolic"],
        "diastolic_pressure": Données_patient_anormal["diastolic"],
        "anomaly_type": ", ".join(anomalies),
        "timestamp": Données_patient_anormal["timestamp"]
    }
    
    connection_elasticsearch.index(index="blood_pressure_anomalies", body=document)
    print(f" Anormal — envoyé dans Elasticsearch : {document}")


#########################################################################
# Fonction pour traiter les données de pression artérielle
#########################################################################
def traiter_donnees(données):
    systolic = données["systolic"]
    diastolic = données["diastolic"]
    
    anomalies = detecter_anomalies(systolic, diastolic)
    
    if anomalies:
        stocker_patient_anormal(données, anomalies) 
    else:
        stocker_patient_normal(données)

