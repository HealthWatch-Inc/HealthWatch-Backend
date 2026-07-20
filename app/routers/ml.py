from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List
from app.services.ml_services import predecir_ventana
from app.services.ml_fall_service import predecir_caida

router = APIRouter(
    prefix="/api/ml",
    tags=["Machine Learning"]
)

# ============================================
# Modelos Pydantic para validación de entrada
# ============================================

class ModuloAPredictionRequest(BaseModel):
    """Datos biométricos para clasificación de salud (Módulo A)"""
    hr_vals: List[float] = Field(..., description="Lista de 30 valores de frecuencia cardíaca (BPM)")
    spo2_vals: List[float] = Field(..., description="Lista de 30 valores de saturación de oxígeno (%)")
    temp_vals: List[float] = Field(..., description="Lista de 30 valores de temperatura corporal (°C)")
    
    class Config:
        example = {
            "hr_vals": [72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101],
            "spo2_vals": [98, 98, 98, 97, 97, 97, 96, 96, 96, 95, 95, 95, 94, 94, 94, 93, 93, 93, 92, 92, 92, 91, 91, 91, 90, 90, 90, 89, 89, 89],
            "temp_vals": [36.5, 36.5, 36.6, 36.6, 36.7, 36.7, 36.8, 36.8, 36.9, 36.9, 37.0, 37.0, 37.1, 37.1, 37.2, 37.2, 37.3, 37.3, 37.4, 37.4, 37.5, 37.5, 37.6, 37.6, 37.7, 37.7, 37.8, 37.8, 37.9, 37.9]
        }


class ModuloBPredictionRequest(BaseModel):
    """Datos IMU para detección de caídas (Módulo B)"""
    ax_vals: List[float] = Field(..., description="Lista de 20 valores de aceleración en eje X (m/s²)")
    ay_vals: List[float] = Field(..., description="Lista de 20 valores de aceleración en eje Y (m/s²)")
    az_vals: List[float] = Field(..., description="Lista de 20 valores de aceleración en eje Z (m/s²)")
    gx_vals: List[float] = Field(..., description="Lista de 20 valores de velocidad angular en eje X (rad/s)")
    gy_vals: List[float] = Field(..., description="Lista de 20 valores de velocidad angular en eje Y (rad/s)")
    gz_vals: List[float] = Field(..., description="Lista de 20 valores de velocidad angular en eje Z (rad/s)")
    
    class Config:
        example = {
            "ax_vals": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0],
            "ay_vals": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0],
            "az_vals": [9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8],
            "gx_vals": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.2],
            "gy_vals": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.2],
            "gz_vals": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.2]
        }


# ============================================
# Endpoint Módulo A - Clasificación de Salud
# ============================================

@router.post("/modulo-a/prediccion")
def predecir_salud(datos: ModuloAPredictionRequest):
    """
    Predice la clasificación de salud basada en datos biométricos.
    
    **Entrada:**
    - hr_vals: Lista exacta de 30 valores de frecuencia cardíaca
    - spo2_vals: Lista exacta de 30 valores de saturación de oxígeno
    - temp_vals: Lista exacta de 30 valores de temperatura corporal
    
    **Salida:**
    - clasificacion: "okay", "warning" o "bad"
    - probabilidades: Probabilidades para cada clase
    
    **Casos de error:**
    - 400: Número incorrecto de valores en las listas
    - 500: Error al ejecutar el modelo
    """
    try:
        # Validar longitud de listas
        if len(datos.hr_vals) != 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Se requieren exactamente 30 valores de HR, se recibieron {len(datos.hr_vals)}"
            )
        if len(datos.spo2_vals) != 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Se requieren exactamente 30 valores de SpO2, se recibieron {len(datos.spo2_vals)}"
            )
        if len(datos.temp_vals) != 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Se requieren exactamente 30 valores de temperatura, se recibieron {len(datos.temp_vals)}"
            )
        
        # Realizar predicción
        clasificacion, probabilidades = predecir_ventana(
            datos.hr_vals,
            datos.spo2_vals,
            datos.temp_vals
        )
        
        return {
            "status": "éxito",
            "modulo": "A",
            "clasificacion": clasificacion,
            "probabilidades": probabilidades
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ejecutar predicción del Módulo A: {str(e)}"
        )


# ============================================
# Endpoint Módulo B - Detección de Caídas
# ============================================

@router.post("/modulo-b/prediccion")
def predecir_caida_endpoint(datos: ModuloBPredictionRequest):
    """
    Predice la probabilidad de caída basada en datos IMU.
    
    **Entrada:**
    - ax_vals, ay_vals, az_vals: Listas exactas de 20 valores de aceleración
    - gx_vals, gy_vals, gz_vals: Listas exactas de 20 valores de velocidad angular
    
    **Salida:**
    - probabilidad_caida: Probabilidad de caída (0.0 a 1.0)
    - es_caida: Boolean indicando si se detectó caída
    
    **Casos de error:**
    - 400: Número incorrecto de valores en las listas
    - 500: Error al ejecutar el modelo
    """
    try:
        # Validar longitud de listas
        lista_imu = {
            "ax": datos.ax_vals,
            "ay": datos.ay_vals,
            "az": datos.az_vals,
            "gx": datos.gx_vals,
            "gy": datos.gy_vals,
            "gz": datos.gz_vals
        }
        
        for nombre, valores in lista_imu.items():
            if len(valores) != 20:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Se requieren exactamente 20 valores de {nombre}, se recibieron {len(valores)}"
                )
        
        # Realizar predicción
        probabilidad, es_caida = predecir_caida(
            datos.ax_vals,
            datos.ay_vals,
            datos.az_vals,
            datos.gx_vals,
            datos.gy_vals,
            datos.gz_vals
        )
        
        return {
            "status": "éxito",
            "modulo": "B",
            "probabilidad_caida": probabilidad,
            "es_caida": es_caida
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ejecutar predicción del Módulo B: {str(e)}"
        )
