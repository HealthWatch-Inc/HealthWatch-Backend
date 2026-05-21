import sys
import time
import json
import random
import math
import paho.mqtt.client as mqtt

if len(sys.argv) == 3:
    ID_PATIENT = sys.argv[1]
    ID_DEVICE = sys.argv[2]
else:
    ID_PATIENT = "adulto_mayor_test"
    ID_DEVICE = "dispositivo_reloj_01"

# Configuración
BROKER = "localhost"
PORT = 1883
TOPIC = f"healthwatch/{ID_PATIENT}/{ID_DEVICE}/biometrics"

client = mqtt.Client()

print("Esperando a que el broker MQTT esté listo...")
while True:
    try:
        client.connect(BROKER, PORT, 60)
        break
    except Exception as e:
        print(f"Broker no disponible: {e}")
        time.sleep(2)

print("¡Conectado al Broker MQTT! Iniciando envío de datos simulados...")

# Variables base para simular cambios suaves (caminata aleatoria)
heart_rate = 72.0
spo2 = 98
battery = 100
tick = 0

while True:
    tick += 1
    
    # 1. Simulación de Signos Vitales (Variaciones suaves)
    heart_rate += random.uniform(-1.5, 1.5)
    heart_rate = max(60.0, min(heart_rate, 95.0)) # Límites normales
    
    if random.random() > 0.95:  # Pequeño bache ocasional en SpO2
        spo2 = random.randint(95, 97)
    else:
        spo2 = random.randint(97, 99)
        
    # 2. Simulación de Red y Batería
    rssi = random.randint(-65, -45)
    if tick % 60 == 0 and battery > 1: # Baja 1% de batería cada 60 segundos ficticios
        battery -= 1

    # 3. Simulación de Movimiento de Muñeca Fisiológico (Ruido base en reposo/caminata leve)
    # Usamos senos/cosenos para que el acelerómetro dibuje ondas en Grafana
    ax = 0.1 * math.sin(tick * 0.5) + random.uniform(-0.05, 0.05)
    ay = 0.2 * math.cos(tick * 0.3) + random.uniform(-0.05, 0.05)
    az = 9.81 + random.uniform(-0.1, 0.1) # Gravedad base en Z
    
    gx = 0.02 * math.sin(tick * 0.2)
    gy = 0.01 * math.cos(tick * 0.4)
    gz = random.uniform(-0.01, 0.01)

    # 4. SIMULACIÓN DE EMERGENCIA (Cada 120 segundos simula una caída fuerte)
    if tick % 120 == 0:
        print("⚠️ [MOCK] Simulando evento de caída detectada...")
        ax, ay, az = random.uniform(25.0, 35.0), random.uniform(20.0, 30.0), random.uniform(-5.0, 5.0) # Impacto masivo
        gx, gy, gz = random.uniform(5.0, 10.0), random.uniform(5.0, 10.0), random.uniform(5.0, 10.0)
        heart_rate = random.uniform(115.0, 135.0) # Taquicardia por susto
        spo2 = 94 # Caída de oxígeno transitoria

    # Payload adaptado al nuevo esquema (id_device)
    payload = {
        "id_patient": ID_PATIENT,
        "id_device": ID_DEVICE,
        "ax": round(ax, 3),
        "ay": round(ay, 3),
        "az": round(az, 3),
        "gx": round(gx, 4),
        "gy": round(gy, 4),
        "gz": round(gz, 4),
        "temp": round(36.4 + random.uniform(-0.3, 0.3), 1),
        "heart_rate": round(heart_rate, 1),
        "spo2": int(spo2),
        "rssi": int(rssi),
        "battery": int(battery)
    }

    client.publish(TOPIC, json.dumps(payload))
    time.sleep(1.0) # Envia cada 1 segundo exacto