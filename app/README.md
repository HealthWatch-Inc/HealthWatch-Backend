# 🏥 HealthWatch API - Backend & IoT Infrastructure

Este repositorio contiene la arquitectura backend y la infraestructura de datos para **HealthWatch**, un sistema de monitoreo IoT en tiempo real diseñado para supervisar los signos vitales de adultos mayores. 

El sistema integra dispositivos portátiles (ESP32), una aplicación móvil (React Native) y un backend robusto basado en Python que gestiona bases de datos híbridas (documentales y de series temporales).

## 🏗️ Arquitectura y División de Tareas

El proyecto utiliza una arquitectura de microservicios y bases de datos especializadas para maximizar el rendimiento y la seguridad:

* **Aplicación Móvil (React Native):**
    * Comunicación directa con Firebase para Login y Registro.
    * Suscripción en tiempo real a la colección de Alertas (Firestore).
* **Backend (Python / FastAPI):**
    * Actúa como capa de seguridad (validación de tokens JWT de Firebase).
    * Sirve el historial de telemetría extrayendo datos de InfluxDB.
    * Preparado para futuras implementaciones de Machine Learning (ML).
* **Infraestructura IoT (Docker):**
    * **Mosquitto:** Broker MQTT que recibe los latidos del reloj ESP32.
    * **Telegraf:** Agente de ingesta que traduce los datos de MQTT y los inserta en InfluxDB.
    * **InfluxDB v3:** Base de datos de series temporales de alto rendimiento.

---

## 📋 Requisitos Previos

* **Python:** Versión 3.10 o superior (Desarrollado en entorno Python 3.14.5).
* **Docker Desktop:** Con integración WSL 2 (si se ejecuta en Windows).
* **Credenciales:** Archivo `firebase-credentials.json` en la raíz del proyecto.
* **Entorno:** Archivo `.env` con las variables de InfluxDB (`INFLUXDB3_AUTH_TOKEN`, `INFLUXDB3_DATABASE_NAME`).

### Dependencias del Entorno (requirements.txt)

```text
# Servidor web y framework 
fastapi 
uvicorn
python-dotenv

# Conexión con InfluxDB y procesamiento de datos 
influxdb-client-v3 
pandas 
pyarrow 

# SDK de Firebase y utilidades de red 
firebase-admin 
requests 
```

---

## 🗄️ Estructura de Bases de Datos

El sistema utiliza un enfoque híbrido, separando los datos relacionales/estáticos de los datos masivos de telemetría.

### 1. Firebase Firestore (Datos Estáticos y Relacionales)

* **Colección Principal: usuarios** (Cuidadores y Familiares)
    * ID de Documento: UID proporcionado por Firebase Auth.
    * nombre: String (ej. "Juan Perez")
    * rol: String ("cuidador" o "familiar")
    * pacientes_asignados: Array de Strings (ej. ["paciente_01", "paciente_02"])

* **Colección Principal: pacientes** (Adultos Mayores)
    * ID de Documento: Identificador único del paciente (ej. "paciente_01").
    * nombre_completo: String (ej. "Arturo Gomez")
    * id_reloj_esp32: String (MAC o ID del hardware, ej. "esp_mac_001")
    * contactos_emergencia: Array de Objetos (nombres y teléfonos)
    * bateria_actual: Number (Último % de batería registrado)
    * **Sub-colección: alertas** (Historial de emergencias del paciente)
        * tipo: String ("caida", "oxigeno_bajo", "taquicardia")
        * fecha_hora: Timestamp
        * estado: String ("revisada", "no_revisada")

### 2. InfluxDB v3 (Datos de Telemetría)

* **Bucket:** health-watch
* **Measurement (Tabla):** biometrics
* **Tags (Índices):** id_patient, id_device
* **Fields (Valores):** heart_rate, spo2, temp, ax, ay, az, battery

---

## 🚀 Instalación y Despliegue Local


Antes de continuar, en la carpeta raíz está el README.md para configurar docker, se deben seguir esos pasos. Luego, sigue estos pasos para levantar el entorno de desarrollo:

### 1. Levantar la Infraestructura (Docker)

El proyecto utiliza contenedores para la base de datos y el broker de mensajería. Los datos se persisten localmente a través de volúmenes definidos en el docker-compose.yml.

- Iniciar los contenedores en segundo plano

```bash
docker compose up -d
```

### 2. Configurar el Backend (Python)

Abre una nueva terminal en la raíz del proyecto y ejecuta:

1. Crear el entorno virtual

```bash
python -m venv venv
```

2. Activar el entorno virtual (Windows)
```bash
.\venv\Scripts\activate
```
3. Instalar dependencias del sistema
```bash
pip install -r requirements.txt
```
### 3. Ejecutar el Servidor

Con el entorno virtual activado y los contenedores corriendo, levanta la API de FastAPI:

```bash
uvicorn app.main:app --reload
```
---

## 📖 Documentación de la API (Swagger UI)

FastAPI genera automáticamente documentación interactiva basada en OpenAPI. Una vez que el servidor esté en ejecución, puedes explorar y probar todos los endpoints accediendo a:

👉 http://127.0.0.1:8000/docs

### Endpoints Principales:

* POST /api/auth/login-prueba: Genera un token JWT simulado para pruebas de desarrollo mediante peticiones a Google Identity Toolkit.
* GET /api/pacientes/: Lista los pacientes asignados al cuidador autenticado.
* GET /api/pacientes/{paciente_id}: Obtiene el perfil estático de un paciente específico desde Firestore, validando que el cuidador esté asignado.
* GET /api/pacientes/{paciente_id}/telemetria: Cruza la validación de seguridad de Firestore y extrae el historial biométrico reciente del paciente desde InfluxDB usando SQL estándar.