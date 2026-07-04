from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import verificar_token
from app.models.actividad_models import ObjetivoActividad
from app.services import actividad_fisica_service

router = APIRouter(
    prefix="/api/actividad-fisica",
    tags=["Objetivos"]
)


@router.put("/{paciente_id}")
def actualizar_objetivo(
    paciente_id: str,
    objetivo: ObjetivoActividad,
    usuario_actual=Depends(verificar_token)
):
    try:
        doc_data = {"pasos_diarios": objetivo.pasos_diarios}
        actividad_fisica_service.guardar_actividad_fisica(paciente_id, doc_data)
        return {"mensaje": "Objetivo de pasos actualizado con éxito"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar el objetivo: {str(e)}"
        )


@router.get("/{paciente_id}")
def obtener_objetivo(
    paciente_id: str,
    usuario_actual=Depends(verificar_token)
):
    try:
        datos = actividad_fisica_service.obtener_objetivo_fisico(paciente_id)
        return datos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{paciente_id}")
def borrar_objetivo(
    paciente_id: str,
    usuario_actual=Depends(verificar_token)
):
    try:
        actividad_fisica_service.eliminar_actividad_fisica(paciente_id)
        return {"mensaje": "Objetivo de pasos eliminado con éxito"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar el objetivo: {str(e)}"
        )
