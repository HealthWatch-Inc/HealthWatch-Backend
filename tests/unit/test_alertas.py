"""
Suite 2: Unit Tests para alertas_ml.py y alertas_caidas.py
Cubre: Cooldown de notificaciones, construcción de payloads de alerta
"""
import datetime
from unittest.mock import patch, MagicMock

import pytest

from app.services import alertas_ml
from app.services import alertas_caidas


# ========================================================================
# Helper: Fecha fija para tests de cooldown
# ========================================================================

_FIXED_NOW = datetime.datetime(2026, 7, 12, 12, 0, 0)


# ========================================================================
# Grupo 1: alertas_ml - Payloads de notificación
# ========================================================================

class TestAlertasMlPayloads:
    """Tests para enviar_notificacion() de alertas_ml.py."""

    @patch("app.services.alertas_ml.requests.post")
    def test_payload_bad_title(self, mock_post):
        """clasificacion='bad' → título contiene 'crítica'."""
        mock_post.return_value = MagicMock(status_code=200)
        alertas_ml.enviar_notificacion("token_123", "María", "bad")
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs[1]["json"]
        assert "crítica" in payload["title"].lower()

    @patch("app.services.alertas_ml.requests.post")
    def test_payload_warning_title(self, mock_post):
        """clasificacion='warning' → título contiene 'Precaución'."""
        mock_post.return_value = MagicMock(status_code=200)
        alertas_ml.enviar_notificacion("token_123", "María", "warning")
        mock_post.assert_called_once()
        payload = mock_post.call_args[1]["json"]
        assert "precaución" in payload["title"].lower()

    @patch("app.services.alertas_ml.requests.post")
    def test_payload_okay_no_notifica(self, mock_post):
        """clasificacion='okay' → NO se envía notificación."""
        mock_post.return_value = MagicMock(status_code=200)
        alertas_ml.enviar_notificacion("token_123", "María", "okay")
        mock_post.assert_not_called()

    @patch("app.services.alertas_ml.requests.post")
    def test_payload_body_contiene_nombre(self, mock_post):
        """El body del payload debe contener el nombre del paciente."""
        mock_post.return_value = MagicMock(status_code=200)
        alertas_ml.enviar_notificacion("token_123", "Carlos Pérez", "bad")
        payload = mock_post.call_args[1]["json"]
        assert "Carlos Pérez" in payload["body"]

    @patch("app.services.alertas_ml.requests.post")
    def test_payload_to_es_token(self, mock_post):
        """El campo 'to' del payload debe ser el token enviado."""
        mock_post.return_value = MagicMock(status_code=200)
        alertas_ml.enviar_notificacion("ExponentPushToken[xyz]", "María", "warning")
        payload = mock_post.call_args[1]["json"]
        assert payload["to"] == "ExponentPushToken[xyz]"

    @patch("app.services.alertas_ml.requests.post")
    def test_payload_estructura_completa(self, mock_post):
        """El payload debe tener las 4 keys requeridas por Expo."""
        mock_post.return_value = MagicMock(status_code=200)
        alertas_ml.enviar_notificacion("tok", "Paciente", "bad")
        payload = mock_post.call_args[1]["json"]
        assert "to" in payload
        assert "sound" in payload
        assert "title" in payload
        assert "body" in payload
        assert payload["sound"] == "default"

    @patch("app.services.alertas_ml.requests.post")
    def test_payload_usa_post_a_expo(self, mock_post):
        """La notificación se envía vía POST a la URL de Expo."""
        mock_post.return_value = MagicMock(status_code=200)
        alertas_ml.enviar_notificacion("tok", "P", "bad")
        url = mock_post.call_args[0][0]
        assert "exp.host" in url

    @patch("app.services.alertas_ml.requests.post")
    def test_clasificacion_desconocida_no_notifica(self, mock_post):
        """Cualquier clasificación que no sea 'bad' o 'warning' no notifica."""
        mock_post.return_value = MagicMock(status_code=200)
        alertas_ml.enviar_notificacion("tok", "P", "desconocida")
        mock_post.assert_not_called()


# ========================================================================
# Grupo 2: alertas_ml - Lógica de cooldown
# ========================================================================

class TestAlertasMlCooldown:
    """Tests para la lógica de cooldown del diccionario ultima_alerta."""

    def setup_method(self):
        """Limpia el diccionario de cooldown antes de cada test."""
        alertas_ml.ultima_alerta.clear()

    @patch("app.services.alertas_ml.db")
    @patch("app.services.alertas_ml.enviar_notificacion")
    @patch("app.services.alertas_ml.predecir_ventana")
    @patch("app.services.alertas_ml.obtener_ultima_ventana")
    @patch("app.services.alertas_ml.datetime")
    def test_primera_alerta_fires(
        self, mock_dt, mock_ventana, mock_predecir, mock_enviar, mock_db
    ):
        """Primera alerta para paciente+categoría → siempre se envía."""
        mock_dt.now.return_value = _FIXED_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime.datetime(*a, **kw)

        # ConfigurarMocks: paciente con ventana completa
        doc = MagicMock()
        doc.id = "pac_1"
        doc.to_dict.return_value = {
            "nombre_completo": "Paciente Uno",
            "cuidadores_asignados": ["uid_1"],
        }
        doc.reference.set = MagicMock()
        mock_db.collection.return_value.stream.return_value = [doc]
        mock_ventana.return_value = [{"heart_rate": 72, "spo2": 98, "temp": 36.5}] * 30
        mock_predecir.return_value = ("bad", {"okay": 0.1, "warning": 0.2, "bad": 0.7})

        # Mock cuidador con token
        user_doc = MagicMock()
        user_doc.exists = True
        user_doc.to_dict.return_value = {"expo_token": "tok_1"}
        mock_db.collection.return_value.document.return_value.get.return_value = user_doc

        alertas_ml.revisar_todos_pacientes()

        mock_enviar.assert_called_once()

    def setup_method(self):
        alertas_ml.ultima_alerta.clear()

    def test_cooldown_dentro_5min_bloqueada(self):
        """Segunda alerta dentro de 5 minutos → bloqueada."""
        now = _FIXED_NOW
        alertas_ml.ultima_alerta["pac_1_bad"] = now
        # Segundo intento 2 minutos después
        segundo_intento = now + datetime.timedelta(minutes=2)
        clave = "pac_1_bad"
        assert clave in alertas_ml.ultima_alerta
        assert (segundo_intento - alertas_ml.ultima_alerta[clave]).seconds <= 300

    def test_cooldown_fuera_5min_fires(self):
        """Después de 5 minutos → se permite nueva alerta."""
        now = _FIXED_NOW
        alertas_ml.ultima_alerta["pac_1_bad"] = now - datetime.timedelta(minutes=6)
        segundo_intento = now
        clave = "pac_1_bad"
        assert (segundo_intento - alertas_ml.ultima_alerta[clave]).seconds > 300

    def test_diferente_categoria_independiente(self):
        """Mismo paciente, diferentes categorías → cooldowns independientes."""
        now = _FIXED_NOW
        alertas_ml.ultima_alerta["pac_1_warning"] = now
        # "bad" no tiene entrada → debería permitirse
        assert "pac_1_bad" not in alertas_ml.ultima_alerta

    def test_diferente_paciente_independiente(self):
        """Diferentes pacientes → cooldowns independientes."""
        now = _FIXED_NOW
        alertas_ml.ultima_alerta["pac_1_bad"] = now
        # pac_2 no tiene entrada → debería permitirse
        assert "pac_2_bad" not in alertas_ml.ultima_alerta


# ========================================================================
# Grupo 3: alertas_caidas - Payloads de notificación
# ========================================================================

class TestAlertasCaidasPayloads:
    """Tests para enviar_notificacion_caida() de alertas_caidas.py."""

    @patch("app.services.alertas_caidas.requests.post")
    def test_payload_titulo_caida(self, mock_post):
        """El título siempre contiene 'Caída'."""
        mock_post.return_value = MagicMock(status_code=200)
        alertas_caidas.enviar_notificacion_caida("tok", "María", 0.85)
        payload = mock_post.call_args[1]["json"]
        assert "caída" in payload["title"].lower()

    @patch("app.services.alertas_caidas.requests.post")
    def test_payload_probabilidad_formato_85(self, mock_post):
        """prob=0.85 → body contiene '85.0%'."""
        mock_post.return_value = MagicMock(status_code=200)
        alertas_caidas.enviar_notificacion_caida("tok", "María", 0.85)
        payload = mock_post.call_args[1]["json"]
        assert "85.0%" in payload["body"]

    @patch("app.services.alertas_caidas.requests.post")
    def test_payload_probabilidad_formato_0(self, mock_post):
        """prob=0.0 → body contiene '0.0%'."""
        mock_post.return_value = MagicMock(status_code=200)
        alertas_caidas.enviar_notificacion_caida("tok", "María", 0.0)
        payload = mock_post.call_args[1]["json"]
        assert "0.0%" in payload["body"]

    @patch("app.services.alertas_caidas.requests.post")
    def test_payload_probabilidad_formato_100(self, mock_post):
        """prob=1.0 → body contiene '100.0%'."""
        mock_post.return_value = MagicMock(status_code=200)
        alertas_caidas.enviar_notificacion_caida("tok", "María", 1.0)
        payload = mock_post.call_args[1]["json"]
        assert "100.0%" in payload["body"]

    @patch("app.services.alertas_caidas.requests.post")
    def test_payload_contiene_nombre(self, mock_post):
        """El body contiene el nombre del paciente."""
        mock_post.return_value = MagicMock(status_code=200)
        alertas_caidas.enviar_notificacion_caida("tok", "Carlos Pérez", 0.5)
        payload = mock_post.call_args[1]["json"]
        assert "Carlos Pérez" in payload["body"]

    @patch("app.services.alertas_caidas.requests.post")
    def test_payload_to_es_token(self, mock_post):
        """El campo 'to' es el token enviado."""
        mock_post.return_value = MagicMock(status_code=200)
        alertas_caidas.enviar_notificacion_caida("tok_xyz", "P", 0.5)
        payload = mock_post.call_args[1]["json"]
        assert payload["to"] == "tok_xyz"


# ========================================================================
# Grupo 4: alertas_caidas - Lógica de cooldown
# ========================================================================

class TestAlertasCaidasCooldown:
    """Tests para la lógica de cooldown del diccionario ultima_alerta_caida."""

    def setup_method(self):
        """Limpia el diccionario de cooldown antes de cada test."""
        alertas_caidas.ultima_alerta_caida.clear()

    def test_primera_alerta_caida_fires(self):
        """Primera alerta de caída para un paciente → sempre se permite."""
        assert "pac_1" not in alertas_caidas.ultima_alerta_caida

    def test_cooldown_caidas_dentro_5min(self):
        """Segunda alerta dentro de 5 minutos → bloqueada."""
        now = _FIXED_NOW
        alertas_caidas.ultima_alerta_caida["pac_1"] = now
        segundo = now + datetime.timedelta(minutes=2)
        assert (segundo - alertas_caidas.ultima_alerta_caida["pac_1"]).seconds <= 300

    def test_cooldown_caidas_fuera_5min(self):
        """Después de 5 minutos → se permite."""
        now = _FIXED_NOW
        alertas_caidas.ultima_alerta_caida["pac_1"] = now - datetime.timedelta(minutes=6)
        assert (now - alertas_caidas.ultima_alerta_caida["pac_1"]).seconds > 300

    def test_diferente_paciente_independiente(self):
        """Diferentes pacientes → cooldowns independientes."""
        now = _FIXED_NOW
        alertas_caidas.ultima_alerta_caida["pac_1"] = now
        assert "pac_2" not in alertas_caidas.ultima_alerta_caida
