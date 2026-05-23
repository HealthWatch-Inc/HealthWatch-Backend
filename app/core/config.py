import firebase_admin
from firebase_admin import credentials, firestore
import os

CREDENTIALS_PATH = "firebase-credentials.json" 

if not os.path.exists(CREDENTIALS_PATH):
    raise FileNotFoundError(f"Falta el archivo de credenciales en: {CREDENTIALS_PATH}")

if not firebase_admin._apps:
    cred = credentials.Certificate(CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()
print("Conexión a Firestore establecida correctamente.")