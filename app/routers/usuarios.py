from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import db
from app.core.security import verificar_token
from app.models.usuario_models import FCMTokenUpdate
from pydantic import BaseModel
from app.services import usuarios_service

router = APIRouter(
    prefix="/api/usuarios",
    tags=["Usuarios"]
)

class ExpoTokenUpdate(BaseModel):
    expo_token: str

class TelefonoUpdate(BaseModel):
    telefono: str

@router.put("/expo-token")
def actualizar_token_celular(datos: ExpoTokenUpdate, usuario_actual: dict = Depends(verificar_token)):
    uid = usuario_actual.get("uid")
    try:
        usuarios_service.actualizar_token(uid, datos.expo_token)
        return {"mensaje": "Token de notificaciones actualizado correctamente."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error interno al guardar el token: {str(e)}"
        )

@router.get("/me")
def obtener_mi_perfil(usuario_actual: dict = Depends(verificar_token)):
    uid = usuario_actual.get("uid")
    perfil = usuarios_service.obtener_perfil(uid)
    correo_auth = usuario_actual.get("email", "")
    
    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="El perfil del usuario no existe en la base de datos."
        )
        
    return {
        "uid": uid,
        "nombre_completo": perfil.get("nombre_completo", ""),
        "correo": correo_auth,
        "rol": perfil.get("rol", "CUIDADOR"),
        "telefono": perfil.get("telefono", "")
    }

@router.put("/telefono")
def actualizar_telefono_usuario(datos: TelefonoUpdate, usuario_actual: dict = Depends(verificar_token)):
    uid = usuario_actual.get("uid")
    try:
        usuarios_service.actualizar_telefono(uid, datos.telefono)
        return {"mensaje": "Teléfono actualizado correctamente."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error interno al actualizar el teléfono: {str(e)}"
        )