"""
Suite 3: Unit Tests para notificaciones_service.py
Cubre: Payload de notificación push, extracción de cuidadores, lógica de revisión
"""
import datetime
from unittest.mock import patch, MagicMock, call

import pytest

from app.services import notificaciones_service


# ========================================================================
# Grupo 1: enviar_notificacion_push - Payload de notificación
# ========================================================================

class TestEnviarNotificacionPush:
    """Tests para la función enviar_notificacion_push."""

    @patch("app.services.notificaciones_service.requests.post")
    def test_payload_estructura_correcta(self, mock_post):
        """El payload contiene las 4 keys requeridas por Expo."""
        mock_post.return_value = MagicMock(status_code=200)
        notificaciones_service.enviar_notificacion_push("tok_123", "Losartán")
        mock_post.assert_called_once()
        payload = mock_post.call_args[1]["json"]
        assert "to" in payload
        assert "sound" in payload
        assert "title" in payload
        assert "body" in payload

    @patch("app.services.notificaciones_service.requests.post")
    def test_payload_titulo_estatico(self, mock_post):
        """El título siempre es 'Recordatorio de Medicamento'."""
        mock_post.return_value = MagicMock(status_code=200)
        notificaciones_service.enviar_notificacion_push("tok", "Aspirina")
        payload = mock_post.call_args[1]["json"]
        assert payload["title"] == "Recordatorio de Medicamento"

    @patch("app.services.notificaciones_service.requests.post")
    def test_payload_body_contiene_medicamento(self, mock_post):
        """El body contiene el nombre del medicamento."""
        mock_post.return_value = MagicMock(status_code=200)
        notificaciones_service.enviar_notificacion_push("tok", "Losartán 50mg")
        payload = mock_post.call_args[1]["json"]
        assert "Losartán 50mg" in payload["body"]

    @patch("app.services.notificaciones_service.requests.post")
    def test_payload_body_especifico(self, mock_post):
        """El body tiene el formato exacto 'Es hora de administrar: {med}'."""
        mock_post.return_value = MagicMock(status_code=200)
        notificaciones_service.enviar_notificacion_push("tok", "Ibuprofeno")
        payload = mock_post.call_args[1]["json"]
        assert payload["body"] == "Es hora de administrar: Ibuprofeno"

    @patch("app.services.notificaciones_service.requests.post")
    def test_payload_to_es_token(self, mock_post):
        """El campo 'to' es el token del destinatario."""
        mock_post.return_value = MagicMock(status_code=200)
        notificaciones_service.enviar_notificacion_push("ExponentPushToken[abc]", "Med")
        payload = mock_post.call_args[1]["json"]
        assert payload["to"] == "ExponentPushToken[abc]"

    @patch("app.services.notificaciones_service.requests.post")
    def test_payload_sound_default(self, mock_post):
        """El campo 'sound' es 'default'."""
        mock_post.return_value = MagicMock(status_code=200)
        notificaciones_service.enviar_notificacion_push("tok", "Med")
        payload = mock_post.call_args[1]["json"]
        assert payload["sound"] == "default"

    @patch("app.services.notificaciones_service.requests.post")
    def test_headers_json(self, mock_post):
        """Los headers indican contenido JSON."""
        mock_post.return_value = MagicMock(status_code=200)
        notificaciones_service.enviar_notificacion_push("tok", "Med")
        headers = mock_post.call_args[1]["headers"]
        assert headers["Content-Type"] == "application/json"

    @patch("app.services.notificaciones_service.requests.post")
    def test_usa_post_a_expo(self, mock_post):
        """Se envía POST a la URL de Expo."""
        mock_post.return_value = MagicMock(status_code=200)
        notificaciones_service.enviar_notificacion_push("tok", "Med")
        url = mock_post.call_args[0][0]
        assert "exp.host" in url

    @patch("app.services.notificaciones_service.requests.post")
    def test_medicamento_especial_caracteres(self, mock_post):
        """Medicamento con caracteres especiales se envía correctamente."""
        mock_post.return_value = MagicMock(status_code=200)
        notificaciones_service.enviar_notificacion_push("tok", "Paracetamol 500mg (jarabe)")
        payload = mock_post.call_args[1]["json"]
        assert "Paracetamol 500mg (jarabe)" in payload["body"]


# ========================================================================
# Grupo 2: revisar_medicamentos_y_notificar - Lógica de revisión
# ========================================================================

class TestRevisarMedicamentos:
    """Tests para la función revisar_medicamentos_y_notificar."""

    @patch("app.services.notificaciones_service.enviar_notificacion_push")
    @patch("app.services.notificaciones_service.db")
    @patch("app.services.notificaciones_service.datetime")
    def test_envia_notificacion_a_cuidadores(
        self, mock_dt, mock_db, mock_enviar
    ):
        """Envía notificación a todos los cuidadores del paciente."""
        # Fijar hora a 08:00
        mock_dt.now.return_value = datetime.datetime(2026, 7, 12, 8, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime.datetime(*a, **kw)

        # Mock medicamento encontrado
        med_doc = MagicMock()
        med_doc.to_dict.return_value = {"nombre": "Losartán", "horas": ["08:00"]}
        med_doc.reference.parent.parent.get.return_value.exists = True
        med_doc.reference.parent.parent.get.return_value.to_dict.return_value = {
            "cuidadores_asignados": ["uid_1", "uid_2"]
        }
        mock_db.collection_group.return_value.where.return_value.stream.return_value = [
            med_doc
        ]

        # Mock usuarios
        user_doc = MagicMock()
        user_doc.exists = True
        user_doc.to_dict.return_value = {"expo_token": "tok_1"}
        mock_db.collection.return_value.document.return_value.get.return_value = (
            user_doc
        )

        notificaciones_service.revisar_medicamentos_y_notificar()

        # Debió enviar 2 notificaciones (1 por cada cuidador)
        assert mock_enviar.call_count == 2

    @patch("app.services.notificaciones_service.enviar_notificacion_push")
    @patch("app.services.notificaciones_service.db")
    @patch("app.services.notificaciones_service.datetime")
    def test_no_envia_si_cuidador_no_token(
        self, mock_dt, mock_db, mock_enviar
    ):
        """No envía si el cuidador no tiene token."""
        mock_dt.now.return_value = datetime.datetime(2026, 7, 12, 8, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime.datetime(*a, **kw)

        med_doc = MagicMock()
        med_doc.to_dict.return_value = {"nombre": "Aspirina", "horas": ["08:00"]}
        med_doc.reference.parent.parent.get.return_value.exists = True
        med_doc.reference.parent.parent.get.return_value.to_dict.return_value = {
            "cuidadores_asignados": ["uid_1"]
        }
        mock_db.collection_group.return_value.where.return_value.stream.return_value = [
            med_doc
        ]

        # Cuidador sin token
        user_doc = MagicMock()
        user_doc.exists = True
        user_doc.to_dict.return_value = {}
        mock_db.collection.return_value.document.return_value.get.return_value = (
            user_doc
        )

        notificaciones_service.revisar_medicamentos_y_notificar()

        mock_enviar.assert_not_called()

    @patch("app.services.notificaciones_service.enviar_notificacion_push")
    @patch("app.services.notificaciones_service.db")
    @patch("app.services.notificaciones_service.datetime")
    def test_no_envia_si_paciente_no_existe(
        self, mock_dt, mock_db, mock_enviar
    ):
        """No envía si el paciente referenciado no existe."""
        mock_dt.now.return_value = datetime.datetime(2026, 7, 12, 8, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime.datetime(*a, **kw)

        med_doc = MagicMock()
        med_doc.to_dict.return_value = {"nombre": "Med", "horas": ["08:00"]}
        paciente_doc = MagicMock()
        paciente_doc.exists = False
        med_doc.reference.parent.parent.get.return_value = paciente_doc
        mock_db.collection_group.return_value.where.return_value.stream.return_value = [
            med_doc
        ]

        notificaciones_service.revisar_medicamentos_y_notificar()

        mock_enviar.assert_not_called()

    @patch("app.services.notificaciones_service.enviar_notificacion_push")
    @patch("app.services.notificaciones_service.db")
    @patch("app.services.notificaciones_service.datetime")
    def test_usa_hora_peru(self, mock_dt, mock_db, mock_enviar):
        """Usa timezone America/Lima para obtener la hora."""
        from zoneinfo import ZoneInfo

        # El código llama datetime.datetime.now(zona_peru), no datetime.now()
        mock_dt.datetime.now.return_value = datetime.datetime(2026, 7, 12, 8, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime.datetime(*a, **kw)

        # Mock: no hay medicamentos programados
        mock_db.collection_group.return_value.where.return_value.stream.return_value = []

        notificaciones_service.revisar_medicamentos_y_notificar()

        # Verificar que se llamó datetime.now() con la zona horaria de Peru
        mock_dt.datetime.now.assert_called_with(ZoneInfo("America/Lima"))
