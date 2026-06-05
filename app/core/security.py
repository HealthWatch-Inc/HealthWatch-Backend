from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

security = HTTPBearer()

def verificar_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_recibido = credentials.credentials
    
    try:
        # 💡 Añadimos clock_skew_seconds para tolerar desfases de hasta 10 segundos
        token_decodificado = auth.verify_id_token(token_recibido, clock_skew_seconds=10)
        logger.info(f"✅ Token válido para usuario: {token_decodificado.get('email')}")
        return token_decodificado
        
    except Exception as e:
        logger.error(f"❌ Error de autenticación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Acceso denegado. Token inválido o expirado. Detalle: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )