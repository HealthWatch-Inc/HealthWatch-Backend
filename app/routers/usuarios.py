from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.config import db
from app.core.security import verificar_token

router = APIRouter(
    prefix="/api/usuarios",
    tags=["Usuarios"]
)

class FCMTokenUpdate(BaseModel):
    fcm_token: str

@router.put("/fcm-token")
def actualizar_token_celular(
    datos: FCMTokenUpdate, 
    usuario_actual = Depends(verificar_token)
):
    try:
        uid_cuidador = usuario_actual.get("uid")
        
        db.collection("usuarios").document(uid_cuidador).set({
            "fcm_token_celular": datos.fcm_token
        }, merge=True)
        
        return {"mensaje": "Token de notificaciones actualizado correctamente."}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error interno al guardar el token: {str(e)}"
        )