# seed_db.py
import firebase_admin
from firebase_admin import credentials, firestore

# Inicializar Firebase
cred = credentials.Certificate("firebase-credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ⚠️ REMPLAZA ESTO CON TU UID REAL DE SWAGGER/FIREBASE AUTH
MI_UID_REAL = "GVVhi1xpSVc9MpVO5gqQ0GcI6mH2" 
UID_DE_OTRO_CUIDADOR = "rs50QcXoevTE7fUXit2q6EetpNy2"

def crear_datos_prueba():
    print("🚀 Insertando pacientes de prueba en Cloud Firestore...")

    # 1. Paciente asignado a TI (Debes poder verlo)
    db.collection("pacientes").document("paciente_autorizado_1").set({
        "nombre_completo": "Ana María Gómez",
        "edad": 74,
        "bateria_actual": 92,
        "cuidadores_asignados": [MI_UID_REAL] # <--- Estás autorizado
    })

    # 2. Otro paciente asignado a TI
    db.collection("pacientes").document("paciente_autorizado_2").set({
        "nombre_completo": "Carlos Mendoza",
        "edad": 81,
        "bateria_actual": 15,
        "cuidadores_asignados": [MI_UID_REAL, "otro_enfermero_id"] # <--- Compartido
    })

    # 3. Paciente de OTRO cuidador (Este debería ser invisible para ti)
    db.collection("pacientes").document("paciente_bloqueado_3").set({
        "nombre_completo": "Héctor Rodríguez",
        "edad": 68,
        "bateria_actual": 88,
        "cuidadores_asignados": [UID_DE_OTRO_CUIDADOR] # <--- NO estás aquí
    })

    print("✅ Datos inyectados con éxito. Ya puedes revisar tu consola web de Firestore.")

if __name__ == "__main__":
    crear_datos_prueba()