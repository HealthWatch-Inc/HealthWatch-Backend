"""
Suite 6: Integration Tests - Pipeline completo de alertas
Verifica: Datos → Clasificación ML → Decisión de notificación
"""
import datetime
from unittest.mock import patch, MagicMock

import pytest

from app.services import alertas_ml
from app.services import alertas_caidas


# ========================================================================
# Fixtures de integración
# ========================================================================

@pytest.fixture(autouse=True)
def clean_cooldowns():
    """Limpia cooldowns antes y después de cada test."""
    alertas_ml.ultima_alerta.clear()
    alertas_caidas.ultima_alerta_caida.clear()
    yield
    alertas_ml.ultima_alerta.clear()
    alertas_caidas.ultima_alerta_caida.clear()


@pytest.fixture
def fake_patient_doc():
    """Documento de paciente mockeado."""
    doc = MagicMock()
    doc.id = "paciente_pipeline_001"
    doc.to_dict.return_value = {
        "nombre_completo": "Paciente Pipeline",
        "cuidadores_asignados": ["uid_cuidador_1"],
    }
    doc.reference.set = MagicMock()
    return doc


@pytest.fixture
def fake_user_doc():
    """Documento de usuario mockeado con token."""
    doc = MagicMock()
    doc.exists = True
    doc.to_dict.return_value = {"expo_token": "ExponentPushToken[pipeline_test]"}
    return doc


@pytest.fixture
def fake_user_doc_no_token():
    """Documento de usuario mockeado sin token."""
    doc = MagicMock()
    doc.exists = True
    doc.to_dict.return_value = {}
    return doc


# ========================================================================
# Tests: Pipeline de alertas ML (salud)
# ========================================================================

class TestPipelineAlertasML:
    """Tests del pipeline completo: ventana → clasificación → notificación."""

    @patch("app.services.alertas_ml.enviar_notificacion")
    @patch("app.services.alertas_ml.db")
    @patch("app.services.alertas_ml.datetime")
    def test_paciente_normal_no_notifica(
        self, mock_dt, mock_db, mock_enviar, fake_patient_doc, fake_user_doc
    ):
        """Paciente con clasificación 'okay' → NO se envía notificación."""
        mock_dt.now.return_value = datetime.datetime(2026, 7, 12, 12, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime.datetime(*a, **kw)

        mock_db.collection.return_value.stream.return_value = [fake_patient_doc]
        mock_db.collection.return_value.document.return_value.get.return_value = (
            fake_user_doc
        )

        # Mock: ventana con datos normales → clasificación "okay"
        with patch("app.services.alertas_ml.obtener_ultima_ventana") as mock_ventana:
            mock_ventana.return_value = [
                {"heart_rate": 72, "spo2": 98, "temp": 36.5}
            ] * 30
            with patch("app.services.alertas_ml.predecir_ventana") as mock_predecir:
                mock_predecir.return_value = (
                    "okay",
                    {"okay": 0.90, "warning": 0.08, "bad": 0.02},
                )
                alertas_ml.revisar_todos_pacientes()

        mock_enviar.assert_not_called()

    @patch("app.services.alertas_ml.enviar_notificacion")
    @patch("app.services.alertas_ml.db")
    @patch("app.services.alertas_ml.datetime")
    def test_paciente_alerta_notifica(
        self, mock_dt, mock_db, mock_enviar, fake_patient_doc, fake_user_doc
    ):
        """Paciente con clasificación 'bad' → SÍ se envía notificación."""
        mock_dt.now.return_value = datetime.datetime(2026, 7, 12, 12, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime.datetime(*a, **kw)

        mock_db.collection.return_value.stream.return_value = [fake_patient_doc]
        mock_db.collection.return_value.document.return_value.get.return_value = (
            fake_user_doc
        )

        with patch("app.services.alertas_ml.obtener_ultima_ventana") as mock_ventana:
            mock_ventana.return_value = [
                {"heart_rate": 120, "spo2": 90, "temp": 38.5}
            ] * 30
            with patch("app.services.alertas_ml.predecir_ventana") as mock_predecir:
                mock_predecir.return_value = (
                    "bad",
                    {"okay": 0.05, "warning": 0.15, "bad": 0.80},
                )
                alertas_ml.revisar_todos_pacientes()

        mock_enviar.assert_called_once()
        call_args = mock_enviar.call_args
        assert call_args[0][0] == "ExponentPushToken[pipeline_test]"
        assert call_args[0][1] == "Paciente Pipeline"
        assert call_args[0][2] == "bad"

    @patch("app.services.alertas_ml.enviar_notificacion")
    @patch("app.services.alertas_ml.db")
    @patch("app.services.alertas_ml.datetime")
    def test_datos_insuficientes_no_procesa(
        self, mock_dt, mock_db, mock_enviar, fake_patient_doc
    ):
        """Menos de 30 lecturas → no se procesa el paciente."""
        mock_dt.now.return_value = datetime.datetime(2026, 7, 12, 12, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime.datetime(*a, **kw)

        mock_db.collection.return_value.stream.return_value = [fake_patient_doc]

        with patch("app.services.alertas_ml.obtener_ultima_ventana") as mock_ventana:
            mock_ventana.return_value = [{"heart_rate": 72, "spo2": 98, "temp": 36.5}] * 10
            alertas_ml.revisar_todos_pacientes()

        mock_enviar.assert_not_called()

    @patch("app.services.alertas_ml.enviar_notificacion")
    @patch("app.services.alertas_ml.db")
    @patch("app.services.alertas_ml.datetime")
    def test_warning_tambien_notifica(
        self, mock_dt, mock_db, mock_enviar, fake_patient_doc, fake_user_doc
    ):
        """Paciente con clasificación 'warning' → SÍ se envía notificación."""
        mock_dt.now.return_value = datetime.datetime(2026, 7, 12, 12, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime.datetime(*a, **kw)

        mock_db.collection.return_value.stream.return_value = [fake_patient_doc]
        mock_db.collection.return_value.document.return_value.get.return_value = (
            fake_user_doc
        )

        with patch("app.services.alertas_ml.obtener_ultima_ventana") as mock_ventana:
            mock_ventana.return_value = [
                {"heart_rate": 95, "spo2": 94, "temp": 37.5}
            ] * 30
            with patch("app.services.alertas_ml.predecir_ventana") as mock_predecir:
                mock_predecir.return_value = (
                    "warning",
                    {"okay": 0.30, "warning": 0.55, "bad": 0.15},
                )
                alertas_ml.revisar_todos_pacientes()

        mock_enviar.assert_called_once()


# ========================================================================
# Tests: Pipeline de alertas de caídas
# ========================================================================

class TestPipelineAlertasCaidas:
    """Tests del pipeline completo: ventana IMU → predicción → notificación."""

    @patch("app.services.alertas_caidas.enviar_notificacion_caida")
    @patch("app.services.alertas_caidas.db")
    @patch("app.services.alertas_caidas.datetime")
    def test_caidas_detectada_notifica(
        self, mock_dt, mock_db, mock_enviar, fake_patient_doc, fake_user_doc
    ):
        """Caída detectada → SÍ se envía notificación."""
        mock_dt.now.return_value = datetime.datetime(2026, 7, 12, 12, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime.datetime(*a, **kw)

        mock_db.collection.return_value.stream.return_value = [fake_patient_doc]
        mock_db.collection.return_value.document.return_value.get.return_value = (
            fake_user_doc
        )

        with patch("app.services.alertas_caidas.obtener_ultima_ventana_imu") as mock_imu:
            mock_imu.return_value = [
                {"ax": 0.1, "ay": 0.2, "az": 9.81, "gx": 0.01, "gy": 0.01, "gz": 0.0}
            ] * 20
            with patch("app.services.alertas_caidas.predecir_caida") as mock_caida:
                mock_caida.return_value = (0.85, True)
                alertas_caidas.revisar_caidas_todos_pacientes()

        mock_enviar.assert_called_once()
        call_args = mock_enviar.call_args
        assert call_args[0][0] == "ExponentPushToken[pipeline_test]"
        assert call_args[0][1] == "Paciente Pipeline"
        assert call_args[0][2] == 0.85

    @patch("app.services.alertas_caidas.enviar_notificacion_caida")
    @patch("app.services.alertas_caidas.db")
    @patch("app.services.alertas_caidas.datetime")
    def test_caidas_no_detectada_no_notifica(
        self, mock_dt, mock_db, mock_enviar, fake_patient_doc, fake_user_doc
    ):
        """Sin caída → NO se envía notificación."""
        mock_dt.now.return_value = datetime.datetime(2026, 7, 12, 12, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime.datetime(*a, **kw)

        mock_db.collection.return_value.stream.return_value = [fake_patient_doc]
        mock_db.collection.return_value.document.return_value.get.return_value = (
            fake_user_doc
        )

        with patch("app.services.alertas_caidas.obtener_ultima_ventana_imu") as mock_imu:
            mock_imu.return_value = [
                {"ax": 0.1, "ay": 0.2, "az": 9.81, "gx": 0.01, "gy": 0.01, "gz": 0.0}
            ] * 20
            with patch("app.services.alertas_caidas.predecir_caida") as mock_caida:
                mock_caida.return_value = (0.10, False)
                alertas_caidas.revisar_caidas_todos_pacientes()

        mock_enviar.assert_not_called()
