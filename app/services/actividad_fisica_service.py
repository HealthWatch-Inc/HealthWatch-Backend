from app.core.config import db

def guardar_actividad_fisica(paciente_id: str, datos_objetivo: dict) -> bool:
    doc_ref = db.collection("pacientes").document(paciente_id).collection("objetivos").document("actividad_fisica")
    
    doc_ref.set(datos_objetivo, merge=True)
    return True

def obtener_objetivo_fisico(paciente_id: str) -> dict:
    doc_ref = db.collection("pacientes").document(paciente_id).collection("objetivos").document("actividad_fisica").get()
    
    if doc_ref.exists:
        return doc_ref.to_dict()

    return {"pasos_diarios": 0}

def eliminar_actividad_fisica(paciente_id: str) -> bool:
    doc_ref = db.collection("pacientes").document(paciente_id).collection("objetivos").document("actividad_fisica")

    doc_ref.delete()
    return True