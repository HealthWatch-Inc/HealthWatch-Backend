# Guía de Integración de ML con n8n - HealthWatch

## Visión General

Esta guía explica cómo crear workflows en n8n que:
1. Reciban datos MQTT del dispositivo biométrico/IMU
2. Acumulen datos en ventanas (30 para Módulo A, 20 para Módulo B)
3. Envíen predicciones al backend
4. Procesen y almacenen resultados

---

## Estructura de Datos desde el Dispositivo

Cada lectura MQTT llega con este formato:

```json
{
    "message": {
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
    },
    "topic": "healthwatch/adulto_mayor_test/dispositivo_reloj_01/biometrics"
}
```

---

## Workflow 1: Módulo A - Clasificación de Salud

### Estructura del Workflow

```
[1. MQTT Trigger]
    ↓
[2. Extraer datos]
    ↓
[3. Acumular en array (últimas 30)]
    ↓
[4. ¿30 datos acumulados?]
    ├─ NO → Esperar más datos
    └─ SÍ ↓
    [5. HTTP POST a /api/ml/modulo-a/prediccion/n8n]
        ↓
    [6. Procesar resultado]
        ↓
    [7. Guardar en Firestore]
    [8. Enviar notificación si warning/bad]
```

### Paso a Paso

#### 1. Trigger MQTT
- **Nodo**: MQTT
- **Trigger**: On message
- **Topic**: `healthwatch/#` (o el topic específico)
- **Salida**: `$node["MQTT"].json`

```
message: {
    id_patient,
    id_device,
    heart_rate,
    spo2,
    tenp,
    ax, ay, az,
    gx, gy, gz,
    ...
}
```

#### 2. Code: Extraer y acumular datos
- **Nodo**: JavaScript (Code)
- **Entrada**: `$node["MQTT"].json.message`

```javascript
// Extrae el mensaje del MQTT
const newReading = $node["MQTT"].json.message;

// Obtener el estado anterior (si existe)
let dataBuffer = workflowData || {
  paciente_id: newReading.id_patient,
  dispositivo_id: newReading.id_device,
  lecturas: []
};

// Agregar la nueva lectura
dataBuffer.lecturas.push({
    id_patient: newReading.id_patient,
    id_device: newReading.id_device,
    heart_rate: newReading.heart_rate,
    spo2: newReading.spo2,
    tenp: newReading.tenp,
    ax: newReading.ax,
    ay: newReading.ay,
    az: newReading.az,
    gx: newReading.gx,
    gy: newReading.gy,
    gz: newReading.gz,
    battery: newReading.battery,
    rss1: newReading.rss1
});

// Mantener solo las últimas 30 lecturas
if (dataBuffer.lecturas.length > 30) {
  dataBuffer.lecturas = dataBuffer.lecturas.slice(-30);
}

return {
  dataBuffer: dataBuffer,
  isReadyForModuloA: dataBuffer.lecturas.length >= 30
};
```

#### 3. Condición: ¿Tenemos 30 datos?
- **Nodo**: If
- **Condición**: `$node["Code"].json.isReadyForModuloA == true`

#### 4. HTTP POST
- **Nodo**: HTTP Request
- **Método**: POST
- **URL**: `http://localhost:8000/api/ml/modulo-a/prediccion/n8n`
- **Headers**: 
  ```
  Content-Type: application/json
  ```
- **Body** (JSON):
  ```json
  {
    "datos": {{ $node["Code"].json.dataBuffer.lecturas }}
  }
  ```

#### 5. Procesar respuesta
- **Nodo**: Set (o Code)
- **Variables a capturar**:
  - `clasificacion`
  - `probabilidades`
  - `paciente_id`
  - `dispositivo_id`

```javascript
return {
  paciente_id: $node["HTTP Request"].json.paciente_id,
  dispositivo_id: $node["HTTP Request"].json.dispositivo_id,
  clasificacion: $node["HTTP Request"].json.clasificacion,
  probabilidades: $node["HTTP Request"].json.probabilidades,
  timestamp: new Date().toISOString(),
  es_alerta: $node["HTTP Request"].json.clasificacion !== "okay"
};
```

#### 6. Guardar en Firestore
- **Nodo**: Firestore
- **Operación**: Create Document
- **Colección**: `pacientes/{paciente_id}/estados_salud`
- **Documento**: Auto-generado
- **Data**:
  ```json
  {
    "paciente_id": {{ $node["Set"].json.paciente_id }},
    "dispositivo_id": {{ $node["Set"].json.dispositivo_id }},
    "clasificacion": {{ $node["Set"].json.clasificacion }},
    "probabilidades": {{ JSON.stringify($node["Set"].json.probabilidades) }},
    "timestamp": {{ $node["Set"].json.timestamp }},
    "es_alerta": {{ $node["Set"].json.es_alerta }}
  }
  ```

#### 7. Notificación condicional
- **Nodo**: If
- **Condición**: `$node["Set"].json.es_alerta == true`
- **Si es true**:
  - **Nodo**: Send notification (Firebase Cloud Messaging, email, etc.)
  - **Mensaje**: `Alerta de salud para paciente: {{$node["Set"].json.clasificacion}}`

---

## Workflow 2: Módulo B - Detección de Caídas

### Estructura del Workflow

```
[1. MQTT Trigger]
    ↓
[2. Extraer datos IMU]
    ↓
[3. Acumular en array (últimas 20)]
    ↓
[4. ¿20 datos acumulados?]
    ├─ NO → Esperar más datos
    └─ SÍ ↓
    [5. HTTP POST a /api/ml/modulo-b/prediccion/n8n]
        ↓
    [6. Procesar resultado]
        ↓
    [7. Si es_caida = true]
        ├─ Guardar alerta urgente en Firestore
        └─ Enviar notificación crítica
```

### Paso a Paso (Similar a Módulo A, pero con cambios)

#### Pasos 1-2: Idénticos a Módulo A

#### 3. Code: Acumular datos IMU (20 lecturas)
```javascript
const newReading = $node["MQTT"].json.message;

let imuBuffer = workflowData || {
  paciente_id: newReading.id_patient,
  dispositivo_id: newReading.id_device,
  lecturas_imu: []
};

imuBuffer.lecturas_imu.push({
    id_patient: newReading.id_patient,
    id_device: newReading.id_device,
    heart_rate: newReading.heart_rate,
    spo2: newReading.spo2,
    tenp: newReading.tenp,
    ax: newReading.ax,
    ay: newReading.ay,
    az: newReading.az,
    gx: newReading.gx,
    gy: newReading.gy,
    gz: newReading.gz,
    battery: newReading.battery,
    rss1: newReading.rss1
});

// Mantener solo las últimas 20 lecturas
if (imuBuffer.lecturas_imu.length > 20) {
  imuBuffer.lecturas_imu = imuBuffer.lecturas_imu.slice(-20);
}

return {
  imuBuffer: imuBuffer,
  isReadyForModuloB: imuBuffer.lecturas_imu.length >= 20
};
```

#### 4. Condición: ¿Tenemos 20 datos IMU?
- **Nodo**: If
- **Condición**: `$node["Code"].json.isReadyForModuloB == true`

#### 5. HTTP POST
- **Nodo**: HTTP Request
- **Método**: POST
- **URL**: `http://localhost:8000/api/ml/modulo-b/prediccion/n8n`
- **Body** (JSON):
  ```json
  {
    "datos": {{ $node["Code"].json.imuBuffer.lecturas_imu }}
  }
  ```

#### 6-7. Procesar y guardar
```javascript
const resultado = $node["HTTP Request"].json;

return {
  paciente_id: resultado.paciente_id,
  dispositivo_id: resultado.dispositivo_id,
  es_caida: resultado.es_caida,
  probabilidad_caida: resultado.probabilidad_caida,
  timestamp: new Date().toISOString()
};
```

#### 8. Si es caída
- **Nodo**: If
- **Condición**: `$node["Set"].json.es_caida == true`
- **Si es true** → Enviar alerta urgente (email, SMS, notificación push)

---

## Configuración de Persistencia (Opcional)

Para mantener los datos acumulados entre execuciones de n8n, puedes usar:

### Opción 1: Usar Firestore como buffer
```javascript
// Guardar buffer en Firestore
const buffer_ref = `pacientes/${id_patient}/buffers/modulo_a`;
// Leer y actualizar en cada execución
```

### Opción 2: Usar variables globales de n8n
```javascript
// Establecer variable global
n8n.variables.set('modulo_a_buffer', JSON.stringify(dataBuffer));
// Leer en siguiente execución
const savedBuffer = JSON.parse(n8n.variables.get('modulo_a_buffer'));
```

---

## URLs de los Endpoints

### Desarrollo Local
```
POST http://localhost:8000/api/ml/modulo-a/prediccion/n8n
POST http://localhost:8000/api/ml/modulo-b/prediccion/n8n
```

### Producción (reemplaza con tu dominio)
```
POST https://tu-api.com/api/ml/modulo-a/prediccion/n8n
POST https://tu-api.com/api/ml/modulo-b/prediccion/n8n
```

---

## Debugging y Testing

### 1. Prueba el endpoint directamente
```bash
curl -X POST http://localhost:8000/api/ml/modulo-a/prediccion/n8n \
  -H "Content-Type: application/json" \
  -d '{"datos": [...]}'
```

### 2. Usa Postman o Insomnia
- Importa los ejemplos de `TEST_PAYLOADS_N8N.json`
- Prueba con datos de ejemplo antes de conectar n8n

### 3. Habilita logs en n8n
- Agrega nodos `Log` después de cada paso
- Verifica que los datos se acumulan correctamente
- Verifica que el response del endpoint es correcto

---

## Errores Comunes y Soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| 400 "Se requieren al menos 30 lecturas" | No hay suficientes datos | Verifica que el buffer acumula datos correctamente |
| 400 "Faltan campos necesarios" | Campos nulos en los datos | Valida que MQTT envía todos los campos |
| 500 Error ejecutando modelo | Error en el modelo ML | Verifica los logs del backend |
| Connection refused | El servidor no está corriendo | Inicia el backend: `python -m uvicorn app.main:app --reload` |

---

## Ejemplo Completo de Payload para Testing

### Módulo A (30 lecturas)
Puedes generar datos de prueba con este patrón:

```javascript
// En un nodo Code
const datos = [];
for (let i = 0; i < 30; i++) {
  datos.push({
    id_patient: "adulto_mayor_test",
    id_device: "dispositivo_reloj_01",
    heart_rate: 72 + Math.random() * 5,
    spo2: 98 - Math.random() * 2,
    tenp: 36.5 + Math.random() * 0.3,
    ax: Math.random() * 0.1,
    ay: Math.random() * 0.3,
    az: 9.8 + Math.random() * 0.1,
    gx: Math.random() * 0.01,
    gy: Math.random() * 0.01,
    gz: Math.random() * 0.01,
    battery: 100,
    rss1: -63
  });
}
return { datos };
```

---

## Monitoreo y Métricas

### KPIs a monitorear
- Tiempo promedio de predicción
- Precisión de clasificación en producción
- Latencia MQTT → n8n → Backend
- Tasa de alertas (warning/bad)

### Logs recomendados
- Guardar cada predicción en Firestore con timestamp
- Registrar cambios en clasificación para un paciente
- Alertar si hay cambios bruscos en probabilities

