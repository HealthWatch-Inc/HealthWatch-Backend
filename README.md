# HealthWatch - Backend

Este repositorio contiene la infraestructura backend, el pipeline de datos de series temporales y las configuraciones de telemetría para el sistema de monitoreo continuo de adultos mayores en centros especializados.

El núcleo del backend está diseñado bajo una arquitectura de microservicios contenerizados, priorizando la eficiencia energética de los dispositivos wearables y la alta disponibilidad de los datos biométricos.

## 🏗️ Arquitectura del Sistema

El flujo de datos sigue un paradigma de desacoplamiento mediante **Publish/Subscribe**:

1. **Edge (Wearable):** El reloj inteligente (ESP32) lee los sensores y publica un payload JSON ligero mediante **MQTT**.
2. **Broker (Mosquitto):** Centraliza y distribuye los mensajes de manera eficiente.
3. **Ingestión (Telegraf):** Se suscribe al broker, procesa el JSON en tiempo real y realiza la inserción masiva en la base de datos.
4. **Almacenamiento (InfluxDB 3 Core):** Motor de series temporales optimizado para analíticas.
5. **Visualización (Grafana):** Dashboard para el monitoreo del personal médico.

## 🛠️ Stack Tecnológico & Hardware

### Hardware del Dispositivo (Wearable)

- **Microcontrolador:** ESP32 (Sistemas de ejecución en arquitectura Dual-Core con FreeRTOS).
- **Pantalla:** OLED SSD1306 (Interfaz local para el usuario).
- **Sensores:**
  - `MPU6050`: Acelerómetro y Giroscopio (Detección de caídas y actividad).
  - `MAX30100`: Oxímetro de pulso y monitor de frecuencia cardíaca.

### Componentes de Infraestructura (Backend)

- **MQTT Broker:** Eclipse Mosquitto `v2.1`
- **Data Collector:** Telegraf `v1.38`
- **Time Series Database:** InfluxDB `v3-core`
- **Visualization:** Grafana Labs (Main Linux-Slim)
- **Orquestación:** Docker & Docker Compose

## 🚀 Guía de Despliegue Rápido (Entorno de Desarrollo)

Sigue estos pasos para levantar toda la infraestructura localmente en tu máquina de desarrollo.

1. Crea las carpetas de volumen persistente

```bash
mkdir -p ~/.influxdb3/core/data
mkdir -p ~/.influxdb3/core/plugins
```

2. Configura el archivo de entorno basandote en el ejemplo

```bash
cp .env.expample .env
```

3. Levanta los servicios de docker

```bash
docker compose up -d
```

4. Genera un token para InfluxDB

```bash
docker exec -it influxdb3-core bash
influxdb3 create token
```

5. Copia el token generado en el archivo .env y reinciar el contenedor

```bash
# INFLUXDB3_AUTH_TOKEN=apiv3_yourtokenhere
docker compose up -d
```

6. Crear la base de datos

```bash
docker exec -it influxdb3-core bash
influxdb3 create database health-watch
```

## 📊 Modelo de Datos

InfluxDB es schemaless, por lo que Telegraf creará automáticamente este esquema estructurado al recibir el primer mensaje MQTT del ESP32:

```yml
table: biometrics
tags:
  id_patient: id_patient
  id_device: id_device
fields:
  # m/s^2
  ax: acceleration_x (float)
  ay: acceleration_y (float)
  az: acceleration_z (float)
  # rad/s
  gx: gyro_x (float)
  gy: gyro_y (float)
  gz: gyro_z (float)
  # °C
  temp: temp (float)
  # BPM
  heart_rate: heart_rate (float)
  # %
  spo2: spo2 (int)
  # dBm
  rssi: wi-fi signal (int)
  # %
  battery: battery_level (int)
```

## 📡 Protocolo de Comunicación MQTT

El ESP32 debe publicar datos formateados en cadenas JSON puras bajo la siguiente nomenclatura jerárquica de tópicos:

- Tópico Base: `healthwatch/{id_patient}/{id_device}/biometrics`

- Ejemplo Práctico: `healthwatch/patient_01/esp32_01/biometrics`

Estructura de Payload JSON Esperada:

```json
{
  "id_patient": "adulto_mayor_42",
  "id_device": "esp32_01",
  "ax": 0.05,
  "ay": -0.12,
  "az": 9.81,
  "gx": 0.0,
  "gy": 0.02,
  "gz": -0.01,
  "temp": 36.6,
  "heart_rate": 72.5,
  "spo2": 98,
  "rssi": -55,
  "battery": 87
}
```
