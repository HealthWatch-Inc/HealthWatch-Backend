from app.core.config import db

def actualizar_token(uid: str, token: str) -> bool:
    db.collection("usuarios").document(uid).set({
        "expo_token": token
    }, merge=True)

    return True

def obtener_perfil(uid: str) -> dict | None:
    doc_ref = db.collection("usuarios").document(uid)
    doc = doc_ref.get()
    
    if doc.exists:
        return doc.to_dict()
    return None

def actualizar_telefono(uid: str, telefono: str) -> bool:
    db.collection("usuarios").document(uid).set({
        "telefono": telefono
    }, merge=True)
    return True