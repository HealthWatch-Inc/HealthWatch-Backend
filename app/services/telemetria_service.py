from influxdb_client_3 import InfluxDBClient3
import os
import pandas as pd
from app.core.config import INFLUX_HOST, INFLUX_TOKEN, INFLUX_DATABASE

client = InfluxDBClient3(host=INFLUX_HOST, token=INFLUX_TOKEN, database=INFLUX_DATABASE)

def obtener_historial_paciente(paciente_id: str) -> list:
    query = f"""
        SELECT time, heart_rate, spo2, battery, ax, ay, az
        FROM biometrics
        WHERE id_patient = '{paciente_id}'
          AND time >= now() - INTERVAL '7 days'
        ORDER BY time DESC
        LIMIT 1
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

def obtener_ultima_ventana(paciente_id: str, tamanio: int = 30) -> list:
    """
    Obtiene las últimas 'tamanio' lecturas de heart_rate, spo2, temp
    desde InfluxDB, ordenadas de la más antigua a la más reciente.
    """
    query = f"""
        SELECT time, heart_rate, spo2, temp
        FROM biometrics
        WHERE id_patient = '{paciente_id}'
        ORDER BY time DESC
        LIMIT {tamanio}
    """
    try:
        tabla = client.query(query=query, language="sql")
        df = tabla.to_pandas()
        if df.empty:
            return []   # o podrías lanzar una excepción
        df['time'] = df['time'].astype(str)
        registros = df.to_dict(orient='records')
        registros.reverse()   # orden cronológico ascendente
        return registros
    except Exception as e:
        print(f"Error al consultar InfluxDB: {e}")
        return []   # o puedes lanzar una excepción HTTP 500

def obtener_ultima_ventana_imu(paciente_id: str, tamanio: int = 20) -> list:
    """
    Obtiene las últimas 'tamanio' lecturas de acelerómetro y giroscopio
    desde InfluxDB, ordenadas de la más antigua a la más reciente.
    """
    query = f"""
        SELECT time, ax, ay, az, gx, gy, gz
        FROM biometrics
        WHERE id_patient = '{paciente_id}'
        ORDER BY time DESC
        LIMIT {tamanio}
    """
    try:
        tabla = client.query(query=query, language="sql")
        df = tabla.to_pandas()
        if df.empty:
            return []
        df['time'] = df['time'].astype(str)
        registros = df.to_dict(orient='records')
        registros.reverse()  # orden ascendente (antiguo a nuevo)
        return registros
    except Exception as e:
        print(f"Error al consultar InfluxDB para IMU: {e}")
        return []
