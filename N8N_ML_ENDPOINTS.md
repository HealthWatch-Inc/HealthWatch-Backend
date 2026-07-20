# Endpoints ML para n8n - HealthWatch

## Descripción General
Los nuevos endpoints están diseñados para que n8n pueda enviar datos directamente a los modelos ML sin necesidad de autenticación, permitiendo predicciones en tiempo real.

---

## Módulo A: Clasificación de Salud

### Endpoint
```
POST /api/ml/modulo-a/prediccion
```

### Descripción
Predice la clasificación de salud (estrés/fatiga) basada en datos biométricos: frecuencia cardíaca, saturación de oxígeno y temperatura corporal.

### Request Body (JSON)
```json
{
    "hr_vals": [72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101],
    "spo2_vals": [98, 98, 98, 97, 97, 97, 96, 96, 96, 95, 95, 95, 94, 94, 94, 93, 93, 93, 92, 92, 92, 91, 91, 91, 90, 90, 90, 89, 89, 89],
    "temp_vals": [36.5, 36.5, 36.6, 36.6, 36.7, 36.7, 36.8, 36.8, 36.9, 36.9, 37.0, 37.0, 37.1, 37.1, 37.2, 37.2, 37.3, 37.3, 37.4, 37.4, 37.5, 37.5, 37.6, 37.6, 37.7, 37.7, 37.8, 37.8, 37.9, 37.9]
}
```

### Parámetros
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|----------|-------------|
| `hr_vals` | Array[float] | ✅ | **Exactamente 30 valores** de frecuencia cardíaca (BPM) |
| `spo2_vals` | Array[float] | ✅ | **Exactamente 30 valores** de saturación de oxígeno (%) |
| `temp_vals` | Array[float] | ✅ | **Exactamente 30 valores** de temperatura corporal (°C) |

### Response (200 OK)
```json
{
    "status": "éxito",
    "modulo": "A",
    "clasificacion": "okay",
    "probabilidades": {
        "okay": 0.85,
        "warning": 0.12,
        "bad": 0.03
    }
}
```

### Posibles valores de clasificación
- **"okay"**: Salud normal, sin alertas
- **"warning"**: Precaución, posible estrés o fatiga
- **"bad"**: Crítico, requiere atención inmediata

### Códigos de error
| Código | Descripción |
|--------|-------------|
| 400 | Número incorrecto de valores en alguna lista (debe ser exactamente 30) |
| 500 | Error al ejecutar el modelo |

### Ejemplo en n8n (HTTP Request)
```
URL: POST http://localhost:8000/api/ml/modulo-a/prediccion
Body (JSON):
{
    "hr_vals": {{ $node["nombreDelNodoAnterior"].json.heartRateArray }},
    "spo2_vals": {{ $node["nombreDelNodoAnterior"].json.spo2Array }},
    "temp_vals": {{ $node["nombreDelNodoAnterior"].json.tempArray }}
}
```

---

## Módulo B: Detección de Caídas

### Endpoint
```
POST /api/ml/modulo-b/prediccion
```

### Descripción
Predice la probabilidad de caída basada en datos del acelerómetro y giroscopio (IMU).

### Request Body (JSON)
```json
{
    "ax_vals": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0],
    "ay_vals": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0],
    "az_vals": [9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8, 9.8],
    "gx_vals": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.2],
    "gy_vals": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.2],
    "gz_vals": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.2]
}
```

### Parámetros
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|----------|-------------|
| `ax_vals` | Array[float] | ✅ | **Exactamente 20 valores** de aceleración en eje X (m/s²) |
| `ay_vals` | Array[float] | ✅ | **Exactamente 20 valores** de aceleración en eje Y (m/s²) |
| `az_vals` | Array[float] | ✅ | **Exactamente 20 valores** de aceleración en eje Z (m/s²) |
| `gx_vals` | Array[float] | ✅ | **Exactamente 20 valores** de velocidad angular en eje X (rad/s) |
| `gy_vals` | Array[float] | ✅ | **Exactamente 20 valores** de velocidad angular en eje Y (rad/s) |
| `gz_vals` | Array[float] | ✅ | **Exactamente 20 valores** de velocidad angular en eje Z (rad/s) |

### Response (200 OK)
```json
{
    "status": "éxito",
    "modulo": "B",
    "probabilidad_caida": 0.15,
    "es_caida": false
}
```

### Interpretación de resultados
- **`probabilidad_caida`**: Valor entre 0.0 y 1.0 indicando la probabilidad de caída
  - < 0.3: Baja probabilidad
  - 0.3 - 0.7: Probabilidad media (revisar)
  - > 0.7: Alta probabilidad de caída
- **`es_caida`**: Boolean true si se detectó caída, false en caso contrario

### Códigos de error
| Código | Descripción |
|--------|-------------|
| 400 | Número incorrecto de valores en alguna lista (debe ser exactamente 20) |
| 500 | Error al ejecutar el modelo |

### Ejemplo en n8n (HTTP Request)
```
URL: POST http://localhost:8000/api/ml/modulo-b/prediccion
Body (JSON):
{
    "ax_vals": {{ $node["nombreDelNodoAnterior"].json.accelX }},
    "ay_vals": {{ $node["nombreDelNodoAnterior"].json.accelY }},
    "az_vals": {{ $node["nombreDelNodoAnterior"].json.accelZ }},
    "gx_vals": {{ $node["nombreDelNodoAnterior"].json.gyroX }},
    "gy_vals": {{ $node["nombreDelNodoAnterior"].json.gyroY }},
    "gz_vals": {{ $node["nombreDelNodoAnterior"].json.gyroZ }}
}
```

---

## Notas Importantes

### Requisitos de datos
1. **Módulo A**: Siempre necesita exactamente **30 valores** de cada sensor biométrico
2. **Módulo B**: Siempre necesita exactamente **20 valores** de cada sensor IMU
3. Los valores deben estar en el orden correcto (orden temporal)

### Integración con n8n
- Los endpoints **NO requieren autenticación** (token Bearer)
- Se comunican por HTTP POST
- Aceptan y retornan JSON
- Ideales para integrarse en workflows de n8n

### Consideraciones de rendimiento
- Módulo A: ~50ms de predicción (FeedForward - rápido)
- Módulo B: ~30ms de predicción (LSTM ligero)
- Usa estos endpoints para procesamiento en tiempo real

### Almacenamiento de resultados
Después de obtener las predicciones, n8n puede:
- Guardar resultados en Firestore
- Enviar notificaciones
- Gatillar alertas
- Actualizar dashboards
- Registrar en logs

---

## URLs Completas

### Desarrollo local
```
POST http://localhost:8000/api/ml/modulo-a/prediccion
POST http://localhost:8000/api/ml/modulo-b/prediccion
```

### Producción (ajusta según tu dominio)
```
POST https://tudominio.com/api/ml/modulo-a/prediccion
POST https://tudominio.com/api/ml/modulo-b/prediccion
```

---

## Swagger/OpenAPI
Puedes ver la documentación interactiva de los endpoints en:
- `http://localhost:8000/docs` (Swagger UI)
- `http://localhost:8000/redoc` (ReDoc)
