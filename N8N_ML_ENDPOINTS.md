# Endpoints ML para n8n - HealthWatch

## Descripción General

N8N acumula las lecturas MQTT en ventanas y envía el **mismo JSON completo** a dos endpoints independientes:

| Endpoint | Método | Procesa | Descripción |
|----------|--------|---------|-------------|
| `/api/ml/n8n/salud` | **POST** | `payload_vitales` | Clasificación de salud (SpO2 / HR / Temperatura) |
| `/api/ml/n8n/caidas` | **POST** | `payload_caidas` | Detección de caídas (datos IMU) |

Los endpoints legacy siguen disponibles para compatibilidad.

---

## Formato JSON que N8N envía (mismo para ambos endpoints)

```json
{
  "ventana_caidas": true,
  "ventana_salud": true,
  "payload_caidas": [
    {
      "message": {
        "id_patient": "adulto_mayor_test",
        "id_device": "dispositivo_reloj_01",
        "ax": -0.06,
        "ay": 0.216,
        "az": 9.747,
        "gx": -0.0174,
        "gy": -0.0052,
        "gz": 0.0092,
        "temp": 36.6,
        "heart_rate": 72.9,
        "spo2": 97,
        "rssi": -63,
        "battery": 100
      },
      "topic": "healthwatch/adulto_mayor_test/dispositivo_reloj_01/biometrics"
    }
  ],
  "payload_vitales": [
    {
      "message": {
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
      },
      "topic": "healthwatch/adulto_mayor_test/dispositivo_reloj_01/biometrics"
    }
  ]
}
```

> **Campos de temperatura/RSSI:** El backend acepta tanto `temp` como `tenp`, y tanto `rssi` como `rss1`. El dispositivo real usa `temp` y `rssi`.

---

## Endpoint 1 — Clasificación de Salud (SpO2 / HR)

```
POST /api/ml/n8n/salud
```

### Descripción
Recibe el JSON completo y procesa **solo `payload_vitales`** para predecir el estado de salud del paciente. Usa los **últimos 30** items del array.

### Campos requeridos en cada `message` de `payload_vitales`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_patient` | string | ID del paciente |
| `id_device` | string | ID del dispositivo |
| `heart_rate` | float | Frecuencia cardíaca (BPM) |
| `spo2` | float | Saturación de oxígeno (%) |
| `temp` o `tenp` | float | Temperatura corporal (°C) |

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

### Posibles valores de `clasificacion`
- **`"okay"`** — Salud normal, sin alertas
- **`"warning"`** — Precaución, posible estrés o fatiga
- **`"bad"`** — Crítico, requiere atención inmediata

### Errores
| Código | Descripción |
|--------|-------------|
| 400 | Menos de 30 lecturas en `payload_vitales` o campos faltantes |
| 500 | Error interno del modelo |

---

## Endpoint 2 — Detección de Caídas (IMU)

```
POST /api/ml/n8n/caidas
```

### Descripción
Recibe el mismo JSON completo y procesa **solo `payload_caidas`** para predecir la probabilidad de caída. Usa los **últimos 20** items del array.

### Campos requeridos en cada `message` de `payload_caidas`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_patient` | string | ID del paciente |
| `id_device` | string | ID del dispositivo |
| `ax` | float | Aceleración eje X (m/s²) |
| `ay` | float | Aceleración eje Y (m/s²) |
| `az` | float | Aceleración eje Z (m/s²) |
| `gx` | float | Velocidad angular eje X (rad/s) |
| `gy` | float | Velocidad angular eje Y (rad/s) |
| `gz` | float | Velocidad angular eje Z (rad/s) |

### Response (200 OK)
```json
{
  "status": "éxito",
  "modulo": "B",
  "paciente_id": "adulto_mayor_test",
  "dispositivo_id": "dispositivo_reloj_01",
  "probabilidad_caida": 0.08,
  "es_caida": false,
  "datos_procesados": 20
}
```

### Interpretación de `probabilidad_caida`
| Rango | Interpretación |
|-------|---------------|
| `< 0.3` | Baja probabilidad de caída |
| `0.3 – 0.7` | Probabilidad media (revisar) |
| `> 0.7` | Alta probabilidad de caída |

### Errores
| Código | Descripción |
|--------|-------------|
| 400 | Menos de 20 lecturas en `payload_caidas` o campos IMU faltantes |
| 500 | Error interno del modelo |

---

## Configuración en n8n

En n8n, después del nodo que acumula las ventanas, agrega **dos nodos HTTP Request** en paralelo:

### Nodo 1 — Clasificación de Salud
```
Método: POST
URL: http://localhost:8000/api/ml/n8n/salud
Body (JSON): {{ $json[0] }}
```

### Nodo 2 — Detección de Caídas
```
Método: POST
URL: http://localhost:8000/api/ml/n8n/caidas
Body (JSON): {{ $json[0] }}
```

> `$json[0]` extrae el primer elemento del array que N8N construye, enviando solo el objeto interno `{ventana_caidas, ventana_salud, payload_caidas, payload_vitales}`.

---

## Endpoints Legacy (Compatibilidad)

Estos siguen disponibles para integraciones sin el formato de ventana N8N.

### Módulo A — Salud (formato por nodo individual)
```
POST /api/ml/modulo-a/prediccion/n8n
Body: { "datos": [ { "message": {...}, "topic": "..." }, ... ] }
```

### Módulo B — Caídas (formato por nodo individual)
```
POST /api/ml/modulo-b/prediccion/n8n
Body: { "datos": [ { "message": {...}, "topic": "..." }, ... ] }
```

### Formato directo (sin MQTT)
```
POST /api/ml/modulo-a/prediccion
Body: { "hr_vals": [...], "spo2_vals": [...], "temp_vals": [...] }

POST /api/ml/modulo-b/prediccion
Body: { "ax_vals": [...], "ay_vals": [...], "az_vals": [...], "gx_vals": [...], "gy_vals": [...], "gz_vals": [...] }
```

---

## Notas de Implementación

### Requisitos mínimos de datos
- **`/n8n/salud`** — mínimo **30** lecturas en `payload_vitales`
- **`/n8n/caidas`** — mínimo **20** lecturas en `payload_caidas`

El endpoint siempre toma los **últimos N valores** del array (orden temporal).

### Rendimiento
- Módulo A (salud): ~50ms (FeedForward)
- Módulo B (caídas): ~30ms (LSTM)

---

## URLs Completas

### Desarrollo local
```
POST http://localhost:8000/api/ml/n8n/salud
POST http://localhost:8000/api/ml/n8n/caidas
```

### Producción
```
POST https://tudominio.com/api/ml/n8n/salud
POST https://tudominio.com/api/ml/n8n/caidas
```

---

## Swagger / OpenAPI
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
