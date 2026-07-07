from app.core.config import db

def crear_contacto(paciente_id: str, datos_contacto: dict) -> str:
    nueva_ref = db.collection("pacientes").document(paciente_id).collection("contactos").document()
    nueva_ref.set(datos_contacto)
    return nueva_ref.id

def obtener_contactos(paciente_id: str) -> list:
    docs = db.collection("pacientes").document(paciente_id).collection("contactos").stream()
    
    lista_contactos = []
    for doc in docs:
        datos = doc.to_dict()
        datos["id"] = doc.id
        lista_contactos.append(datos)
        
    return lista_contactos

def actualizar_contacto(paciente_id: str, contacto_id: str, datos_actualizados: dict) -> bool:
    doc_ref = db.collection("pacientes").document(paciente_id).collection("contactos").document(contacto_id)
    doc_ref.update(datos_actualizados)
    return True

def eliminar_contacto(paciente_id: str, contacto_id: str) -> bool:
    doc_ref = db.collection("pacientes").document(paciente_id).collection("contactos").document(contacto_id)
    doc_ref.delete()
    return True