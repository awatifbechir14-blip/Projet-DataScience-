import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

from faker import Faker
from confluent_kafka import Producer

# On utilise fhir.resources pour construire une vraie ressource FHIR Observation
from fhir.resources.observation import Observation
from fhir.resources.quantity import Quantity
from fhir.resources.coding import Coding
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.reference import Reference


fake = Faker()

# Je laisse ces paramètres en variables d'environnement : pratique pour changer
# le broker / topic sans retoucher le code.
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "blood_pressure")
INTERVAL_S = float(os.getenv("INTERVAL_SECONDS", "1.0"))


def iso_now() -> str:
    """Renvoie l'heure courante en ISO 8601 (UTC)."""
    return datetime.now(timezone.utc).isoformat()


def generer_observation_fhir(patient_id: str, systolic: int, diastolic: int, timestamp: str) -> Observation:
    """
    Je construis une ressource FHIR Observation pour une pression artérielle.

    Codes LOINC :
      - 85354-9 : Blood pressure panel (pression artérielle globale)
      - 8480-6  : Systolic blood pressure
      - 8462-4  : Diastolic blood pressure
    """

    # Partie "systolique" (component[0])
    component_systolic = {
        "code": CodeableConcept(
            coding=[Coding(system="http://loinc.org", code="8480-6", display="Systolic blood pressure")]
        ),
        "valueQuantity": Quantity(
            value=systolic,
            unit="mmHg",
            system="http://unitsofmeasure.org",
            code="mm[Hg]"
        ),
    }

    # Partie "diastolique" (component[1])
    component_diastolic = {
        "code": CodeableConcept(
            coding=[Coding(system="http://loinc.org", code="8462-4", display="Diastolic blood pressure")]
        ),
        "valueQuantity": Quantity(
            value=diastolic,
            unit="mmHg",
            system="http://unitsofmeasure.org",
            code="mm[Hg]"
        ),
    }

    # Observation complète
    obs = Observation(
        resourceType="Observation",
        id=str(uuid.uuid4()),
        status="final",
        category=[
            CodeableConcept(
                coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/observation-category",
                    code="vital-signs",
                    display="Vital Signs"
                )]
            )
        ],
        code=CodeableConcept(
            coding=[Coding(system="http://loinc.org", code="85354-9", display="Blood pressure panel")]
        ),
        subject=Reference(reference=f"Patient/{patient_id}"),
        effectiveDateTime=timestamp,
        issued=timestamp,
        component=[component_systolic, component_diastolic],
    )

    return obs


def generer_message() -> dict:
    """
    Ici je génère le message final qui part dans Kafka.

    Important : je garde EXACTEMENT les champs plats attendus 
    (patient_id, name, systolic, diastolic, timestamp).

    Et j'ajoute en plus fhir_resource pour respecter :
    une Observation FHIR construite avec fhir.resources.
    """

    patient_id = fake.uuid4()[:8]
    name = fake.name()

    # Plages larges pour avoir régulièrement des anomalies
    systolic = random.randint(70, 200)
    diastolic = random.randint(40, 130)

    # Timestamp ISO 8601
    timestamp = iso_now()

    # Construction de la ressource FHIR Observation
    obs_fhir = generer_observation_fhir(patient_id, systolic, diastolic, timestamp)

    # obs_fhir.json() -> string JSON ; je le remets en dict pour l'inclure dans notre message
    fhir_as_dict = json.loads(obs_fhir.json())

    return {
        # Champs simples 
        "patient_id": patient_id,
        "name": name,
        "systolic": systolic,
        "diastolic": diastolic,
        "timestamp": timestamp,

        # Ressource FHIR complète
        "fhir_resource": fhir_as_dict
    }


def delivery_report(err, msg):
    """Callback Kafka : permet de voir si le message est bien arrivé."""
    if err is not None:
        print(f"❌ Erreur d'envoi : {err}")
    else:
        print(f"✅ Envoyé sur {msg.topic()} [{msg.partition()}] offset={msg.offset()}")


def main():
    # Je crée le producer Kafka (confluent-kafka)
    producer = Producer({"bootstrap.servers": BOOTSTRAP_SERVERS})

    print("🚀 Producer démarré")
    print(f"   broker  = {BOOTSTRAP_SERVERS}")
    print(f"   topic   = {TOPIC}")
    print(f"   interval= {INTERVAL_S} s")
    print("   Ctrl+C pour arrêter.\n")

    try:
        while True:
            # 1) Je fabrique un message (plat + FHIR)
            message = generer_message()

            # 2) Petit print pour vérifier vite fait ce qui part
            print(
                f"📨 {message['patient_id']} | SYS={message['systolic']} | "
                f"DIA={message['diastolic']} | {message['timestamp']}"
            )

            # 3) Kafka envoie des bytes -> je sérialise en JSON UTF-8
            payload = json.dumps(message).encode("utf-8")

            # poll(0) déclenche les callbacks (delivery_report)
            producer.poll(0)

            # 4) Envoi vers le topic
            producer.produce(TOPIC, payload, callback=delivery_report)

            # 5) Pause pour simuler un flux temps réel
            time.sleep(INTERVAL_S)

    except KeyboardInterrupt:
        print("\n⛔ Arrêt manuel du producer.")

    finally:
        # flush() pour être sûr que tout ce qui est en buffer est bien envoyé
        producer.flush()
        print("✔ Producer fermé proprement.")


if __name__ == "__main__":
    main()