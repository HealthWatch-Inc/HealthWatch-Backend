"""
conftest.py - Fixtures y mocks compartidos para todas las pruebas.

Este archivo se ejecuta ANTES de la colección de tests.
Intercepta las inicializaciones pesadas de módulos (Firebase, InfluxDB, PyTorch)
para que los tests sean herméticos y no dependan de servicios externos.
"""
import os
import sys
import math
import datetime
from unittest.mock import MagicMock, patch, PropertyMock
from collections import OrderedDict

import pytest
import numpy as np
import pandas as pd


# ========================================================================
# PARCHEAR MÓDULOS PESADOS ANTES DE CUALQUIER IMPORTACIÓN DEL PROYECTO
# ========================================================================

# 1) Variables de entorno mínimas para que config.py no falle
os.environ.setdefault("INFLUXDB3_HOST_URL", "http://localhost:8181")
os.environ.setdefault("INFLUXDB3_DATABASE_NAME", "test_db")
os.environ.setdefault("INFLUXDB3_AUTH_TOKEN", "test_token_12345")
os.environ.setdefault("FIREBASE_WEB_API_KEY", "fake_api_key_for_testing")

# 2) Parchear firebase_admin ANTES de que app.core.config se importe
_firebase_patcher = patch("firebase_admin.credentials.Certificate", return_value=MagicMock())
_firebase_init_patcher = patch("firebase_admin.initialize_app", return_value=MagicMock())
_firebase_apps_patcher = patch.object(
    __import__("firebase_admin"), "_apps", new_callable=lambda: MagicMock(__bool__=lambda s: False)
)
_firestore_client_patcher = patch("firebase_admin.firestore.client")

_firebase_patcher.start()
_firebase_init_patcher.start()
_firebase_apps_patcher.start()
_mock_firestore_client = _firestore_client_patcher.start()

# 3) Parchear InfluxDBClient3 ANTES de que telemetria_service se importe
_mock_influx_class = patch("influxdb_client_3.InfluxDBClient3")
_mock_influx_class.start()

# 4) Prevenir que los servicios ML carguen archivos pickle/modelos reales
#    Parcheamos joblib.load y torch.load a nivel de módulo
_joblib_load_patcher = patch("joblib.load")
_mock_joblib_load = _joblib_load_patcher.start()

_torch_load_patcher = patch("torch.load")
_mock_torch_load = _torch_load_patcher.start()

# Configurar retornos por defecto para que los módulos ML se importen sin error
# ml_services.py espera: config dict, model state_dict, scaler, label_mapping
_mock_config_lstm = {
    "input_size": 3,
    "hidden_size": 64,
    "num_layers": 2,
    "num_classes": 3,
    "window_size": 30,
}
_mock_config_fall = {
    "input_size": 9,
    "hidden_size": 64,
    "num_layers": 2,
    "window_size": 20,
}
_mock_label_mapping = {"okay": 0, "warning": 1, "bad": 2}


def _fake_joblib_load(path):
    """Retorna objetos fake según el archivo solicitado."""
    path_str = str(path)
    if "config_lstm" in path_str:
        return _mock_config_lstm
    elif "label_mapping_lstm" in path_str:
        return _mock_label_mapping
    elif "scaler_lstm" in path_str:
        scaler = MagicMock()
        scaler.transform = MagicMock(
            side_effect=lambda x: x if isinstance(x, np.ndarray) else np.array(x)
        )
        return scaler
    elif "config_fall" in path_str:
        return _mock_config_fall
    elif "scaler_fall" in path_str:
        scaler = MagicMock()
        scaler.transform = MagicMock(
            side_effect=lambda x: x if isinstance(x, np.ndarray) else np.array(x)
        )
        return scaler
    else:
        return MagicMock()


_mock_joblib_load.side_effect = _fake_joblib_load


def _build_fake_state_dict_lstm_health():
    """
    Construye un state_dict con shapes correctas para HealthLSTM:
    input_size=3, hidden_size=64, num_layers=2, num_classes=3
    """
    import torch
    hs = 64
    is_ = 3
    nc = 3
    return OrderedDict({
        "lstm.weight_ih_l0": torch.randn(4 * hs, is_),
        "lstm.weight_hh_l0": torch.randn(4 * hs, hs),
        "lstm.bias_ih_l0": torch.randn(4 * hs),
        "lstm.bias_hh_l0": torch.randn(4 * hs),
        "lstm.weight_ih_l1": torch.randn(4 * hs, hs),
        "lstm.weight_hh_l1": torch.randn(4 * hs, hs),
        "lstm.bias_ih_l1": torch.randn(4 * hs),
        "lstm.bias_hh_l1": torch.randn(4 * hs),
        "fc.weight": torch.randn(nc, hs),
        "fc.bias": torch.randn(nc),
    })


def _build_fake_state_dict_fall():
    """
    Construye un state_dict con shapes correctas para FallLSTM:
    input_size=9, hidden_size=64, num_layers=2
    """
    import torch
    hs = 64
    is_ = 9
    return OrderedDict({
        "lstm.weight_ih_l0": torch.randn(4 * hs, is_),
        "lstm.weight_hh_l0": torch.randn(4 * hs, hs),
        "lstm.bias_ih_l0": torch.randn(4 * hs),
        "lstm.bias_hh_l0": torch.randn(4 * hs),
        "lstm.weight_ih_l1": torch.randn(4 * hs, hs),
        "lstm.weight_hh_l1": torch.randn(4 * hs, hs),
        "lstm.bias_ih_l1": torch.randn(4 * hs),
        "lstm.bias_hh_l1": torch.randn(4 * hs),
        "fc.weight": torch.randn(1, hs),
        "fc.bias": torch.randn(1),
    })


_health_lstm_state_dict = _build_fake_state_dict_lstm_health()
_fall_lstm_state_dict = _build_fake_state_dict_fall()


def _fake_torch_load(path, map_location=None):
    """Retorna un state_dict fake con shapes correctas según el modelo."""
    path_str = str(path)
    if "fall" in path_str:
        return _fall_lstm_state_dict
    return _health_lstm_state_dict


_mock_torch_load.side_effect = _fake_torch_load

# 5) Ahora SÍ podemos importar los módulos del proyecto (seguros de importar)
from app.core import config
from app.services import telemetria_service
from app.services import ml_services
from app.services import ml_fall_service


# ========================================================================
# FIXTURES DE DATOS SINTÉTICOS
# ========================================================================

@pytest.fixture
def fake_patient_data():
    """Paciente de prueba con cuidadores asignados."""
    return {
        "id": "paciente_test_001",
        "nombre_completo": "María García López",
        "edad": 78,
        "bateria_actual": 85,
        "cuidadores_asignados": ["uid_cuidador_1", "uid_cuidador_2"],
    }


@pytest.fixture
def fake_patient_no_caregivers():
    """Paciente sin cuidadores asignados."""
    return {
        "id": "paciente_sin_cuidadores",
        "nombre_completo": "Pedro Sin Cuidadores",
        "edad": 70,
        "bateria_actual": 50,
        "cuidadores_asignados": [],
    }


@pytest.fixture
def fake_patient_missing_caregivers():
    """Paciente sin el campo cuidadores_asignados."""
    return {
        "id": "paciente_sin_campo",
        "nombre_completo": "Ana Sin Campo",
        "edad": 65,
    }


@pytest.fixture
def fake_medication_data():
    """Medicamento de prueba."""
    return {
        "id": "med_test_001",
        "nombre": "Losartán 50mg",
        "horas": ["08:00", "14:00", "20:00"],
        "frecuencia": "Diario",
    }


@pytest.fixture
def fake_medication_single_hour():
    """Medicamento con una sola hora programada."""
    return {
        "id": "med_test_002",
        "nombre": "Aspirina 100mg",
        "horas": ["12:30"],
        "frecuencia": "Diario",
    }


@pytest.fixture
def fake_telemetry_window():
    """
    Ventana de 30 lecturas de telemetría biométrica.
    Datos en rango realista: HR 60-100, SpO2 95-100, Temp 36.0-37.5.
    """
    np.random.seed(42)
    n = 30
    return [
        {
            "time": f"2026-07-12T{10 + i // 60}:{i % 60:02d}:00Z",
            "heart_rate": round(float(np.clip(72 + np.random.randn() * 5, 60, 100)), 1),
            "spo2": int(np.clip(97 + np.random.randn() * 1.5, 95, 100)),
            "temp": round(float(np.clip(36.5 + np.random.randn() * 0.3, 36.0, 37.5)), 1),
        }
        for i in range(n)
    ]


@pytest.fixture
def fake_telemetry_window_anomalous():
    """
    Ventana de 30 lecturas con valores anómalos (HR alto, SpO2 bajo).
    Debería producir clasificación 'warning' o 'bad' en el modelo ML.
    """
    np.random.seed(99)
    n = 30
    return [
        {
            "time": f"2026-07-12T{10 + i // 60}:{i % 60:02d}:00Z",
            "heart_rate": round(float(np.clip(110 + np.random.randn() * 8, 100, 140)), 1),
            "spo2": int(np.clip(92 + np.random.randn() * 2, 88, 95)),
            "temp": round(float(np.clip(37.8 + np.random.randn() * 0.4, 37.2, 38.5)), 1),
        }
        for i in range(n)
    ]


@pytest.fixture
def fake_imu_window():
    """
    Ventana de 20 lecturas IMU (acelerómetro + giroscopio).
    Simula movimiento normal de caminata.
    """
    np.random.seed(42)
    n = 20
    return [
        {
            "time": f"2026-07-12T10:00:{i:02d}Z",
            "ax": round(float(0.1 * math.sin(i * 0.5) + np.random.randn() * 0.05), 3),
            "ay": round(float(0.2 * math.cos(i * 0.3) + np.random.randn() * 0.05), 3),
            "az": round(float(9.81 + np.random.randn() * 0.1), 3),
            "gx": round(float(0.02 * math.sin(i * 0.2) + np.random.randn() * 0.01), 4),
            "gy": round(float(0.01 * math.cos(i * 0.4) + np.random.randn() * 0.01), 4),
            "gz": round(float(np.random.randn() * 0.01), 4),
        }
        for i in range(n)
    ]


@pytest.fixture
def fake_imu_window_fall():
    """
    Ventana de 20 lecturas IMU simulando una caída.
    Los primeros 18 registros son normales, los últimos 2 tienen impacto alto.
    """
    np.random.seed(42)
    n = 20
    records = [
        {
            "time": f"2026-07-12T10:00:{i:02d}Z",
            "ax": round(float(0.1 * math.sin(i * 0.5)), 3),
            "ay": round(float(0.2 * math.cos(i * 0.3)), 3),
            "az": round(float(9.81 + np.random.randn() * 0.1), 3),
            "gx": round(float(0.02 * math.sin(i * 0.2)), 4),
            "gy": round(float(0.01 * math.cos(i * 0.4)), 4),
            "gz": round(float(np.random.randn() * 0.01), 4),
        }
        for i in range(n - 2)
    ]
    # Simular impacto de caída en los últimos 2 registros
    records.append({
        "time": f"2026-07-12T10:00:18Z",
        "ax": 28.5, "ay": 22.3, "az": -3.2,
        "gx": 18.0, "gy": 16.5, "gz": 8.0,
    })
    records.append({
        "time": f"2026-07-12T10:00:19Z",
        "ax": 0.05, "ay": 0.03, "az": 0.02,
        "gx": 0.0, "gy": 0.0, "gz": 0.0,
    })
    return records


@pytest.fixture
def fake_caregiver_data():
    """Datos de un cuidador con token Expo válido."""
    return {
        "uid": "uid_cuidador_1",
        "nombre_completo": "Juan Cuidador",
        "rol": "CUIDADOR",
        "expo_token": "ExponentPushToken[abc123xyz]",
        "telefono": "+51999888777",
    }


@pytest.fixture
def fake_caregiver_no_token():
    """Cuidador sin token de notificaciones."""
    return {
        "uid": "uid_cuidador_2",
        "nombre_completo": "Ana Sin Token",
        "rol": "CUIDADOR",
    }


# ========================================================================
# FIXTURES DE MOCKS PARA SERVICIOS EXTERNOS
# ========================================================================

@pytest.fixture
def mock_db():
    """
    Mock completo de Firestore db.
    Configura un paciente de prueba accesible por uid_cuidador_1.
    """
    db = MagicMock()

    # Paciente de prueba
    patient_doc = MagicMock()
    patient_doc.exists = True
    patient_doc.to_dict.return_value = {
        "nombre_completo": "María García López",
        "edad": 78,
        "bateria_actual": 85,
        "cuidadores_asignados": ["uid_cuidador_1", "uid_cuidador_2"],
    }
    patient_doc.id = "paciente_test_001"

    # Mock de collection("pacientes").document(id).get()
    db.collection.return_value.document.return_value.get.return_value = patient_doc

    # Mock de collection_group para medicamentos
    med_doc = MagicMock()
    med_doc.to_dict.return_value = {
        "nombre": "Losartán 50mg",
        "horas": ["08:00", "14:00", "20:00"],
    }
    med_doc.reference.parent.parent.get.return_value = patient_doc
    db.collection_group.return_value.where.return_value.stream.return_value = [med_doc]

    return db


@pytest.fixture
def mock_requests_post():
    """Mock de requests.post que captura payloads enviados."""
    with patch("app.services.notificaciones_service.requests.post") as mock_notif:
        with patch("app.services.alertas_ml.requests.post") as mock_ml:
            with patch("app.services.alertas_caidas.requests.post") as mock_caidas:
                mock_notif.return_value = MagicMock(status_code=200)
                mock_ml.return_value = MagicMock(status_code=200)
                mock_caidas.return_value = MagicMock(status_code=200)
                yield {
                    "notificaciones": mock_notif,
                    "alertas_ml": mock_ml,
                    "alertas_caidas": mock_caidas,
                }


@pytest.fixture
def mock_datetime():
    """
    Parchea datetime.now() para controlar el tiempo en tests de cooldown.
    Retorna un MagicMock que puede configurarse con .return_value.
    """
    fixed_time = datetime.datetime(2026, 7, 12, 12, 0, 0)
    with patch("datetime.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_time
        mock_dt.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)
        yield mock_dt


@pytest.fixture
def mock_datetime_peru():
    """
    Parchea datetime.now() específicamente para timezone America/Lima.
    """
    fixed_time = datetime.datetime(2026, 7, 12, 7, 0, 0)  # Hora Peru
    with patch("datetime.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_time
        mock_dt.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)
        yield mock_dt


@pytest.fixture
def mock_telemetria_service():
    """
    Mock de telemetria_service con datos predefinidos.
    Permite configurar el retorno de obtener_ultima_ventana y obtener_ultima_ventana_imu.
    """
    with patch.object(telemetria_service, "obtener_ultima_ventana") as mock_ventana, \
         patch.object(telemetria_service, "obtener_ultima_ventana_imu") as mock_ventana_imu:
        yield {
            "ventana": mock_ventana,
            "ventana_imu": mock_ventana_imu,
        }


@pytest.fixture
def mock_ml_services():
    """
    Mock de ml_services.predecir_ventana.
    Retorna por defecto 'okay' con probabilidades altas.
    """
    with patch.object(ml_services, "predecir_ventana") as mock_predecir:
        mock_predecir.return_value = (
            "okay",
            {"okay": 0.90, "warning": 0.08, "bad": 0.02},
        )
        yield mock_predecir


@pytest.fixture
def mock_ml_fall_service():
    """
    Mock de ml_fall_service.predecir_caida.
    Retorna por defecto no-caída.
    """
    with patch.object(ml_fall_service, "predecir_caida") as mock_caida:
        mock_caida.return_value = (0.10, False)
        yield mock_caida


# ========================================================================
# FIXTURES DE HELPERS PUROS (para testear lógica extraída)
# ========================================================================

@pytest.fixture
def sample_cuidadores_list():
    """Lista de UID de cuidadores para tests de permisos."""
    return ["uid_cuidador_1", "uid_cuidador_2", "uid_cuidador_3"]


@pytest.fixture
def sample_cooldown_dict():
    """
    Diccionario de cooldown con entradas preexistentes para tests.
    Clave: 'pacienteId_categoria' -> datetime
    """
    now = datetime.datetime(2026, 7, 12, 12, 0, 0)
    return {
        "paciente_1_warning": now,
        "paciente_1_bad": now,
        "paciente_2_warning": now - datetime.timedelta(minutes=6),  # >5 min atrás
    }


@pytest.fixture
def sample_notification_payload():
    """Payload base para notificaciones push."""
    return {
        "to": "ExponentPushToken[test123]",
        "sound": "default",
        "title": "",
        "body": "",
    }
