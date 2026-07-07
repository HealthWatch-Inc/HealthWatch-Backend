from fastapi import APIRouter, HTTPException
import requests
from app.core.config import FIREBASE_WEB_API_KEY
from app.models.auth_models import LoginRequest

router = APIRouter(
    prefix="/api/auth",
    tags=["Autenticación (Pruebas)"]
) 

FIREBASE_WEB_API_KEY = "AIzaSyBdSZze-ATiqrtZFLpuumGYVA5qXwdhjUU" 

@router.post("/login-prueba")
def simular_login_frontend(credenciales: LoginRequest):
    """
    Login token
    """
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    
    payload = {
        "email": credenciales.email,
        "password": credenciales.password,
        "returnSecureToken": True
    }
    
    respuesta = requests.post(url, json=payload)
    datos = respuesta.json()
    
    if "error" in datos:
        raise HTTPException(
            status_code=400, 
            detail=f"Error de Firebase: {datos['error']['message']}"
        )
        
    return {
        "mensaje": "¡Login exitoso! Copia el token de abajo.",
        "uid_usuario": datos["localId"],
        "token_para_swagger": datos["idToken"]
    }

