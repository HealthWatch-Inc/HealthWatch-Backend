# Endpoints ML para n8n - HealthWatch

## Descripción General
Los nuevos endpoints están diseñados para que n8n pueda enviar datos directamente del formato MQTT/biométrico del dispositivo a los modelos ML, sin necesidad de transformación previa. Los endpoints extraen automáticamente los campos necesarios y acumulan los datos para hacer las predicciones.

---

## Formato de datos que envía n8n

Cada lectura desde el dispositivo llega en este formato:
```json
{
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
```

---

## Módulo A: Clasificación de Salud (desde n8n)

### Endpoint
```
POST /api/ml/modulo-a/prediccion/n8n
```

### Descripción
Predice la clasificación de salud (estrés/fatiga) basada en datos biométricos enviados por n8n. Acepta un array de lecturas y procesa automáticamente los últimos 30 valores.

### Request Body (JSON)
```json
{
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
        },
        {
            "id_patient": "adulto_mayor_test",
            "id_device": "dispositivo_reloj_01",
            "heart_rate": 72.1,
            "spo2": 98,
            "tenp": 36.3,
            "ax": 0.054,
            "ay": 0.194,
            "az": 9.871,
            "gx": 0.005,
            "gy": 0.0093,
            "gz": 0.0063,
            "rss1": -63,
            "battery": 100
        }
    ]
}
```

### Parámetros
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|----------|-------------|
| `datos` | Array[BiometricData] | ✅ | Array de datos biométricos (se usan los últimos 30) |

**Campos de BiometricData:**
| Campo | Tipo | Requerido para Módulo A | Descripción |
|-------|------|--------|-------------|
| `id_patient` | string | ✅ | ID del paciente |
| `id_device` | string | ✅ | ID del dispositivo |
| `heart_rate` | float | ✅ | Frecuencia cardíaca (BPM) |
| `spo2` | float | ✅ | Saturación de oxígeno (%) |
| `tenp` | float | ✅ | Temperatura corporal (°C) - NOTA: viene con typo en el nombre |
| `ax`, `ay`, `az` | float | ❌ | Aceleración (no necesaria para Módulo A) |
| `gx`, `gy`, `gz` | float | ❌ | Velocidad angular (no necesaria para Módulo A) |
| `rss1`, `battery` | float | ❌ | Información del dispositivo (opcional) |

### Response (200 OK)
```json
{
    "status": "éxito",
    "modulo": "A",
    "paciente_id": "adulto_mayor_test",
    "dispositivo_id": "dispositivo_reloj_01",
    "clasificacion": "okay",
    "probabilidades": {
        "okay": 0.85,
        "warning": 0.12,
        "bad": 0.03
    },
    "datos_procesados": 30
}
```

### Posibles valores de clasificación
- **"okay"**: Salud normal, sin alertas
- **"warning"**: Precaución, posible estrés o fatiga
- **"bad"**: Crítico, requiere atención inmediata

### Códigos de error
| Código | Descripción |
|--------|-------------|
| 400 | Menos de 30 lecturas o campos obligatorios faltantes |
| 500 | Error al ejecutar el modelo |

### Ejemplo en n8n (HTTP Request)
```
URL: POST http://localhost:8000/api/ml/modulo-a/prediccion/n8n

Body (tipo: JSON):
{
    "datos": {{ $node["nodeAnterior"].json }}
}

// Si el nodo anterior devuelve un array de lecturas:
{
    "datos": {{ $node["nodeAnterior"].json.biometricReadings }}
}
```

---

## Módulo B: Detección de Caídas (desde n8n)

### Endpoint
```
POST /api/ml/modulo-b/prediccion/n8n
```

### Descripción
Predice la probabilidad de caída basada en datos IMU enviados por n8n. Acepta un array de lecturas y procesa automáticamente los últimos 20 valores.

### Request Body (JSON)
```json
{
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
        },
        {
            "id_patient": "adulto_mayor_test",
            "id_device": "dispositivo_reloj_01",
            "heart_rate": 72.1,
            "spo2": 98,
            "tenp": 36.3,
            "ax": 0.054,
            "ay": 0.194,
            "az": 9.871,
            "gx": 0.005,
            "gy": 0.0093,
            "gz": 0.0063,
            "rss1": -63,
            "battery": 100
        }
    ]
}
```

### Parámetros
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|----------|-------------|
| `datos` | Array[BiometricData] | ✅ | Array de datos IMU (se usan los últimos 20) |

**Campos de BiometricData (relevantes para Módulo B):**
| Campo | Tipo | Requerido para Módulo B | Descripción |
|-------|------|--------|-------------|
| `id_patient` | string | ✅ | ID del paciente |
| `id_device` | string | ✅ | ID del dispositivo |
| `ax` | float | ✅ | Aceleración en eje X (m/s²) |
| `ay` | float | ✅ | Aceleración en eje Y (m/s²) |
| `az` | float | ✅ | Aceleración en eje Z (m/s²) |
| `gx` | float | ✅ | Velocidad angular en eje X (rad/s) |
| `gy` | float | ✅ | Velocidad angular en eje Y (rad/s) |
| `gz` | float | ✅ | Velocidad angular en eje Z (rad/s) |
| `heart_rate`, `spo2`, `tenp` | float | ❌ | Biométricos (no necesarios para Módulo B) |
| `rss1`, `battery` | float | ❌ | Información del dispositivo (opcional) |

### Response (200 OK)
```json
{
    "status": "éxito",
    "modulo": "B",
    "paciente_id": "adulto_mayor_test",
    "dispositivo_id": "dispositivo_reloj_01",
    "probabilidad_caida": 0.15,
    "es_caida": false,
    "datos_procesados": 20
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
| 400 | Menos de 20 lecturas o campos IMU obligatorios faltantes |
| 500 | Error al ejecutar el modelo |

### Ejemplo en n8n (HTTP Request)
```
URL: POST http://localhost:8000/api/ml/modulo-b/prediccion/n8n

Body (tipo: JSON):
{
    "datos": {{ $node["nodeAnterior"].json }}
}

// Si el nodo anterior devuelve un array de lecturas:
{
    "datos": {{ $node["nodeAnterior"].json.imuReadings }}
}
```

---

## Endpoints Legacy (Compatibilidad)

### Módulo A - Formato directo
```
POST /api/ml/modulo-a/prediccion
```

Acepta listas directas de valores (para integración sin n8n):
```json
{
    "hr_vals": [72, 73, 74, ...],      // 30 valores
    "spo2_vals": [98, 98, 97, ...],    // 30 valores
    "temp_vals": [36.5, 36.5, ...]     // 30 valores
}
```

### Módulo B - Formato directo
```
POST /api/ml/modulo-b/prediccion
```

Acepta listas directas de valores (para integración sin n8n):
```json
{
    "ax_vals": [0.1, 0.2, ...],        // 20 valores
    "ay_vals": [0.1, 0.2, ...],        // 20 valores
    "az_vals": [9.8, 9.8, ...],        // 20 valores
    "gx_vals": [0.01, 0.02, ...],      // 20 valores
    "gy_vals": [0.01, 0.02, ...],      // 20 valores
    "gz_vals": [0.01, 0.02, ...]       // 20 valores
}
```

---

## Notas Importantes

### Requisitos de datos
1. **Módulo A (n8n)**: Necesita al menos 30 lecturas biométricas con heart_rate, spo2, tenp
2. **Módulo B (n8n)**: Necesita al menos 20 lecturas IMU con ax, ay, az, gx, gy, gz
3. Los valores deben estar en orden temporal
4. El endpoint automáticamente usa los últimos 30 o 20 valores del array

### Flujo típico en n8n

1. **Recibir datos MQTT** → Nodo MQTT con el payload biométrico
2. **Acumular datos** → Usar un array que guarde las últimas N lecturas
3. **Enviar a API ML** → POST a `/api/ml/modulo-a/prediccion/n8n` o `/api/ml/modulo-b/prediccion/n8n`
4. **Procesar resultado** → Guardar en Firestore, enviar notificación, etc.

### Consideraciones de rendimiento
- Módulo A: ~50ms de predicción (FeedForward - rápido)
- Módulo B: ~30ms de predicción (LSTM ligero)
- Ideales para procesamiento en tiempo real desde n8n

### Campo "tenp" con typo
El campo `tenp` (temperatura) viene con typo desde el dispositivo. El backend maneja esto automáticamente, pero es importante notar que en los datos raw MQTT verás `tenp` en lugar de `temp`.

---

## URLs Completas

### Desarrollo local
```
POST http://localhost:8000/api/ml/modulo-a/prediccion/n8n
POST http://localhost:8000/api/ml/modulo-b/prediccion/n8n
POST http://localhost:8000/api/ml/modulo-a/prediccion      (legacy)
POST http://localhost:8000/api/ml/modulo-b/prediccion      (legacy)
```

### Producción (ajusta según tu dominio)
```
POST https://tudominio.com/api/ml/modulo-a/prediccion/n8n
POST https://tudominio.com/api/ml/modulo-b/prediccion/n8n
```

---

## Swagger/OpenAPI
Puedes ver la documentación interactiva de los endpoints en:
- `http://localhost:8000/docs` (Swagger UI)
- `http://localhost:8000/redoc` (ReDoc)
