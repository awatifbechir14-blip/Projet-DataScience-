#ce fichier est utilisé pour détecter les anomalies dans les données de pression artérielle des patients 


###############################################################################
# Fonction pour détecter les anomalies dans les données de pression artérielle
###############################################################################

def detecter_anomalies(systolic, diastolic):
    anomalies = []
    
    # Verification systolique
    if systolic > 140:
        anomalies.append("hypertension_systolique") # Si la pression systolique est supérieur à 140 mmHg, il stocke l'anomalie "hypertension_systolique" dans la liste anomalies
    elif systolic < 90: 
        anomalies.append("hypotension_systolique") # Si la pression systolique est inférieure à 90 mmHg, il stocke l'anomalie "hypotension_systolique" dans la liste anomalies
    
    # Vérification diastolique
    if diastolic > 90:
        anomalies.append("hypertension_diastolique") # Si la pression diastolique est supérieure à 90 mmHg, il stocke l'anomalie "hypertension_diastolique" dans la liste anomalies
    elif diastolic < 60:
        anomalies.append("hypotension_diastolique") # Si la pression diastolique est inférieure à 60 mmHg, il stocke l'anomalie "hypotension_diastolique" dans la liste anomalies

    return anomalies

