"""
Suite 4: Unit Tests para pacientes.py (permisos, extracción) y security.py (token)
Cubre: Lógica de permisos, extracción de datos de telemetría, verificación de token
"""
from unittest.mock import patch, MagicMock

import pytest
from fastapi import HTTPException

from app.core import security


# ========================================================================
# Grupo 1: Lógica de permisos de acceso a pacientes
# (Extraída de pacientes.py - patrón repetido en 4 endpoints)
# ========================================================================

class TestLogicaPermisos:
    """
    Tests de la lógica de verificación de permisos.
    Patrón: uid_cuidador in paciente.get("cuidadores_asignados", [])
    """

    def _check_permission(self, uid, paciente):
        """Helper: replica la lógica de permisos de pacientes.py."""
        if paciente is None:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
        if uid not in paciente.get("cuidadores_asignados", []):
            raise HTTPException(status_code=403, detail="Acceso denegado")
        return True

    def test_uid_in_list_acceso_permitido(self, fake_patient_data):
        """UID está en cuidadores_asignados → acceso permitido."""
        result = self._check_permission("uid_cuidador_1", fake_patient_data)
        assert result is True

    def test_uid_not_in_list_acceso_denegado(self, fake_patient_data):
        """UID NO está en cuidadores_asignados → HTTPException 403."""
        with pytest.raises(HTTPException) as exc_info:
            self._check_permission("uid_desconocido", fake_patient_data)
        assert exc_info.value.status_code == 403

    def test_paciente_none_404(self):
        """Paciente es None → HTTPException 404."""
        with pytest.raises(HTTPException) as exc_info:
            self._check_permission("uid_1", None)
        assert exc_info.value.status_code == 404

    def test_lista_vacia_cuidadores_403(self, fake_patient_no_caregivers):
        """Lista vacía de cuidadores → HTTPException 403."""
        with pytest.raises(HTTPException) as exc_info:
            self._check_permission("uid_1", fake_patient_no_caregivers)
        assert exc_info.value.status_code == 403

    def test_campo_faltante_cuidadores_403(self, fake_patient_missing_caregivers):
        """Sin campo cuidadores_asignados → default [] → HTTPException 403."""
        with pytest.raises(HTTPException) as exc_info:
            self._check_permission("uid_1", fake_patient_missing_caregivers)
        assert exc_info.value.status_code == 403

    def test_multiples_cuidadores(self):
        """Múltiples cuidadores: uid en la posición 2 también tiene acceso."""
        paciente = {
            "cuidadores_asignados": ["uid_a", "uid_b", "uid_c"],
        }
        assert self._check_permission("uid_c", paciente) is True

    def test_cuidadores_tipo_array(self):
        """Verificar que cuidadores_asignados es iterable (lista)."""
        paciente = {"cuidadores_asignados": ["uid_1"]}
        assert self._check_permission("uid_1", paciente) is True


# ========================================================================
# Grupo 2: Extracción de campos de telemetría
# ========================================================================

class TestExtraccionTelemetria:
    """Tests de extracción de campos de listas de diccionarios de telemetría."""

    def test_extract_hr_from_window(self, fake_telemetry_window):
        """Extraer heart_rate de la ventana."""
        hr_vals = [p["heart_rate"] for p in fake_telemetry_window]
        assert len(hr_vals) == 30
        assert all(isinstance(v, (int, float)) for v in hr_vals)

    def test_extract_spo2_from_window(self, fake_telemetry_window):
        """Extraer spo2 de la ventana."""
        spo2_vals = [p["spo2"] for p in fake_telemetry_window]
        assert len(spo2_vals) == 30
        assert all(isinstance(v, (int, float)) for v in spo2_vals)

    def test_extract_temp_from_window(self, fake_telemetry_window):
        """Extraer temp de la ventana."""
        temp_vals = [p["temp"] for p in fake_telemetry_window]
        assert len(temp_vals) == 30
        assert all(isinstance(v, (int, float)) for v in temp_vals)

    def test_extract_imu_6_campos(self, fake_imu_window):
        """Extraer los 6 campos IMU: ax,ay,az,gx,gy,gz."""
        ax = [p["ax"] for p in fake_imu_window]
        ay = [p["ay"] for p in fake_imu_window]
        az = [p["az"] for p in fake_imu_window]
        gx = [p["gx"] for p in fake_imu_window]
        gy = [p["gy"] for p in fake_imu_window]
        gz = [p["gz"] for p in fake_imu_window]
        assert len(ax) == 20
        assert len(ay) == 20
        assert len(az) == 20
        assert len(gx) == 20
        assert len(gy) == 20
        assert len(gz) == 20

    def test_ventana_orden_cronologico(self, fake_telemetry_window):
        """La ventana debe estar en orden cronológico ascendente."""
        times = [p["time"] for p in fake_telemetry_window]
        assert times == sorted(times)

    def test_ventana_imu_orden_cronologico(self, fake_imu_window):
        """La ventana IMU debe estar en orden cronológico ascendente."""
        times = [p["time"] for p in fake_imu_window]
        assert times == sorted(times)

    def test_reverse_funciona(self):
        """reverse() invierte la lista correctamente (como en telemetria_service)."""
        datos = [{"time": "3"}, {"time": "2"}, {"time": "1"}]
        datos.reverse()
        assert datos[0]["time"] == "1"
        assert datos[2]["time"] == "3"

    def test_extract_hr_rango_realista(self, fake_telemetry_window):
        """Los valores de HR extraídos están en rango realista."""
        hr_vals = [p["heart_rate"] for p in fake_telemetry_window]
        assert all(60 <= hr <= 100 for hr in hr_vals)


# ========================================================================
# Grupo 3: security.py - Verificación de token
# ========================================================================

class TestVerificarToken:
    """Tests para la función verificar_token de security.py."""

    @patch("app.core.security.auth")
    def test_token_valido_retorna_decoded(self, mock_auth):
        """Token válido → retorna dict decodificado."""
        mock_auth.verify_id_token.return_value = {
            "uid": "uid_123",
            "email": "test@example.com",
        }
        cred = MagicMock()
        cred.credentials = "valid_token_abc"

        result = security.verificar_token(cred)

        assert result["uid"] == "uid_123"
        assert result["email"] == "test@example.com"

    @patch("app.core.security.auth")
    def test_token_valido_verifica_con_clock_skew(self, mock_auth):
        """Token válido → se verifica con clock_skew_seconds=10."""
        mock_auth.verify_id_token.return_value = {"uid": "uid_1"}
        cred = MagicMock()
        cred.credentials = "token"

        security.verificar_token(cred)

        mock_auth.verify_id_token.assert_called_once_with(
            "token", clock_skew_seconds=10
        )

    @patch("app.core.security.auth")
    def test_token_invalido_lanza_401(self, mock_auth):
        """Token inválido → HTTPException 401."""
        mock_auth.verify_id_token.side_effect = Exception("Token expirado")
        cred = MagicMock()
        cred.credentials = "bad_token"

        with pytest.raises(HTTPException) as exc_info:
            security.verificar_token(cred)
        assert exc_info.value.status_code == 401

    @patch("app.core.security.auth")
    def test_token_expirado_lanza_401(self, mock_auth):
        """Token expirado → HTTPException 401."""
        from firebase_admin.exceptions import FirebaseError

        mock_auth.verify_id_token.side_effect = FirebaseError(code="expired", message="Token expirado")
        cred = MagicMock()
        cred.credentials = "expired_token"

        with pytest.raises(HTTPException) as exc_info:
            security.verificar_token(cred)
        assert exc_info.value.status_code == 401

    @patch("app.core.security.auth")
    def test_token_401_contiene_www_auth_header(self, mock_auth):
        """HTTPException 401 debe incluir header WWW-Authenticate."""
        mock_auth.verify_id_token.side_effect = Exception("fail")
        cred = MagicMock()
        cred.credentials = "tok"

        with pytest.raises(HTTPException) as exc_info:
            security.verificar_token(cred)
        assert "WWW-Authenticate" in exc_info.value.headers

    @patch("app.core.security.auth")
    def test_token_401_detalle_contiene_error(self, mock_auth):
        """El detail del 401 debe contener información del error."""
        mock_auth.verify_id_token.side_effect = Exception("Causa del error")
        cred = MagicMock()
        cred.credentials = "tok"

        with pytest.raises(HTTPException) as exc_info:
            security.verificar_token(cred)
        assert "Causa del error" in exc_info.value.detail
