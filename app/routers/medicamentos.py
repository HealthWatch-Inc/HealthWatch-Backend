from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
from app.core.security import verificar_token 
from app.services import medicamentos_service

router = APIRouter(
    prefix="/api/medicamentos",
    tags=["Medicamentos"]
)

class MedicamentoCreate(BaseModel):
    nombre: str
    horas: List[str]
    frecuencia: str

@router.post("/{paciente_id}")
def agregar_medicamento(
    paciente_id: str, 
    medicamento: MedicamentoCreate,
    usuario_actual = Depends(verificar_token)
):
    doc_data = {
        "nombre": medicamento.nombre,
        "horas": medicamento.horas,
        "frecuencia": medicamento.frecuencia,
        "activo": True
    }
    
    try:
        med_id = medicamentos_service.crear_medicamento(paciente_id, doc_data)
        
        return {
            "mensaje": "Medicamento programado con éxito", 
            "id_medicamento": med_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error interno al guardar en base de datos: {str(e)}"
        )

@router.get("/{paciente_id}")
def listar_medicamentos(
    paciente_id: str,
    usuario_actual = Depends(verificar_token)
):
    try:
        lista = medicamentos_service.obtener_medicamentos_por_paciente(paciente_id)
        return lista
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))