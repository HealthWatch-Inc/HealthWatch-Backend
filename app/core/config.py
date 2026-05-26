import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os

load_dotenv()
CREDENTIALS_PATH = "firebase-credentials.json" 

if not os.path.exists(CREDENTIALS_PATH):
    raise FileNotFoundError(f"Falta el archivo de credenciales en: {CREDENTIALS_PATH}")

if not firebase_admin._apps:
    cred = credentials.Certificate(CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()
print("Conexión a Firestore establecida correctamente.")

INFLUX_HOST = os.getenv("INFLUXDB3_HOST_URL")
INFLUX_TOKEN = os.getenv("INFLUXDB3_AUTH_TOKEN")
INFLUX_DATABASE = os.getenv("INFLUXDB3_DATABASE_NAME")