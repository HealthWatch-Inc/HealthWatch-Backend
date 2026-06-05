from app.core.config import db

def crear_medicamento(paciente_id: str, datos_medicamento: dict) -> str:
    nueva_ref = db.collection("pacientes").document(paciente_id).collection("medicamentos").document()
    nueva_ref.set(datos_medicamento)
    
    return nueva_ref.id

def obtener_medicamentos_por_paciente(paciente_id: str) -> list:
    medicamentos_ref = db.collection("pacientes").document(paciente_id).collection("medicamentos")
    docs = medicamentos_ref.where("activo", "==", True).stream()
    
    lista = []
    for doc in docs:
        datos = doc.to_dict()
        datos["id"] = doc.id
        lista.append(datos)
        
    return lista