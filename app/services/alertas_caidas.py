import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import db
from app.services.telemetria_service import obtener_ultima_ventana_imu
from app.services.ml_fall_service import predecir_caida
from firebase_admin import messaging

# Diccionario para evitar notificaciones repetidas (cooldown de 5 minutos por paciente)
ultima_alerta_caida = {}

def enviar_notificacion_caida(token: str, paciente_nombre: str, probabilidad: float):
    titulo = "⚠️ Alerta de Caída Detectada"
    cuerpo = f"{paciente_nombre} ha sufrido una posible caída (probabilidad: {probabilidad:.1%}). Revise inmediatamente."
    mensaje = messaging.Message(
        notification=messaging.Notification(title=titulo, body=cuerpo),
        token=token,
    )
    try:
        response = messaging.send(mensaje)
        print(f"Notificación de caída enviada a {paciente_nombre}: {response}")
    except Exception as e:
        print(f"Error enviando notificación de caída a {token}: {e}")

def revisar_caidas_todos_pacientes():
    print(f"[{datetime.datetime.now()}] Ejecutando detección automática de caídas...")
    pacientes_ref = db.collection("pacientes").stream()
    for doc in pacientes_ref:
        paciente_id = doc.id
        data = doc.to_dict()
        nombre = data.get("nombre_completo", "Paciente")
        cuidadores = data.get("cuidadores_asignados", [])
        
        ventana = obtener_ultima_ventana_imu(paciente_id, tamanio=20)
        if len(ventana) < 20:
            # print(f"Paciente {paciente_id}: solo {len(ventana)} lecturas IMU, omitiendo")
            continue
        
        ax_vals = [p['ax'] for p in ventana]
        ay_vals = [p['ay'] for p in ventana]
        az_vals = [p['az'] for p in ventana]
        gx_vals = [p['gx'] for p in ventana]
        gy_vals = [p['gy'] for p in ventana]
        gz_vals = [p['gz'] for p in ventana]
        
        prob, es_caida = predecir_caida(ax_vals, ay_vals, az_vals, gx_vals, gy_vals, gz_vals)
        
        # Guardar última predicción en Firestore (opcional)
        doc.reference.set({"ultima_probabilidad_caida": prob, "ultima_deteccion_caida": es_caida, "ultima_actualizacion_caida": datetime.datetime.now().isoformat()}, merge=True)
        
        # Notificar si es caída, con cooldown de 5 minutos
        if es_caida:
            ahora = datetime.datetime.now()
            if paciente_id not in ultima_alerta_caida or (ahora - ultima_alerta_caida[paciente_id]).seconds > 300:
                ultima_alerta_caida[paciente_id] = ahora
                for uid in cuidadores:
                    user_doc = db.collection("usuarios").document(uid).get()
                    if user_doc.exists:
                        token = user_doc.to_dict().get("fcm_token_celular")
                        if token:
                            enviar_notificacion_caida(token, nombre, prob)

# Inicializar scheduler
scheduler_caidas = BackgroundScheduler()
scheduler_caidas.add_job(revisar_caidas_todos_pacientes, 'interval', seconds=10)  # cada 10 segundos