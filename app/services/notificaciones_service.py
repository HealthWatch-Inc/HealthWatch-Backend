import datetime
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import db
from google.cloud.firestore_v1.base_query import FieldFilter
from zoneinfo import ZoneInfo

def revisar_medicamentos_y_notificar():
    zona_peru = ZoneInfo("America/Lima")
    hora_actual = datetime.datetime.now(zona_peru).strftime("%H:%M")
    print(f"Scheduler => Revisando medicamentos para las: {hora_actual}")
    
    try:
        meds_programados = db.collection_group('medicamentos').where(
            filter=FieldFilter('horas', 'array_contains', hora_actual)
        ).stream()
        
        for med in meds_programados:
            datos_med = med.to_dict()
            nombre_med = datos_med.get("nombre", "Medicamento")

            print(f"Medicamento encontrado: {nombre_med}")
            
            paciente_ref = med.reference.parent.parent 
            paciente_doc = paciente_ref.get()
            
            if paciente_doc.exists:
                cuidadores = paciente_doc.to_dict().get("cuidadores_asignados", [])

                print(f"Cuidadores asignados: {cuidadores}")

                for uid_cuidador in cuidadores:
                    usuario_doc = db.collection('usuarios').document(uid_cuidador).get()
                    
                    if usuario_doc.exists:
                        token_celular = usuario_doc.to_dict().get("expo_token")

                        print(f"Token encontrado: {token_celular}")
                        
                        if token_celular:
                            enviar_notificacion_push(token_celular, nombre_med)
                            
    except Exception as e:
        print(f"Error en el motor de revisión: {e}")

def enviar_notificacion_push(token: str, medicamento: str):
    url = "https://exp.host/--/api/v2/push/send"
    
    payload = {
        "to": token,
        "sound": "default",
        "title": "Recordatorio de Medicamento",
        "body": f"Es hora de administrar: {medicamento}"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print(f"Error al enviar notificación a través de Expo: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(revisar_medicamentos_y_notificar, 'interval', minutes=1)
