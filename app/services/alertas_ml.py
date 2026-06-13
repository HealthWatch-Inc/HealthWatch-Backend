import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import db
from app.services.telemetria_service import obtener_ultima_ventana
from app.services.ml_services import predecir_ventana
from firebase_admin import messaging

# Diccionario para evitar notificaciones repetidas (cooldown de 5 minutos por paciente y nivel)
ultima_alerta = {}

def enviar_notificacion(token: str, paciente_nombre: str, clasificacion: str):
    if clasificacion == "bad":
        titulo = "Alerta crítica de salud"
        cuerpo = f"{paciente_nombre} presenta signos severos de estrés o fatiga. Por favor revise."
    elif clasificacion == "warning":
        titulo = "Precaución"
        cuerpo = f"{paciente_nombre} muestra indicios de fatiga o estrés moderado."
    else:
        return  # no notificar para okay
    mensaje = messaging.Message(
        notification=messaging.Notification(title=titulo, body=cuerpo),
        token=token,
    )
    try:
        response = messaging.send(mensaje)
        print(f"Notificación enviada a {paciente_nombre}: {response}")
    except Exception as e:
        print(f"Error enviando a {token}: {e}")

def revisar_todos_pacientes():
    print(f"[{datetime.datetime.now()}] Ejecutando clasificación automática ML...")
    pacientes_ref = db.collection("pacientes").stream()
    for doc in pacientes_ref:
        paciente_id = doc.id
        data = doc.to_dict()
        nombre = data.get("nombre_completo", "Paciente")
        cuidadores = data.get("cuidadores_asignados", [])
        
        ventana = obtener_ultima_ventana(paciente_id, tamanio=30)
        if len(ventana) < 30:
            # print(f"Paciente {paciente_id}: solo {len(ventana)} lecturas, omitiendo")
            continue
        
        hr_vals = [p['heart_rate'] for p in ventana]
        spo2_vals = [p['spo2'] for p in ventana]
        temp_vals = [p['temp'] for p in ventana]
        categoria, _ = predecir_ventana(hr_vals, spo2_vals, temp_vals)
        
        # Guardar última clasificación en Firestore (opcional)
        doc.reference.set({"ultima_clasificacion": categoria, "ultima_actualizacion_ml": datetime.datetime.now().isoformat()}, merge=True)
        
        # Notificar si es warning o bad, con cooldown de 5 minutos
        if categoria in ["warning", "bad"]:
            ahora = datetime.datetime.now()
            clave = f"{paciente_id}_{categoria}"
            if clave not in ultima_alerta or (ahora - ultima_alerta[clave]).seconds > 300:
                ultima_alerta[clave] = ahora
                for uid in cuidadores:
                    user_doc = db.collection("usuarios").document(uid).get()
                    if user_doc.exists:
                        token = user_doc.to_dict().get("fcm_token_celular")
                        if token:
                            enviar_notificacion(token, nombre, categoria)

# Inicializar scheduler
scheduler_ml = BackgroundScheduler()
scheduler_ml.add_job(revisar_todos_pacientes, 'interval', seconds=15)  # cada 15 segundos