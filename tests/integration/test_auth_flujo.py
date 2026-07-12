"""
Suite 5: Integration Tests - Flujo Autenticación → Acceso a Datos
Verifica el flujo completo: token → verificación → acceso a paciente
"""
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app


# ========================================================================
# Fixtures de integración
# ========================================================================

@pytest.fixture
def client():
    """Cliente de prueba FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_auth_valid():
    """Mock de firebase_admin.auth.verify_id_token para token válido."""
    with patch("app.core.security.auth") as mock_auth:
        mock_auth.verify_id_token.return_value = {
            "uid": "uid_cuidador_1",
            "email": "cuidador@test.com",
            "email_verified": True,
        }
        yield mock_auth


@pytest.fixture
def mock_auth_invalid():
    """Mock de firebase_admin.auth.verify_id_token para token inválido."""
    with patch("app.core.security.auth") as mock_auth:
        mock_auth.verify_id_token.side_effect = Exception("Token inválido")
        yield mock_auth


@pytest.fixture
def mock_paciente_existe():
    """Mock de pacientes_service.obtener_paciente_por_id para paciente existente."""
    with patch("app.services.pacientes_service.obtener_paciente_por_id") as mock:
        mock.return_value = {
            "nombre_completo": "María García",
            "edad": 78,
            "cuidadores_asignados": ["uid_cuidador_1", "uid_cuidador_2"],
        }
        yield mock


@pytest.fixture
def mock_paciente_no_existe():
    """Mock de pacientes_service.obtener_paciente_por_id para paciente inexistente."""
    with patch("app.services.pacientes_service.obtener_paciente_por_id") as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_telemetria():
    """Mock de telemetria_service.obtener_historial_paciente."""
    with patch("app.services.telemetria_service.obtener_historial_paciente") as mock:
        mock.return_value = [
            {"time": "2026-07-12T10:00:00Z", "heart_rate": 72, "spo2": 98, "battery": 85}
        ]
        yield mock


# ========================================================================
# Tests de integración: Flujo completo
# ========================================================================

class TestFlujoAutenticacionAcceso:
    """Tests del flujo: Autenticación → Verificación permisos → Acceso datos."""

    def test_flujo_completo_acceso_paciente(
        self, client, mock_auth_valid, mock_paciente_existe, mock_telemetria
    ):
        """Token válido + uid en cuidadores → 200 + datos paciente."""
        response = client.get(
            "/api/pacientes/paciente_test_001",
            headers={"Authorization": "Bearer valid_token_123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "éxito"
        assert "paciente" in data

    def test_flujo_token_invalido_rechazado(self, client, mock_auth_invalid):
        """Token inválido → 401 antes de llegar a lógica de pacientes."""
        response = client.get(
            "/api/pacientes/paciente_test_001",
            headers={"Authorization": "Bearer bad_token"},
        )
        assert response.status_code == 401

    def test_flujo_uid_no_autorizado(
        self, client, mock_auth_valid, mock_paciente_existe
    ):
        """Token válido pero uid no está en cuidadores_asignados → 403."""
        # mock_auth_valid retorna uid_cuidador_1, pero el mock de paciente
        # solo tiene uid_cuidador_1 y uid_cuidador_2
        # Cambiamos el mock para que el uid NO esté en la lista
        with patch("app.core.security.auth") as mock_auth:
            mock_auth.verify_id_token.return_value = {
                "uid": "uid_no_autorizado",
                "email": "hacker@test.com",
            }
            response = client.get(
                "/api/pacientes/paciente_test_001",
                headers={"Authorization": "Bearer token_hacker"},
            )
        assert response.status_code == 403

    def test_flujo_paciente_no_existe(
        self, client, mock_auth_valid, mock_paciente_no_existe
    ):
        """Token válido + paciente_id inexistente → 404."""
        response = client.get(
            "/api/pacientes/paciente_inexistente",
            headers={"Authorization": "Bearer valid_token_123"},
        )
        assert response.status_code == 404

    def test_flujo_telemetria_acceso(
        self, client, mock_auth_valid, mock_paciente_existe, mock_telemetria
    ):
        """Flujo completo para obtener telemetría → 200."""
        response = client.get(
            "/api/pacientes/paciente_test_001/telemetria",
            headers={"Authorization": "Bearer valid_token_123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "éxito"
        assert "telemetria" in data

    def test_flujo_sin_header_auth(self, client):
        """Sin header Authorization → 401 (FastAPI HTTPBearer)."""
        response = client.get("/api/pacientes/paciente_test_001")
        assert response.status_code == 401
