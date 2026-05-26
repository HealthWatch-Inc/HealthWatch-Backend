from influxdb_client_3 import InfluxDBClient3
import os
import pandas as pd
from app.core.config import INFLUX_HOST, INFLUX_TOKEN, INFLUX_DATABASE

client = InfluxDBClient3(host=INFLUX_HOST, token=INFLUX_TOKEN, database=INFLUX_DATABASE)

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