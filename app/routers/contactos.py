from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.security import verificar_token
from app.services import contactos_service

router = APIRouter(
    prefix="/api/contactos",
    tags=["Contactos"]
)

class ContactoCreate(BaseModel):
    name: str
    phone: str
    relation: str

@router.post("/{paciente_id}")
def agregar_contacto(
    paciente_id: str, 
    contacto: ContactoCreate,
    usuario_actual = Depends(verificar_token)
):
    try:
        doc_data = {
            "name": contacto.name,
            "phone": contacto.phone,
            "relation": contacto.relation
        }
        contacto_id = contactos_service.crear_contacto(paciente_id, doc_data)
        return {"mensaje": "Contacto creado", "id": contacto_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{paciente_id}")
def listar_contactos(
    paciente_id: str,
    usuario_actual = Depends(verificar_token)
):
    try:
        contactos = contactos_service.obtener_contactos(paciente_id)
        return contactos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{paciente_id}/{contacto_id}")
def editar_contacto(
    paciente_id: str,
    contacto_id: str,
    contacto: ContactoCreate,
    usuario_actual = Depends(verificar_token)
):
    try:
        doc_data = {
            "name": contacto.name,
            "phone": contacto.phone,
            "relation": contacto.relation
        }
        contactos_service.actualizar_contacto(paciente_id, contacto_id, doc_data)
        return {"mensaje": "Contacto actualizado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{paciente_id}/{contacto_id}")
def borrar_contacto(
    paciente_id: str,
    contacto_id: str,
    usuario_actual = Depends(verificar_token)
):
    try:
        contactos_service.eliminar_contacto(paciente_id, contacto_id)
        return {"mensaje": "Contacto eliminado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))