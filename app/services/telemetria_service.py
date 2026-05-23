# app/services/telemetria_service.py
from influxdb_client_3 import InfluxDBClient3
import os
import pandas as pd

HOST = os.getenv("INFLUXDB3_HOST_URL", "http://localhost:8181")
TOKEN = os.getenv("INFLUXDB3_AUTH_TOKEN", "apiv3_RE8r67lajh9RM7KoR5Hz1MvNaAzI5OeGtbmqFEtYkPcsZf_axngEOVXONc30tj73xOO3SP91B-vsmIyMF2YeHw")
DATABASE = os.getenv("INFLUXDB3_DATABASE_NAME", "health-watch")

client = InfluxDBClient3(host=HOST, token=TOKEN, database=DATABASE)

def obtener_historial_paciente(paciente_id: str, limite: int = 50) -> list:
    query = f"""
        SELECT time, heart_rate, spo2, battery, ax, ay, az
        FROM biometrics
        WHERE id_patient = '{paciente_id}'
        ORDER BY time DESC
        LIMIT {limite}
    """
    
    try:
        tabla = client.query(query=query, language="sql")
        
        df = tabla.to_pandas()
        
        if df.empty:
            return []

        df['time'] = df['time'].astype(str)

        return df.to_dict(orient='records')
        
    except Exception as e:
        print(f"Error al consultar InfluxDB: {e}")
        return []