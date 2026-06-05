import datetime
from firebase_admin import messaging
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import db

def revisar_medicamentos_y_notificar():
    hora_actual = datetime.datetime.now().strftime("%I:%M %p").lower() 
    print(f"Scheduler => Revisando medicamentos para las: {hora_actual}")
    
    try:
        # Traemos los pacientes
        pacientes_ref = db.collection('pacientes').stream()
        
        for paciente in pacientes_ref:
            datos_paciente = paciente.to_dict()
            paciente_id = paciente.id
            cuidadores = datos_paciente.get("cuidadores_asignados", [])
            
            # Buscamos medicamentos activos de este paciente
            medicamentos_ref = db.collection('pacientes').document(paciente_id).collection('medicamentos')
            meds_activos = medicamentos_ref.where('activo', '==', True).stream()
            
            for med in meds_activos:
                datos_med = med.to_dict()
                horas_programadas = datos_med.get("horas", [])
                nombre_med = datos_med.get("nombre", "Medicamento")
                
                # 3. Revisa la hora actual con las programadas y avisa
                if hora_actual in horas_programadas:
                    for uid_cuidador in cuidadores:
                        usuario_doc = db.collection('usuarios').document(uid_cuidador).get()
                        
                        if usuario_doc.exists:
                            token_celular = usuario_doc.to_dict().get("fcm_token_celular")
                            
                            if token_celular:
                                enviar_notificacion_push(token_celular, nombre_med)
                                
    except Exception as e:
        print(f"Error en el motor de revisión: {e}")

def enviar_notificacion_push(token: str, medicamento: str):
    mensaje = messaging.Message(
        notification=messaging.Notification(
            title="Recordatorio de Medicamento",
            body=f"Es hora de administrar: {medicamento}",
        ),
        token=token,
    )
    
    try:
        respuesta = messaging.send(mensaje)
        print(f"Notificación enviada con éxito: {respuesta}")
    except Exception as e:
        print(f"Error al enviar notificación al token {token}: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(revisar_medicamentos_y_notificar, 'interval', minutes=1)