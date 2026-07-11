# 🏥 HealthWatch API - Backend & IoT Infrastructure

Este repositorio contiene la arquitectura backend y la infraestructura de datos para **HealthWatch**, un sistema de monitoreo IoT en tiempo real diseñado para supervisar los signos vitales de adultos mayores. 

El sistema integra dispositivos portátiles (ESP32), una aplicación móvil (React Native) y un backend robusto basado en Python que gestiona bases de datos híbridas (documentales y de series temporales).

## 🏗️ Arquitectura y División de Tareas

El proyecto utiliza una arquitectura de microservicios y bases de datos especializadas para maximizar el rendimiento y la seguridad:

* **Aplicación Móvil (React Native):**
    * Comunicación directa con Firebase para Login y Registro.
* **Backend (Python / FastAPI):**
    * Actúa como capa de seguridad (validación de tokens JWT de Firebase).
    * Sirve el historial de telemetría extrayendo datos de InfluxDB.
    * Utiliza `APScheduler` para ejecutar revisiones periódicas en segundo plano (ej. recordatorios de medicinas).
    * Integración con la API de Expo Push Notifications para enviar alertas en tiempo real a los dispositivos móviles.
    * Ejecución de modelos de Machine Learning (LSTM) integrados nativamente para inferencia en tiempo real (clasificación de salud cardíaca y detección de caídas).
* **Infraestructura IoT (Docker):**
    * **HiveMQ:** Broker MQTT escalable que recibe y enruta la telemetría del reloj ESP32.
    * **Telegraf:** Agente de ingesta que traduce los datos de MQTT y los inserta en InfluxDB.
    * **InfluxDB v3:** Base de datos de series temporales de alto rendimiento.

---

## 📋 Requisitos Previos

* **Python:** Versión 3.10 o superior (Desarrollado en entorno Python 3.14.5).
* **Docker Desktop:** Con integración WSL 2 (si se ejecuta en Windows).
* **Credenciales:** Archivo `firebase-credentials.json` en la raíz del proyecto.
* **Entorno:** Archivo `.env` con las variables de InfluxDB (`INFLUXDB3_HOST_URL`, `INFLUXDB3_DATABASE_NAME`, `INFLUXDB3_AUTH_TOKEN`) y las de HiveMQ (`HIVEMQ_HOST_URL`, `HIVEMQ_PORT`, `HIVEMQ_USERNAME`, `HIVEMQ_PASSWORD`).

### Dependencias del Entorno (requirements.txt)

```text
# Servidor web y framework 
fastapi 
uvicorn
python-dotenv
apscheduler

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
    * nombre_completo: String (ej. "Juan Perez")
    * rol: String ("cuidador" o "familiar")
    * telefono: String (ej. "987654321")
    * expo_token: String (Token físico para recibir notificaciones Push vía Expo).

* **Colección Principal: pacientes** (Adultos Mayores)
    * ID de Documento: Identificador único del paciente (ej. "paciente_autorizado_1").
    * nombre_completo: String (ej. "Ana María Gómez")
    * edad: Number (ej. 74)
    * bateria_actual: Number (Último % de batería registrado del reloj)
    * cuidadores_asignados: Array de Strings (Contiene los UIDs de los usuarios autorizados)
    * **Campos de Machine Learning (Actualizados en segundo plano):**
        * ultima_clasificacion: String ("okay", "warning", "bad")
        * ultima_actualizacion_ml: String (Timestamp ISO)
        * ultima_probabilidad_caida: Number (Float, ej. 0.3221)
        * ultima_deteccion_caida: Boolean (true/false)
        * ultima_actualizacion_caida: String (Timestamp ISO)
        
    * **Sub-colección: contactos** (Red de emergencia)
        * ID de Documento: String (Autogenerado)
        * name: String (ej. "Antonio Banderas")
        * phone: String (ej. "970464752")
        * relation: String (ej. "Primo")

    * **Sub-colección: medicamentos** (Sistema de recordatorios)
        * ID de Documento: String (Autogenerado)
        * nombre: String (ej. "Losartán")
        * horas: Array de Strings (Formato 24h "%H:%M", ej. ["08:00", "20:00"])
        * frecuencia: String (ej. "Diario")
        
    * **Sub-colección: objetivos** (Metas físicas)
        * ID de Documento: String (ej. "actividad_fisica")
        * pasos_diarios: Number (ej. 5000)

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

### Endpoints:

* **Módulo de usuarios:**

    * `GET /api/usuarios/me`: Retorna el perfil (nombre, rol, teléfono) del usuario autenticado cruzando datos de Auth y Firestore.  
    * `PUT /api/usuarios/telefono`: Actualiza el número telefónico del perfil actual.  
    * `PUT /api/usuarios/expo-token`: Guarda o actualiza el token de Expo para el envío de notificaciones push.  
    * `PUT /api/usuarios/fcm-token`: Registra o actualiza el FCM Token del dispositivo móvil del cuidador autenticado para habilitar alertas Push.

* **Módulo de pacientes:**

    * `GET /api/pacientes/`: Lista todos los pacientes asignados al cuidador autenticado.  
    * `GET /api/pacientes/{paciente_id}`: Obtiene el perfil base de un paciente verificando permisos de acceso.  
    * `GET /api/pacientes/{paciente_id}/telemetria`: Extrae el historial reciente de signos vitales (InfluxDB).  

* **Módulo de medicamentos:**

    * `POST /api/medicamentos/{paciente_id}`: Crea un nuevo recordatorio de medicamento para un paciente.
    * `GET /api/medicamentos/{paciente_id}`: Lista todos los medicamentos programados del paciente.
    * `PUT /api/medicamentos/{paciente_id}/{medicamento_id}`: Modifica los datos (horas, nombre, frecuencia) de un medicamento existente.
    * `DELETE /api/medicamentos/{paciente_id}/{medicamento_id}`: Realiza el borrado físico de un recordatorio de medicamento.


* **Módulo de contactos:**

    * `POST /api/contactos/{paciente_id}`: Añade un contacto de emergencia (nombre, teléfono, relación). 
    * `GET /api/contactos/{paciente_id}`: Lista los contactos de emergencia disponibles.  
    * `PUT /api/contactos/{paciente_id}/{contacto_id}`: Edita la información de un contacto.  
    * `DELETE /api/contactos/{paciente_id}/{contacto_id}`: Elimina un contacto de la lista. 

* **Módulo de actividad física:**

    * `PUT /api/actividad-fisica/{paciente_id}`: Actualiza o establece el objetivo diario de pasos.  
    * `GET /api/actividad-fisica/{paciente_id}`: Consulta la meta actual de pasos del paciente.  
    * `DELETE /api/actividad-fisica/{paciente_id}`: Remueve el objetivo físico configurado.

* **Módulo de autenticación:** 

    * `POST /api/auth/login-prueba`: Simulador de login que devuelve un token JWT válido para realizar pruebas manuales en Swagger sin necesidad de la app móvil.  