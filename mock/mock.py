import os
import sys
import time
import json
import random
import math
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()

if len(sys.argv) == 3:
    ID_PATIENT = sys.argv[1]
    ID_DEVICE = sys.argv[2]
else:
    ID_PATIENT = "paciente_autorizado_1"
    ID_DEVICE = "dispositivo_reloj_01"

# Configuración
BROKER = os.getenv("HIVEMQ_HOST_URL") or "localhost"
PORT = int(os.getenv("HIVEMQ_PORT") or 1883)
USERNAME = os.getenv("HIVEMQ_USERNAME") or "user"
PASSWORD = os.getenv("HIVEMQ_PASSWORD") or "password"
TOPIC = f"healthwatch/{ID_PATIENT}/{ID_DEVICE}/biometrics"

client = mqtt.Client(client_id=f"mock_sender_{ID_PATIENT}_{ID_DEVICE}")

print("Esperando a que el broker MQTT esté listo...")
while True:
    try:
        client.tls_set()
        client.username_pw_set(USERNAME, PASSWORD)
        client.connect(BROKER, PORT, 60)
        break
    except Exception as e:
        print(f"Broker no disponible: {e}")
        time.sleep(2)

print("Intentando conectar al broker MQTT...")
client.connect(BROKER, PORT, 60)
client.loop_start()  # Iniciar el loop de red en segundo plano

# Variables iniciales (antes del while)
heart_rate = 72.0
spo2 = 98
battery = 100
tick = 0

print("🚀 Iniciando simulación RÁPIDA enfocada en CAÍDAS (Ciclo de 60s)...")

while True:
    tick += 1
    
    # Ciclo reducido a 60 segundos para ahorrar datos en InfluxDB
    ciclo_actual = tick % 60 

    # Mantenemos los signos vitales normales y estáticos para no disparar alertas de salud
    heart_rate = random.uniform(70.0, 75.0)
    spo2 = 98
    temp = 36.5

    # =========================================================
    # FASE 1: ESTADO NORMAL (0 a 30 segundos)
    # =========================================================
    if ciclo_actual < 30:
        estado = "NORMAL"
        
        # Caminata normal (Gravedad en Z)
        ax = random.uniform(-1.0, 1.0)
        ay = random.uniform(1.5, 3.5)
        az = 9.81 + random.uniform(1.0, 2.0)
        gx, gy, gz = random.uniform(0.5, 2.0), random.uniform(0.5, 2.0), random.uniform(-0.5, 0.5)

    # =========================================================
    # FASE 2: EVENTO DE CAÍDA (30 a 60 segundos)
    # =========================================================
    else:
        estado = "CAÍDA_DETECTADA"

        if ciclo_actual == 30 or ciclo_actual == 31:
            # Impacto violento inicial (2 segundos)
            ax, ay, az = random.uniform(25.0, 35.0), random.uniform(20.0, 30.0), random.uniform(-10.0, 5.0)
            gx, gy, gz = random.uniform(15.0, 25.0), random.uniform(15.0, 25.0), random.uniform(15.0, 25.0)
        else:
            # Reposo absoluto de COSTADO en el suelo (llenará la ventana de 20s)
            ax = 9.81 + random.uniform(-0.1, 0.1) # Gravedad transferida al eje X
            ay = random.uniform(-0.1, 0.1)
            az = random.uniform(-0.1, 0.1)        # Z pierde la gravedad
            
            # Inmóvil
            gx, gy, gz = 0.0, 0.0, 0.0

    # Lógica de batería y señal
    rssi = random.randint(-65, -45)
    if tick % 60 == 0 and battery > 1:
        battery -= 1

    payload = {
        "id_patient": ID_PATIENT,
        "id_device": ID_DEVICE,
        "ax": round(ax, 3),
        "ay": round(ay, 3),
        "az": round(az, 3),
        "gx": round(gx, 4),
        "gy": round(gy, 4),
        "gz": round(gz, 4),
        "temp": round(temp, 1),
        "heart_rate": round(heart_rate, 1),
        "spo2": int(spo2),
        "rssi": int(rssi),
        "battery": int(battery)
    }

    client.publish(TOPIC, json.dumps(payload))
    print(f"[{estado}] 📤 IMU-X: {round(ax,1)} | IMU-Z: {round(az,1)}")
    time.sleep(1.0)