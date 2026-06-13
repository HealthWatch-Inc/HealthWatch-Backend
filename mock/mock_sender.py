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

BROKER = "localhost"
PORT = 1883
TOPIC = f"healthwatch/{ID_PATIENT}/{ID_DEVICE}/biometrics"

# Callback cuando el cliente se conecta al broker
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Conectado al broker MQTT en {BROKER}:{PORT}")
    else:
        print(f"Fallo de conexión, código de error: {rc}")

# Crear el cliente MQTT con la nueva API
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect

print("Intentando conectar al broker MQTT...")
client.connect(BROKER, PORT, 60)
client.loop_start()  # Iniciar el loop de red en segundo plano

heart_rate = 72.0
spo2 = 98
battery = 100
tick = 0

while True:
    tick += 1

    heart_rate += random.uniform(-1.5, 1.5)
    heart_rate = max(60.0, min(heart_rate, 95.0))

    if random.random() > 0.95:
        spo2 = random.randint(95, 97)
    else:
        spo2 = random.randint(97, 99)

    rssi = random.randint(-65, -45)
    if tick % 60 == 0 and battery > 1:
        battery -= 1

    ax = 0.1 * math.sin(tick * 0.5) + random.uniform(-0.05, 0.05)
    ay = 0.2 * math.cos(tick * 0.3) + random.uniform(-0.05, 0.05)
    az = 9.81 + random.uniform(-0.1, 0.1)

    gx = 0.02 * math.sin(tick * 0.2)
    gy = 0.01 * math.cos(tick * 0.4)
    gz = random.uniform(-0.01, 0.01)

    # Cada 120 ticks simula una caída
    if tick % 120 == 0:
        print("⚠️ [MOCK] Simulando evento de caída detectada...")
        ax, ay, az = random.uniform(25.0, 35.0), random.uniform(20.0, 30.0), random.uniform(-5.0, 5.0)
        gx, gy, gz = random.uniform(5.0, 10.0), random.uniform(5.0, 10.0), random.uniform(5.0, 10.0)
        heart_rate = random.uniform(115.0, 135.0)
        spo2 = 94

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

    # Publicar el mensaje
    result = client.publish(TOPIC, json.dumps(payload))
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"Datos transmitidos exitosamente a tópico: {TOPIC}")
    else:
        print(f"Error al publicar: {result.rc}")

    time.sleep(1.0)