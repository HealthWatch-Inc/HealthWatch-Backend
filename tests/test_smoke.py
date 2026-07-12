"""Test mínimo para verificar que conftest.py y fixtures funcionan."""
import datetime
import pytest


def test_conftest_loads(fake_patient_data):
    assert fake_patient_data["id"] == "paciente_test_001"
    assert len(fake_patient_data["cuidadores_asignados"]) == 2


def test_fake_telemetry_window(fake_telemetry_window):
    assert len(fake_telemetry_window) == 30
    assert "heart_rate" in fake_telemetry_window[0]
    assert "spo2" in fake_telemetry_window[0]
    assert "temp" in fake_telemetry_window[0]


def test_fake_imu_window(fake_imu_window):
    assert len(fake_imu_window) == 20
    for field in ["ax", "ay", "az", "gx", "gy", "gz"]:
        assert field in fake_imu_window[0]


def test_mock_db(fake_patient_data, mock_db):
    doc = mock_db.collection.return_value.document.return_value.get.return_value
    assert doc.exists is True
    data = doc.to_dict()
    assert "cuidadores_asignados" in data


def test_mock_datetime(mock_datetime):
    now = mock_datetime.now()
    assert now.year == 2026
    assert now.month == 7
    assert now.day == 12


def test_mock_ml_services(mock_ml_services):
    categoria, probs = mock_ml_services([72.0] * 30, [98] * 30, [36.5] * 30)
    assert categoria == "okay"
    assert "okay" in probs


def test_mock_ml_fall_service(mock_ml_fall_service):
    prob, es_caida = mock_ml_fall_service(
        [0.1] * 20, [0.2] * 20, [9.81] * 20,
        [0.0] * 20, [0.0] * 20, [0.0] * 20,
    )
    assert prob == 0.10
    assert es_caida is False


def test_mock_requests_post(mock_requests_post):
    import requests
    mock_requests_post["notificaciones"].assert_not_called()
    mock_requests_post["alertas_ml"].assert_not_called()


def test_fake_patient_no_caregivers(fake_patient_no_caregivers):
    assert fake_patient_no_caregivers["cuidadores_asignados"] == []


def test_fake_patient_missing_caregivers(fake_patient_missing_caregivers):
    assert "cuidadores_asignados" not in fake_patient_missing_caregivers


def test_fake_medication_data(fake_medication_data):
    assert len(fake_medication_data["horas"]) == 3
    assert "08:00" in fake_medication_data["horas"]


def test_fake_imu_window_fall(fake_imu_window_fall):
    assert len(fake_imu_window_fall) == 20
    assert fake_imu_window_fall[-1]["ax"] == 0.05
    assert fake_imu_window_fall[-2]["ax"] == 28.5


def test_sample_cooldown_dict(sample_cooldown_dict):
    assert len(sample_cooldown_dict) == 3
    assert "paciente_1_warning" in sample_cooldown_dict
