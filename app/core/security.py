from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

security = HTTPBearer()

def verificar_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_recibido = credentials.credentials
    
    try:
        # Firebase descifra el token y valida
        token_decodificado = auth.verify_id_token(token_recibido)
        
        return token_decodificado
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Acceso denegado. Detalle: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )