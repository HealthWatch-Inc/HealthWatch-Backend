# app/routers/pacientes.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import verificar_token
from app.services import pacientes_service, telemetria_service

router = APIRouter(
    prefix="/api/pacientes",
    tags=["Pacientes"]
)

@router.get("/")
def listar_mis_pacientes(usuario_actual: dict = Depends(verificar_token)):
    uid_cuidador = usuario_actual.get("uid")
    pacientes = pacientes_service.obtener_pacientes_por_cuidador(uid_cuidador)
    return {
        "status": "éxito",
        "cantidad": len(pacientes),
        "pacientes": pacientes
    }

@router.get("/{paciente_id}")
def obtener_perfil_paciente(paciente_id: str, usuario_actual: dict = Depends(verificar_token)):
    uid_cuidador = usuario_actual.get("uid")
    paciente = pacientes_service.obtener_paciente_por_id(paciente_id)
    
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Paciente no encontrado"
        )

    if uid_cuidador not in paciente.get("cuidadores_asignados", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. No estás asignado como cuidador de este paciente."
        )
    
    return {
        "status": "éxito",
        "paciente": paciente
    }

@router.get("/{paciente_id}/telemetria")
def obtener_telemetria(
    paciente_id: str, 
    limite: int = 50, 
    usuario_actual: dict = Depends(verificar_token)
):
    uid_cuidador = usuario_actual.get("uid")
    paciente = pacientes_service.obtener_paciente_por_id(paciente_id)
    
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Paciente no encontrado"
        )

    if uid_cuidador not in paciente.get("cuidadores_asignados", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. No estás asignado como cuidador de este paciente."
        )
        
    datos = telemetria_service.obtener_historial_paciente(paciente_id, limite)
    
    return {
        "status": "éxito",
        "paciente_id": paciente_id,
        "total_registros": len(datos),
        "telemetria": datos
    }