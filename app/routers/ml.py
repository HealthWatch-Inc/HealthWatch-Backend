from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.services.ml_services import predecir_ventana
from app.services.ml_fall_service import predecir_caida

router = APIRouter(
    prefix="/api/ml",
    tags=["Machine Learning"]
)

# ============================================
# Modelos Pydantic para validación de entrada
# ============================================

class BiometricData(BaseModel):
    """Estructura de un dato biométrico individual del dispositivo"""
    id_patient: str
    id_device: str
    heart_rate: float
    spo2: float
    tenp: float  # temperatura (nota: viene con typo en el nombre desde n8n)
    ax: Optional[float] = None
    ay: Optional[float] = None
    az: Optional[float] = None
    gx: Optional[float] = None
    gy: Optional[float] = None
    gz: Optional[float] = None
    rss1: Optional[float] = None
    battery: Optional[float] = None
    
    class Config:
        example = {
            "id_patient": "adulto_mayor_test",
            "id_device": "dispositivo_reloj_01",
            "ax": 0.053,
            "ay": 0.193,
            "az": 9.872,
            "gx": 0.004,
            "gy": 0.0092,
            "gz": 0.0062,
            "tenp": 36.2,
            "heart_rate": 71.5,
            "spo2": 99,
            "rss1": -63,
            "battery": 100
        }


class ModuloAPredictionRequestN8N(BaseModel):
    """Datos biométricos para clasificación de salud (Módulo A) desde n8n"""
    datos: List[BiometricData] = Field(..., description="Lista de datos biométricos (30+ recomendado)")
    
    class Config:
        example = {
            "datos": [
                {
                    "id_patient": "adulto_mayor_test",
                    "id_device": "dispositivo_reloj_01",
                    "heart_rate": 71.5,
                    "spo2": 99,
                    "tenp": 36.2,
                    "ax": 0.053,
                    "ay": 0.193,
                    "az": 9.872,
                    "gx": 0.004,
                    "gy": 0.0092,
                    "gz": 0.0062,
                    "rss1": -63,
                    "battery": 100
                }
            ]
        }


class ModuloBPredictionRequestN8N(BaseModel):
    """Datos IMU para detección de caídas (Módulo B) desde n8n"""
    datos: List[BiometricData] = Field(..., description="Lista de datos IMU (20+ recomendado)")
    
    class Config:
        example = {
            "datos": [
                {
                    "id_patient": "adulto_mayor_test",
                    "id_device": "dispositivo_reloj_01",
                    "heart_rate": 71.5,
                    "spo2": 99,
                    "tenp": 36.2,
                    "ax": 0.053,
                    "ay": 0.193,
                    "az": 9.872,
                    "gx": 0.004,
                    "gy": 0.0092,
                    "gz": 0.0062,
                    "rss1": -63,
                    "battery": 100
                }
            ]
        }


# Modelo alternativo para compatibilidad con formato anterior
class ModuloAPredictionRequest(BaseModel):
    """Datos biométricos para clasificación de salud (Módulo A) - formato directo"""
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
    """Datos IMU para detección de caídas (Módulo B) - formato directo"""
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
# Endpoint Módulo A - Clasificación de Salud (desde n8n)
# ============================================

@router.post("/modulo-a/prediccion/n8n")
def predecir_salud_n8n(datos_request: ModuloAPredictionRequestN8N):
    """
    Predice la clasificación de salud desde datos de n8n.
    
    Acepta un array de datos biométricos del dispositivo y extrae los campos necesarios:
    - heart_rate: frecuencia cardíaca
    - spo2: saturación de oxígeno
    - tenp: temperatura corporal
    
    **Entrada:**
    - datos: Lista de objetos biométricos (usar últimos 30 valores)
    
    **Salida:**
    - clasificacion: "okay", "warning" o "bad"
    - probabilidades: Probabilidades para cada clase
    - paciente_id: ID del paciente procesado
    - dispositivo_id: ID del dispositivo
    
    **Casos de error:**
    - 400: Número incorrecto de valores o campos faltantes
    - 500: Error al ejecutar el modelo
    """
    try:
        if len(datos_request.datos) < 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Se requieren al menos 30 lecturas, se recibieron {len(datos_request.datos)}"
            )
        
        # Usar los últimos 30 datos
        datos_ventana = datos_request.datos[-30:]
        
        # Validar que todos los datos tengan los campos necesarios
        for dato in datos_ventana:
            if dato.heart_rate is None or dato.spo2 is None or dato.tenp is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Faltan campos necesarios: heart_rate, spo2, o tenp"
                )
        
        # Extraer las listas de valores
        hr_vals = [float(d.heart_rate) for d in datos_ventana]
        spo2_vals = [float(d.spo2) for d in datos_ventana]
        temp_vals = [float(d.tenp) for d in datos_ventana]
        
        # Obtener IDs del primer dato (mismo paciente/dispositivo)
        paciente_id = datos_ventana[0].id_patient
        dispositivo_id = datos_ventana[0].id_device
        
        # Realizar predicción
        clasificacion, probabilidades = predecir_ventana(hr_vals, spo2_vals, temp_vals)
        
        return {
            "status": "éxito",
            "modulo": "A",
            "paciente_id": paciente_id,
            "dispositivo_id": dispositivo_id,
            "clasificacion": clasificacion,
            "probabilidades": probabilidades,
            "datos_procesados": len(datos_ventana)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ejecutar predicción del Módulo A: {str(e)}"
        )


# ============================================
# Endpoint Módulo B - Detección de Caídas (desde n8n)
# ============================================

@router.post("/modulo-b/prediccion/n8n")
def predecir_caida_n8n_endpoint(datos_request: ModuloBPredictionRequestN8N):
    """
    Predice la probabilidad de caída desde datos IMU de n8n.
    
    Acepta un array de datos IMU del dispositivo y extrae los campos necesarios:
    - ax, ay, az: aceleración en tres ejes
    - gx, gy, gz: velocidad angular en tres ejes
    
    **Entrada:**
    - datos: Lista de objetos IMU (usar últimos 20 valores)
    
    **Salida:**
    - probabilidad_caida: Probabilidad de caída (0.0 a 1.0)
    - es_caida: Boolean indicando si se detectó caída
    - paciente_id: ID del paciente procesado
    - dispositivo_id: ID del dispositivo
    
    **Casos de error:**
    - 400: Número incorrecto de valores o campos faltantes
    - 500: Error al ejecutar el modelo
    """
    try:
        if len(datos_request.datos) < 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Se requieren al menos 20 lecturas, se recibieron {len(datos_request.datos)}"
            )
        
        # Usar los últimos 20 datos
        datos_ventana = datos_request.datos[-20:]
        
        # Validar que todos los datos tengan los campos IMU necesarios
        for dato in datos_ventana:
            if (dato.ax is None or dato.ay is None or dato.az is None or
                dato.gx is None or dato.gy is None or dato.gz is None):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Faltan campos IMU necesarios: ax, ay, az, gx, gy, gz"
                )
        
        # Extraer las listas de valores
        ax_vals = [float(d.ax) for d in datos_ventana]
        ay_vals = [float(d.ay) for d in datos_ventana]
        az_vals = [float(d.az) for d in datos_ventana]
        gx_vals = [float(d.gx) for d in datos_ventana]
        gy_vals = [float(d.gy) for d in datos_ventana]
        gz_vals = [float(d.gz) for d in datos_ventana]
        
        # Obtener IDs del primer dato (mismo paciente/dispositivo)
        paciente_id = datos_ventana[0].id_patient
        dispositivo_id = datos_ventana[0].id_device
        
        # Realizar predicción
        probabilidad, es_caida = predecir_caida(ax_vals, ay_vals, az_vals, gx_vals, gy_vals, gz_vals)
        
        return {
            "status": "éxito",
            "modulo": "B",
            "paciente_id": paciente_id,
            "dispositivo_id": dispositivo_id,
            "probabilidad_caida": probabilidad,
            "es_caida": es_caida,
            "datos_procesados": len(datos_ventana)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ejecutar predicción del Módulo B: {str(e)}"
        )


# ============================================
# Endpoint Módulo A - Clasificación de Salud (formato directo legacy)
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
# Endpoint Módulo B - Detección de Caídas (formato directo legacy)
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
