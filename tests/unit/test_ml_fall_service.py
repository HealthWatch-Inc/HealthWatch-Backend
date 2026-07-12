"""
Suite 1: Unit Tests para ml_fall_service.py
Cubre: calcular_orientacion, transformar_ventana_imu, predecir_caida
"""
import math
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import torch

from app.services import ml_fall_service


# ========================================================================
# Grupo 1: calcular_orientacion - Cálculos puros de orientación IMU
# ========================================================================

class TestCalcularOrientacion:
    """Tests para la función calcular_orientacion (math puro, zero mocking)."""

    def test_dispositivo_plano(self):
        """Dispositivo sobre mesa: gravedad solo en Z → pitch≈0, roll≈0."""
        pitch, roll, yaw = ml_fall_service.calcular_orientacion(
            ax=0.0, ay=0.0, az=9.81, gx=0.0, gy=0.0, gz=0.0
        )
        assert pitch == pytest.approx(0.0, abs=1e-6)
        assert roll == pytest.approx(0.0, abs=1e-6)
        assert yaw == 0.0

    def test_dispositivo_vertical(self):
        """Dispositivo vertical: gravedad en X → pitch ≈ -π/2."""
        pitch, roll, yaw = ml_fall_service.calcular_orientacion(
            ax=9.81, ay=0.0, az=0.0, gx=0.0, gy=0.0, gz=0.0
        )
        # atan2(-1.0, 0.0) = -π/2
        assert pitch == pytest.approx(-math.pi / 2, abs=1e-6)
        assert yaw == 0.0

    def test_inclinado_45_grados(self):
        """Inclinación de ~45° en eje X."""
        # ax=6.94 (≈9.81*sin(45°)/cos(45°)), az=6.94 (≈9.81*cos(45°))
        ax_val = 9.81 * math.sin(math.radians(45))
        az_val = 9.81 * math.cos(math.radians(45))
        pitch, roll, _ = ml_fall_service.calcular_orientacion(
            ax=ax_val, ay=0.0, az=az_val, gx=0.0, gy=0.0, gz=0.0
        )
        # pitch debería ser aproximadamente -45° = -π/4
        assert pitch == pytest.approx(-math.pi / 4, abs=0.05)

    def test_valores_negativos(self):
        """Aceleraciones negativas: verifican que los signos se manejan bien."""
        pitch_pos, roll_pos, _ = ml_fall_service.calcular_orientacion(
            ax=5.0, ay=3.0, az=9.81, gx=0.0, gy=0.0, gz=0.0
        )
        pitch_neg, roll_neg, _ = ml_fall_service.calcular_orientacion(
            ax=-5.0, ay=-3.0, az=9.81, gx=0.0, gy=0.0, gz=0.0
        )
        # pitch: atan2(-ax_g, ...) → signo invertido
        assert pitch_pos == pytest.approx(-pitch_neg, abs=1e-6)
        # roll: atan2(ay_g, az_g) → mismo patrón
        assert roll_pos == pytest.approx(-roll_neg, abs=1e-6)

    def test_gravedad_cero_no_crash(self):
        """az=0 no debería causar división por cero ni excepción."""
        pitch, roll, yaw = ml_fall_service.calcular_orientacion(
            ax=0.0, ay=0.0, az=0.0, gx=0.0, gy=0.0, gz=0.0
        )
        # atan2(0, 0) = 0 en Python
        assert isinstance(pitch, float)
        assert isinstance(roll, float)
        assert yaw == 0.0

    def test_symmetry_pitch(self):
        """Simetría: (ax, ay, az) y (-ax, -ay, az) deberían dar pitch opuesto."""
        p1, _, _ = ml_fall_service.calcular_orientacion(5.0, 3.0, 9.81, 0, 0, 0)
        p2, _, _ = ml_fall_service.calcular_orientacion(-5.0, -3.0, 9.81, 0, 0, 0)
        assert p1 == pytest.approx(-p2, abs=1e-6)

    def test_yaw_siempre_cero(self):
        """Yaw es siempre 0.0 independientemente del input."""
        test_cases = [
            (0, 0, 0, 0, 0, 0),
            (9.81, 0, 0, 1.0, 2.0, 3.0),
            (-5, -5, -5, 10, -10, 0),
            (100, 200, 300, 0.5, 0.5, 0.5),
        ]
        for ax, ay, az, gx, gy, gz in test_cases:
            _, _, yaw = ml_fall_service.calcular_orientacion(ax, ay, az, gx, gy, gz)
            assert yaw == 0.0

    def test_roll_inclinacion_lateral(self):
        """Roll responde a inclinación lateral (eje Y)."""
        # Solo ay != 0 → roll != 0
        _, roll, _ = ml_fall_service.calcular_orientacion(
            ax=0.0, ay=5.0, az=9.81, gx=0.0, gy=0.0, gz=0.0
        )
        assert roll != pytest.approx(0.0, abs=0.1)

    def test_giroscopio_no_afecta_orientacion(self):
        """Los valores de giroscopio NO afectan pitch ni roll (son ignorados)."""
        p1, r1, _ = ml_fall_service.calcular_orientacion(0, 0, 9.81, 0, 0, 0)
        p2, r2, _ = ml_fall_service.calcular_orientacion(0, 0, 9.81, 100, 200, 300)
        assert p1 == pytest.approx(p2)
        assert r1 == pytest.approx(r2)


# ========================================================================
# Grupo 2: transformar_ventana_imu - Transformación de features
# ========================================================================

class TestTransformarVentanaImu:
    """Tests para la función transformar_ventana_imu."""

    def _make_lists(self, n=20):
        """Helper: crea 6 listas de longitud n con valores de prueba."""
        ax = [0.1 * math.sin(i * 0.5) for i in range(n)]
        ay = [0.2 * math.cos(i * 0.3) for i in range(n)]
        az = [9.81] * n
        gx = [0.02 * math.sin(i * 0.2) for i in range(n)]
        gy = [0.01 * math.cos(i * 0.4) for i in range(n)]
        gz = [0.0] * n
        return ax, ay, az, gx, gy, gz

    def test_shape_correcto(self):
        """Output tiene shape (1, window_size, 9)."""
        ax, ay, az, gx, gy, gz = self._make_lists(20)
        result = ml_fall_service.transformar_ventana_imu(ax, ay, az, gx, gy, gz)
        assert result.shape == (1, 20, 9)

    def test_orden_features(self):
        """El orden de features es [pitch, roll, yaw, gx, gy, gz, az, ax, ay]."""
        # Dispositivo plano: pitch≈0, roll≈0, yaw=0, gx=gy=gz=0
        n = 20
        ax = [0.0] * n
        ay = [0.0] * n
        az = [9.81] * n
        gx = [0.0] * n
        gy = [0.0] * n
        gz = [0.0] * n
        result = ml_fall_service.transformar_ventana_imu(ax, ay, az, gx, gy, gz)
        # Para dispositivo plano, los primeros 3 features (pitch,roll,yaw) ≈ 0
        # features[3:6] = gx,gy,gz = 0
        # features[6:9] = az,ax,ay = 9.81, 0, 0
        features = result[0, 0, :]
        assert features[0] == pytest.approx(0.0, abs=1e-3)  # pitch
        assert features[1] == pytest.approx(0.0, abs=1e-3)  # roll
        assert features[2] == pytest.approx(0.0)            # yaw
        assert features[3] == pytest.approx(0.0)            # gx
        assert features[4] == pytest.approx(0.0)            # gy
        assert features[5] == pytest.approx(0.0)            # gz
        # az, ax, ay en posiciones 6,7,8 (raw values escalados)
        assert isinstance(features[6], (float, np.floating))
        assert isinstance(features[7], (float, np.floating))
        assert isinstance(features[8], (float, np.floating))

    def test_todos_los_tiempos_procesados(self):
        """Cada timestep de la ventana produce un vector de 9 features."""
        n = 20
        ax, ay, az, gx, gy, gz = self._make_lists(n)
        result = ml_fall_service.transformar_ventana_imu(ax, ay, az, gx, gy, gz)
        # Hay n vectores de features
        assert result.shape[1] == n
        # Cada vector tiene 9 dimensiones
        assert result.shape[2] == 9

    def test_valores_no_nan(self):
        """Los valores de salida no deben contener NaN."""
        ax, ay, az, gx, gy, gz = self._make_lists(20)
        result = ml_fall_service.transformar_ventana_imu(ax, ay, az, gx, gy, gz)
        assert not np.isnan(result).any()

    def test_valores_finitos(self):
        """Los valores de salida deben ser finitos (no inf)."""
        ax, ay, az, gx, gy, gz = self._make_lists(20)
        result = ml_fall_service.transformar_ventana_imu(ax, ay, az, gx, gy, gz)
        assert np.all(np.isfinite(result))


# ========================================================================
# Grupo 3: predecir_caida - Predicción con validación
# ========================================================================

class TestPredecirCaida:
    """Tests para la función predecir_caida."""

    def _make_valid_lists(self, n=20):
        """Helper: crea listas válidas de longitud n."""
        ax = [0.0] * n
        ay = [0.0] * n
        az = [9.81] * n
        gx = [0.0] * n
        gy = [0.0] * n
        gz = [0.0] * n
        return ax, ay, az, gx, gy, gz

    def test_window_wrong_length_raises(self):
        """Listas de longitud incorrecta deben lanzar ValueError."""
        ax, ay, az, gx, gy, gz = self._make_valid_lists(15)
        with pytest.raises(ValueError, match="Se requieren"):
            ml_fall_service.predecir_caida(ax, ay, az, gx, gy, gz)

    def test_window_empty_raises(self):
        """Lista vacía debe lanzar ValueError."""
        ax, ay, az, gx, gy, gz = self._make_valid_lists(0)
        with pytest.raises(ValueError):
            ml_fall_service.predecir_caida(ax, ay, az, gx, gy, gz)

    @patch.object(ml_fall_service, "model")
    def test_probabilidad_en_rango(self, mock_model):
        """La probabilidad debe estar entre 0 y 1."""
        mock_output = MagicMock()
        mock_output.item.return_value = 0.75
        mock_model.return_value = mock_output

        ax, ay, az, gx, gy, gz = self._make_valid_lists(20)
        prob, _ = ml_fall_service.predecir_caida(ax, ay, az, gx, gy, gz)
        assert 0.0 <= prob <= 1.0

    @patch.object(ml_fall_service, "model")
    def test_threshold_verdadero(self, mock_model):
        """Probabilidad > 0.5 → es_caida = True."""
        mock_output = MagicMock()
        mock_output.item.return_value = 0.6
        mock_model.return_value = mock_output

        ax, ay, az, gx, gy, gz = self._make_valid_lists(20)
        _, es_caida = ml_fall_service.predecir_caida(ax, ay, az, gx, gy, gz)
        assert es_caida is True

    @patch.object(ml_fall_service, "model")
    def test_threshold_falso(self, mock_model):
        """Probabilidad < 0.5 → es_caida = False."""
        mock_output = MagicMock()
        mock_output.item.return_value = 0.4
        mock_model.return_value = mock_output

        ax, ay, az, gx, gy, gz = self._make_valid_lists(20)
        _, es_caida = ml_fall_service.predecir_caida(ax, ay, az, gx, gy, gz)
        assert es_caida is False

    @patch.object(ml_fall_service, "model")
    def test_threshold_limite_exacto(self, mock_model):
        """Probabilidad exactamente 0.5 → es_caida = False (> 0.5, no >=)."""
        mock_output = MagicMock()
        mock_output.item.return_value = 0.5
        mock_model.return_value = mock_output

        ax, ay, az, gx, gy, gz = self._make_valid_lists(20)
        _, es_caida = ml_fall_service.predecir_caida(ax, ay, az, gx, gy, gz)
        assert es_caida is False

    @patch.object(ml_fall_service, "model")
    def test_probabilidad_cero(self, mock_model):
        """Probabilidad 0.0 → es_caida = False."""
        mock_output = MagicMock()
        mock_output.item.return_value = 0.0
        mock_model.return_value = mock_output

        ax, ay, az, gx, gy, gz = self._make_valid_lists(20)
        prob, es_caida = ml_fall_service.predecir_caida(ax, ay, az, gx, gy, gz)
        assert prob == 0.0
        assert es_caida is False

    @patch.object(ml_fall_service, "model")
    def test_probabilidad_uno(self, mock_model):
        """Probabilidad 1.0 → es_caida = True."""
        mock_output = MagicMock()
        mock_output.item.return_value = 1.0
        mock_model.return_value = mock_output

        ax, ay, az, gx, gy, gz = self._make_valid_lists(20)
        prob, es_caida = ml_fall_service.predecir_caida(ax, ay, az, gx, gy, gz)
        assert prob == 1.0
        assert es_caida is True

    @patch.object(ml_fall_service, "model")
    def test_valores_extremos_imu_no_crash(self, mock_model):
        """Valores IMU extremos no deben causar crash."""
        mock_output = MagicMock()
        mock_output.item.return_value = 0.95
        mock_model.return_value = mock_output

        n = 20
        ax = [100.0] * n
        ay = [200.0] * n
        az = [300.0] * n
        gx = [50.0] * n
        gy = [50.0] * n
        gz = [50.0] * n
        prob, es_caida = ml_fall_service.predecir_caida(ax, ay, az, gx, gy, gz)
        assert isinstance(prob, float)
        assert isinstance(es_caida, bool)

    @patch.object(ml_fall_service, "model")
    def test_model_recibe_tensor_correcto(self, mock_model):
        """El modelo recibe un tensor de la forma correcta."""
        mock_output = MagicMock()
        mock_output.item.return_value = 0.3
        mock_model.return_value = mock_output

        ax, ay, az, gx, gy, gz = self._make_valid_lists(20)
        ml_fall_service.predecir_caida(ax, ay, az, gx, gy, gz)

        # Verificar que el modelo fue llamado con un tensor
        mock_model.assert_called_once()
        call_args = mock_model.call_args
        input_tensor = call_args[0][0]
        assert isinstance(input_tensor, torch.Tensor)
        assert input_tensor.shape == (1, 20, 9)
