from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import db
from app.core.security import verificar_token
from app.models.usuario_models import FCMTokenUpdate

router = APIRouter(
    prefix="/api/usuarios",
    tags=["Usuarios"]
)

class ExpoTokenUpdate(BaseModel):
    expo_token: str

@router.put("/expo-token")
def actualizar_token_celular(
    datos: ExpoTokenUpdate, 
    usuario_actual = Depends(verificar_token)
):
    try:
        uid_cuidador = usuario_actual.get("uid")
        
        db.collection("usuarios").document(uid_cuidador).set({
            "expo_token": datos.expo_token
        }, merge=True)
        
        return {"mensaje": "Token de notificaciones actualizado correctamente."}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error interno al guardar el token: {str(e)}"
        )