from app.core.config import db
from google.cloud import firestore

def obtener_pacientes_por_cuidador(uid_cuidador: str) -> list:
    pacientes_ref = db.collection("pacientes").where(
        filter=firestore.FieldFilter("cuidadores_asignados", "array_contains", uid_cuidador)
    )
    
    resultados = pacientes_ref.stream()
    lista_pacientes = []
    
    for doc in resultados:
        datos = doc.to_dict()
        datos["id"] = doc.id
        lista_pacientes.append(datos)
        
    return lista_pacientes

def obtener_paciente_por_id(paciente_id: str) -> dict:
    doc_ref = db.collection("pacientes").document(paciente_id)
    doc = doc_ref.get()
    
    if doc.exists:
        return doc.to_dict()
    return None