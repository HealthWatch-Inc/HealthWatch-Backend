import datetime
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import db
from google.cloud import firestore
from app.services.telemetria_service import obtener_ultima_ventana_imu
from app.services.ml_fall_service import predecir_caida

# Diccionario para evitar notificaciones repetidas (cooldown de 5 minutos por paciente)
ultima_alerta_caida = {}

def enviar_notificacion_caida(token: str, paciente_nombre: str, probabilidad: float):
    titulo = "🚨 Alerta de Caída Detectada"
    cuerpo = f"{paciente_nombre} ha sufrido una posible caída (probabilidad: {probabilidad:.1%}). Revise inmediatamente."
    
    url = "https://exp.host/--/api/v2/push/send"
    payload = {
        "to": token,
        "sound": "default",
        "title": titulo,
        "body": cuerpo
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Notificación de caída enviada a {paciente_nombre}: {response.status_code}")
    except Exception as e:
        print(f"Error enviando notificación de caída a {token}: {e}")

def revisar_caidas_todos_pacientes():
    print(f"\n[Modelo de caídas] [{datetime.datetime.now().strftime('%H:%M:%S')}] Iniciando evaluación...")
    pacientes_ref = db.collection("pacientes").stream()
    
    for doc in pacientes_ref:
        paciente_id = doc.id
        data = doc.to_dict()
        nombre = data.get("nombre_completo", "Paciente")
        cuidadores = data.get("cuidadores_asignados", [])
        
        ventana = obtener_ultima_ventana_imu(paciente_id, tamanio=20)
        if len(ventana) < 20:
            continue
        
        ax_vals = [p['ax'] for p in ventana]
        ay_vals = [p['ay'] for p in ventana]
        az_vals = [p['az'] for p in ventana]
        gx_vals = [p['gx'] for p in ventana]
        gy_vals = [p['gy'] for p in ventana]
        gz_vals = [p['gz'] for p in ventana]
        
        prob, es_caida = predecir_caida(ax_vals, ay_vals, az_vals, gx_vals, gy_vals, gz_vals)
        
        # LOG DETALLADO CRÍTICO
        print(f"  -> Paciente: {nombre} -> Probabilidad de Caída: {prob:.2%} | Clasificación: {'CAÍDA' if es_caida else 'NORMAL'}")
        
        doc.reference.set({"ultima_probabilidad_caida": prob, "ultima_deteccion_caida": es_caida, "ultima_actualizacion_caida": datetime.datetime.now().isoformat()}, merge=True)
        
        if es_caida:
            ahora = datetime.datetime.now()
            
            # Guardar en el historial de caídas (subcolección)
            try:
                caida_data = {
                    "probabilidad": round(float(prob), 4),
                    "timestamp": ahora.isoformat(),
                    "fecha_legible": ahora.strftime("%Y-%m-%d %H:%M:%S"),
                    "nombre_paciente": nombre,
                    "notificada": False
                }
                db.collection("pacientes").document(paciente_id).collection("caidas").add(caida_data)
                print(f"  -> Caída registrada en historial para {nombre}")
            except Exception as e:
                print(f"  -> Error guardando historial de caída: {e}")
            
            # Cooldown de 5 minutos para notificaciones push
            if paciente_id not in ultima_alerta_caida or (ahora - ultima_alerta_caida[paciente_id]).seconds > 300:
                ultima_alerta_caida[paciente_id] = ahora
                # Marcar la última caída como notificada
                try:
                    docs = db.collection("pacientes").document(paciente_id).collection("caidas").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).get()
                    for d in docs:
                        d.reference.update({"notificada": True})
                except Exception as e:
                    print(f"  -> Error marcando caída como notificada: {e}")
                
                for uid in cuidadores:
                    user_doc = db.collection("usuarios").document(uid).get()
                    if user_doc.exists:
                        token = user_doc.to_dict().get("expo_token")
                        if token:
                            enviar_notificacion_caida(token, nombre, prob)

# Inicializar scheduler
scheduler_caidas = BackgroundScheduler()
scheduler_caidas.add_job(revisar_caidas_todos_pacientes, 'interval', seconds=10)