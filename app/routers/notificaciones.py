from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import db
from app.core.security import verificar_token
from app.models.usuario_models import FCMTokenUpdate
from pydantic import BaseModel
from app.services import usuarios_service
from app.services.notificaciones_service import notificar_cuidadores

router = APIRouter(
  prefix="/api/notificaciones",
  tags=["Notificaciones"]
)

class NotificationRequest(BaseModel):
  paciente_id: str

TIPOS_ALERTA = {
  "caida": {
      "titulo": "Caída detectada",
      "mensaje": "Se detectó una posible caída del paciente."
  },
  "signos": {
      "titulo": "Signos vitales alterados",
      "mensaje": "El paciente presenta signos vitales fuera del rango normal."
  },
  "emergencia": {
      "titulo": "Emergencia crítica",
      "mensaje": "Se detectó una caída junto con signos vitales anormales."
  }
}

def enviar_alerta(paciente_id: str, tipo:str):
  alerta = TIPOS_ALERTA[tipo]

  notificar_cuidadores(
    paciente_id,
    alerta["titulo"],
    alerta["mensaje"],
    tipo
  )

@router.post("/caida")
def notificar_caida(req: NotificationRequest):
  enviar_alerta(req.paciente_id, "caida")
  return {"ok": True}

@router.post("/emergencia")
def notificar_emergencia(req: NotificationRequest):
  enviar_alerta(req.paciente_id, "emergencia")
  return {"ok": True}

@router.post("/signos")
def notificar_signos(req: NotificationRequest):
  enviar_alerta(req.paciente_id, "signos")
  return {"ok": True}