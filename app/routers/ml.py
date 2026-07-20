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
# Modelos para el formato N8N completo (txt.txt)
# ============================================

class MQTTMessageN8N(BaseModel):
    """Estructura del campo 'message' dentro de cada item del payload MQTT enviado por N8N"""
    id_patient: str
    id_device: str
    ax: Optional[float] = None
    ay: Optional[float] = None
    az: Optional[float] = None
    gx: Optional[float] = None
    gy: Optional[float] = None
    gz: Optional[float] = None
    temp: Optional[float] = None   # Temperatura - nombre correcto
    tenp: Optional[float] = None   # Temperatura - fallback con typo
    heart_rate: Optional[float] = None
    spo2: Optional[float] = None
    rssi: Optional[float] = None   # RSSI correcto
    rss1: Optional[float] = None   # RSSI - fallback con typo
    battery: Optional[float] = None

    class Config:
        extra = "allow"


class MQTTPayloadItemN8N(BaseModel):
    """Un item del array payload_caidas / payload_vitales enviado por N8N"""
    message: MQTTMessageN8N
    topic: str


class N8NPredictRequest(BaseModel):
    """
    Formato completo del JSON que N8N envía al backend.
    Es un objeto con flags booleanos y los dos payloads de datos.
    """
    ventana_caidas: bool = Field(True, description="Si True, ejecutar predicción de caídas (Módulo B)")
    ventana_salud: bool = Field(True, description="Si True, ejecutar predicción de salud (Módulo A)")
    payload_caidas: List[MQTTPayloadItemN8N] = Field(
        ..., description="Array de lecturas MQTT para detección de caídas (necesita >= 20)"
    )
    payload_vitales: List[MQTTPayloadItemN8N] = Field(
        ..., description="Array de lecturas MQTT para clasificación de salud (necesita >= 30)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ventana_caidas": True,
                "ventana_salud": True,
                "payload_caidas": [
                    {
                        "message": {
                            "id_patient": "adulto_mayor_test",
                            "id_device": "dispositivo_reloj_01",
                            "ax": -0.091, "ay": -0.191, "az": 9.745,
                            "gx": 0.0162, "gy": -0.0031, "gz": 0.0054,
                            "temp": 36.5,
                            "heart_rate": 75.2, "spo2": 99,
                            "rssi": -48, "battery": 100
                        },
                        "topic": "healthwatch/adulto_mayor_test/dispositivo_reloj_01/biometrics"
                    }
                ],
                "payload_vitales": [
                    {
                        "message": {
                            "id_patient": "adulto_mayor_test",
                            "id_device": "dispositivo_reloj_01",
                            "ax": -0.091, "ay": -0.191, "az": 9.745,
                            "gx": 0.0162, "gy": -0.0031, "gz": 0.0054,
                            "temp": 36.5,
                            "heart_rate": 75.2, "spo2": 99,
                            "rssi": -48, "battery": 100
                        },
                        "topic": "healthwatch/adulto_mayor_test/dispositivo_reloj_01/biometrics"
                    }
                ]
            }
        }

# ============================================
# Modelos Pydantic para validación de entrada
# ============================================

class BiometricDataMessage(BaseModel):
    """Estructura de un dato biométrico individual (del mensaje MQTT)"""
    id_patient: str
    id_device: str
    heart_rate: float
    spo2: float
    temp: Optional[float] = None  # Temperatura - nombre correcto
    tenp: Optional[float] = None  # Temperatura - fallback con typo
    ax: Optional[float] = None
    ay: Optional[float] = None
    az: Optional[float] = None
    gx: Optional[float] = None
    gy: Optional[float] = None
    gz: Optional[float] = None
    rssi: Optional[float] = None  # RSSI correcto
    rss1: Optional[float] = None  # Fallback
    battery: Optional[float] = None
    
    class Config:
        extra = "allow"  # Permite campos adicionales
        example = {
            "id_patient": "adulto_mayor_test",
            "id_device": "dispositivo_reloj_01",
            "ax": -0.091,
            "ay": -0.191,
            "az": 9.745,
            "gx": 0.0162,
            "gy": -0.0031,
            "gz": 0.0054,
            "temp": 36.5,
            "heart_rate": 75.2,
            "spo2": 99,
            "rssi": -48,
            "battery": 100
        }


class MQTTPayload(BaseModel):
    """Estructura completa del payload MQTT (message + topic)"""
    message: BiometricDataMessage
    topic: str


class ModuloAPredictionRequestN8N(BaseModel):
    """Datos biométricos para clasificación de salud (Módulo A) desde n8n - formato MQTT"""
    # Acepta tanto array directo de datos como array de payloads MQTT
    datos: List[Any] = Field(..., description="Lista de datos biométricos o payloads MQTT completos")
    
    class Config:
        example = {
            "datos": [
                {
                    "message": {
                        "id_patient": "adulto_mayor_test",
                        "id_device": "dispositivo_reloj_01",
                        "heart_rate": 75.2,
                        "spo2": 99,
                        "temp": 36.5,
                        "ax": -0.091,
                        "ay": -0.191,
                        "az": 9.745,
                        "gx": 0.0162,
                        "gy": -0.0031,
                        "gz": 0.0054,
                        "rssi": -48,
                        "battery": 100
                    },
                    "topic": "healthwatch/adulto_mayor_test/dispositivo_reloj_01/biometrics"
                }
            ]
        }


class ModuloBPredictionRequestN8N(BaseModel):
    """Datos IMU para detección de caídas (Módulo B) desde n8n - formato MQTT"""
    # Acepta tanto array directo de datos como array de payloads MQTT completos
    datos: List[Any] = Field(..., description="Lista de datos IMU o payloads MQTT completos")
    
    class Config:
        example = {
            "datos": [
                {
                    "message": {
                        "id_patient": "adulto_mayor_test",
                        "id_device": "dispositivo_reloj_01",
                        "heart_rate": 75.2,
                        "spo2": 99,
                        "temp": 36.5,
                        "ax": -0.091,
                        "ay": -0.191,
                        "az": 9.745,
                        "gx": 0.0162,
                        "gy": -0.0031,
                        "gz": 0.0054,
                        "rssi": -48,
                        "battery": 100
                    },
                    "topic": "healthwatch/adulto_mayor_test/dispositivo_reloj_01/biometrics"
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
    Predice la clasificación de salud desde datos de n8n (formato MQTT).
    
    Acepta un array de datos biométricos (ya sea con estructura MQTT completa o datos directos).
    Extrae los campos necesarios y usa los últimos 30 valores.
    
    **Entrada:**
    - datos: Lista de objetos biométricos (con message+topic o datos directos)
    
    **Salida:**
    - clasificacion: "okay", "warning" o "bad"
    - probabilidades: Probabilidades para cada clase
    - paciente_id: ID del paciente procesado
    - dispositivo_id: ID del dispositivo
    """
    try:
        if len(datos_request.datos) < 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Se requieren al menos 30 lecturas, se recibieron {len(datos_request.datos)}"
            )
        
        # Usar los últimos 30 datos
        datos_ventana = datos_request.datos[-30:]
        
        # Procesar datos y extraer campos
        lecturas_procesadas = []
        
        for dato in datos_ventana:
            # Convertir a dict si es necesario
            if isinstance(dato, dict):
                dato_dict = dato
            else:
                dato_dict = dato.dict() if hasattr(dato, 'dict') else dato
            
            # Extraer message si viene en formato MQTT completo
            if "message" in dato_dict:
                mensaje = dato_dict["message"]
            else:
                mensaje = dato_dict
            
            # Validar campos requeridos
            if not all(k in mensaje for k in ["heart_rate", "spo2"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Faltan campos necesarios: heart_rate o spo2"
                )
            
            # Extraer temperatura (aceptar temp o tenp)
            temp = mensaje.get("temp") or mensaje.get("tenp")
            if temp is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Falta campo de temperatura: temp o tenp"
                )
            
            lecturas_procesadas.append({
                "id_patient": mensaje.get("id_patient"),
                "id_device": mensaje.get("id_device"),
                "heart_rate": float(mensaje["heart_rate"]),
                "spo2": float(mensaje["spo2"]),
                "temp": float(temp)
            })
        
        # Extraer listas de valores
        hr_vals = [float(d["heart_rate"]) for d in lecturas_procesadas]
        spo2_vals = [float(d["spo2"]) for d in lecturas_procesadas]
        temp_vals = [float(d["temp"]) for d in lecturas_procesadas]
        
        # Obtener IDs del primer dato
        paciente_id = lecturas_procesadas[0]["id_patient"]
        dispositivo_id = lecturas_procesadas[0]["id_device"]
        
        # Realizar predicción
        clasificacion, probabilidades = predecir_ventana(hr_vals, spo2_vals, temp_vals)
        
        return {
            "status": "éxito",
            "modulo": "A",
            "paciente_id": paciente_id,
            "dispositivo_id": dispositivo_id,
            "clasificacion": clasificacion,
            "probabilidades": probabilidades,
            "datos_procesados": len(lecturas_procesadas)
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
    Predice la probabilidad de caída desde datos IMU de n8n (formato MQTT).
    
    Acepta un array de datos IMU (ya sea con estructura MQTT completa o datos directos).
    Extrae los campos necesarios y usa los últimos 20 valores.
    
    **Entrada:**
    - datos: Lista de objetos IMU (con message+topic o datos directos)
    
    **Salida:**
    - probabilidad_caida: Probabilidad de caída (0.0 a 1.0)
    - es_caida: Boolean indicando si se detectó caída
    - paciente_id: ID del paciente procesado
    - dispositivo_id: ID del dispositivo
    """
    try:
        if len(datos_request.datos) < 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Se requieren al menos 20 lecturas, se recibieron {len(datos_request.datos)}"
            )
        
        # Usar los últimos 20 datos
        datos_ventana = datos_request.datos[-20:]
        
        # Procesar datos y extraer campos
        lecturas_procesadas = []
        
        for dato in datos_ventana:
            # Convertir a dict si es necesario
            if isinstance(dato, dict):
                dato_dict = dato
            else:
                dato_dict = dato.dict() if hasattr(dato, 'dict') else dato
            
            # Extraer message si viene en formato MQTT completo
            if "message" in dato_dict:
                mensaje = dato_dict["message"]
            else:
                mensaje = dato_dict
            
            # Validar campos IMU requeridos
            campos_imu = ["ax", "ay", "az", "gx", "gy", "gz"]
            if not all(k in mensaje for k in campos_imu):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Faltan campos IMU necesarios: {', '.join(campos_imu)}"
                )
            
            lecturas_procesadas.append({
                "id_patient": mensaje.get("id_patient"),
                "id_device": mensaje.get("id_device"),
                "ax": float(mensaje["ax"]),
                "ay": float(mensaje["ay"]),
                "az": float(mensaje["az"]),
                "gx": float(mensaje["gx"]),
                "gy": float(mensaje["gy"]),
                "gz": float(mensaje["gz"])
            })
        
        # Extraer listas de valores
        ax_vals = [float(d["ax"]) for d in lecturas_procesadas]
        ay_vals = [float(d["ay"]) for d in lecturas_procesadas]
        az_vals = [float(d["az"]) for d in lecturas_procesadas]
        gx_vals = [float(d["gx"]) for d in lecturas_procesadas]
        gy_vals = [float(d["gy"]) for d in lecturas_procesadas]
        gz_vals = [float(d["gz"]) for d in lecturas_procesadas]
        
        # Obtener IDs del primer dato
        paciente_id = lecturas_procesadas[0]["id_patient"]
        dispositivo_id = lecturas_procesadas[0]["id_device"]
        
        # Realizar predicción
        probabilidad, es_caida = predecir_caida(ax_vals, ay_vals, az_vals, gx_vals, gy_vals, gz_vals)
        
        return {
            "status": "éxito",
            "modulo": "B",
            "paciente_id": paciente_id,
            "dispositivo_id": dispositivo_id,
            "probabilidad_caida": probabilidad,
            "es_caida": es_caida,
            "datos_procesados": len(lecturas_procesadas)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ejecutar predicción del Módulo B: {str(e)}"
        )


# ============================================================
# Endpoints N8N — Separados por tipo (misma estructura JSON)
# ============================================================
# N8N envía el mismo JSON completo a cada endpoint.
# Estructura esperada (el objeto [0] del array que construye N8N):
# {
#   "ventana_caidas": true,
#   "ventana_salud": true,
#   "payload_caidas": [ { "message": {...}, "topic": "..." }, ... ],
#   "payload_vitales": [ { "message": {...}, "topic": "..." }, ... ]
# }

@router.post("/n8n/salud")
def predecir_n8n_salud(payload: N8NPredictRequest):
    """
    **Endpoint N8N — Clasificación de Salud (Módulo A)**

    Recibe el mismo JSON completo que construye N8N y procesa únicamente
    `payload_vitales` para predecir la clasificación de salud (SpO2 / heart rate / temperatura).

    Usa los **últimos 30** items del array `payload_vitales`.

    **Campos requeridos en cada `message`:** `id_patient`, `id_device`,
    `heart_rate`, `spo2`, `temp` (o `tenp`).

    **Respuesta:**
    - `clasificacion`: `"okay"` | `"warning"` | `"bad"`
    - `probabilidades`: dict con probabilidad de cada clase
    """
    try:
        items = payload.payload_vitales
        if len(items) < 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"payload_vitales requiere al menos 30 lecturas, se recibieron {len(items)}"
            )

        ventana = items[-30:]
        hr_vals, spo2_vals, temp_vals = [], [], []
        paciente_id = None
        dispositivo_id = None

        for item in ventana:
            msg = item.message
            if msg.heart_rate is None or msg.spo2 is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="payload_vitales: falta 'heart_rate' o 'spo2' en alguna lectura"
                )
            temp = msg.temp if msg.temp is not None else msg.tenp
            if temp is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="payload_vitales: falta campo de temperatura ('temp' o 'tenp') en alguna lectura"
                )
            hr_vals.append(float(msg.heart_rate))
            spo2_vals.append(float(msg.spo2))
            temp_vals.append(float(temp))
            if paciente_id is None:
                paciente_id = msg.id_patient
                dispositivo_id = msg.id_device

        clasificacion, probabilidades = predecir_ventana(hr_vals, spo2_vals, temp_vals)

        return {
            "status": "éxito",
            "modulo": "A",
            "paciente_id": paciente_id,
            "dispositivo_id": dispositivo_id,
            "clasificacion": clasificacion,
            "probabilidades": probabilidades,
            "datos_procesados": len(ventana)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en clasificación de salud (Módulo A): {str(e)}"
        )


@router.post("/n8n/caidas")
def predecir_n8n_caidas(payload: N8NPredictRequest):
    """
    **Endpoint N8N — Detección de Caídas (Módulo B)**

    Recibe el mismo JSON completo que construye N8N y procesa únicamente
    `payload_caidas` para predecir la probabilidad de caída con datos IMU.

    Usa los **últimos 20** items del array `payload_caidas`.

    **Campos requeridos en cada `message`:** `id_patient`, `id_device`,
    `ax`, `ay`, `az`, `gx`, `gy`, `gz`.

    **Respuesta:**
    - `probabilidad_caida`: float entre 0.0 y 1.0
    - `es_caida`: bool (`true` si prob > 0.5)
    """
    try:
        items = payload.payload_caidas
        if len(items) < 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"payload_caidas requiere al menos 20 lecturas, se recibieron {len(items)}"
            )

        ventana = items[-20:]
        campos_imu = ["ax", "ay", "az", "gx", "gy", "gz"]
        ax_vals, ay_vals, az_vals, gx_vals, gy_vals, gz_vals = [], [], [], [], [], []
        paciente_id = None
        dispositivo_id = None

        for item in ventana:
            msg = item.message
            msg_dict = msg.dict()
            for campo in campos_imu:
                if msg_dict.get(campo) is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"payload_caidas: falta campo IMU '{campo}' en alguna lectura"
                    )
            ax_vals.append(float(msg.ax))
            ay_vals.append(float(msg.ay))
            az_vals.append(float(msg.az))
            gx_vals.append(float(msg.gx))
            gy_vals.append(float(msg.gy))
            gz_vals.append(float(msg.gz))
            if paciente_id is None:
                paciente_id = msg.id_patient
                dispositivo_id = msg.id_device

        probabilidad, es_caida = predecir_caida(
            ax_vals, ay_vals, az_vals, gx_vals, gy_vals, gz_vals
        )

        return {
            "status": "éxito",
            "modulo": "B",
            "paciente_id": paciente_id,
            "dispositivo_id": dispositivo_id,
            "probabilidad_caida": probabilidad,
            "es_caida": es_caida,
            "datos_procesados": len(ventana)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en predicción de caídas (Módulo B): {str(e)}"
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
