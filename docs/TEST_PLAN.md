# Plan de Testing Completo - HealthWatch-Backend

## 1. Estrategia de Pruebas

### Framework
- **pytest** como framework principal (equivalente Python a Jest)
- **pytest-cov** para medición de cobertura de código
- **pytest-mock** para facilitar el mocking
- **unittest.mock** (stdlib) para patches de bajo nivel

### Filosofía
- Tests **herméticos**: No dependen de servicios externos (Firebase, InfluxDB, MQTT, PyTorch models)
- Tests **deterministas**: Mismos inputs → mismos outputs (seeds fijas en `np.random`)
- Tests **aislados**: Cada test es independiente, no comparte estado con otros

### Qué se testea
- Lógica de negocio pura: cálculos matemáticos, validaciones, transformaciones de datos
- Patrones de comportamiento: cooldown de notificaciones, permisos de acceso
- Construcción de payloads: notificaciones push, respuestas HTTP
- Flujos de integración: autenticación → acceso a datos, pipeline de alertas

### Qué NO se testea
- CRUD puro de Firestore/InfluxDB (wrappers sin lógica)
- Modelos ML reales (se mockean completamente)
- Conexiones de red reales (MQTT, HTTP a Expo API)
- Infraestructura Docker

---

## 2. Estructura de Directorios

```
HealthWatch-Backend/
├── Makefile                              # Scripts de automatización (test, test-unit, etc.)
├── pyproject.toml                        # Config pytest + coverage
├── tests/
│   ├── __init__.py
│   ├── conftest.py                      # Fixtures compartidos, mocks globales
│   ├── test_smoke.py                    # Smoke tests: verificación de infraestructura
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_ml_fall_service.py      # Suite 1: ~24 tests
│   │   ├── test_alertas.py              # Suite 2: ~23 tests
│   │   ├── test_notificaciones.py       # Suite 3: ~13 tests
│   │   └── test_pacientes_seguridad.py  # Suite 4: ~21 tests
│   └── integration/
│       ├── __init__.py
│       ├── test_auth_flujo.py            # Suite 5: ~6 tests
│       └── test_alertas_pipeline.py      # Suite 6: ~6 tests
├── docs/
│   └── TEST_PLAN.md                     # Este archivo
└── ... (código existente)
```

---

## 3. Setup y Ejecución

### Instalación
```bash
# Activar entorno virtual
.\venv\Scripts\activate

# Instalar dependencias (incluye pytest)
pip install -r requirements.txt
```

### Ejecución de Tests
```bash
# Ejecutar todos los tests
pytest

# Solo tests unitarios
pytest tests/unit/

# Solo tests de integración
pytest tests/integration/

# Con cobertura de código
pytest --cov=app --cov-report=term-missing

# Verbose con output detallado
pytest -v -s

# Ejecutar un test específico
pytest tests/unit/test_ml_fall_service.py::test_calcular_orientacion_dispositivo_plano -v
```

### Markers Disponibles
```bash
# Ejecutar solo tests marcados como "unit"
pytest -m unit

# Ejecutar solo tests marcados como "integration"
pytest -m integration

# Ejecutar tests que no son "slow"
pytest -m "not slow"
```

### Scripts de Automatización (Makefile)

El proyecto utiliza un **Makefile** como equivalente a los scripts npm para ejecutar tests. Todos los comandos usan el `python.exe` del virtualenv local.

#### Comandos Principales

| Comando | Descripción | Equivalente npm |
|---------|-------------|-----------------|
| `make test` | Ejecutar todos los tests | `npm test` |
| `make test-unit` | Ejecutar solo tests unitarios | `npm run test:unit` |
| `make test-integration` | Ejecutar solo tests de integración | `npm run test:integration` |
| `make test-coverage` | Ejecutar tests con cobertura de código | `npm run test:coverage` |
| `make test-verbose` | Ejecutar tests con output verbose | `npm run test:verbose` |
| `make test-rerun` | Re-ejecutar solo tests fallidos | — |
| `make test-marker` | Ejecutar tests por marker (ej: `make test-marker MARKER=unit`) | — |

#### Comandos de Cobertura

| Comando | Descripción |
|---------|-------------|
| `make coverage-html` | Generar reporte HTML de cobertura en `htmlcov/index.html` |
| `make coverage-check` | Verificar que cobertura >= 70% (falla si no alcanza el mínimo) |

#### Utilidades

| Comando | Descripción |
|---------|-------------|
| `make test-install` | Instalar dependencias de testing |
| `make test-clean` | Limpiar caché de pytest (`__pycache__`, `.pytest_cache`) |
| `make help` | Mostrar ayuda con todos los comandos disponibles |

#### Detalle de Implementación del Makefile

```makefile
# Variables
PYTHON = venv/Scripts/python.exe
PYTEST = $(PYTHON) -m pytest
PYTEST_OPTS = -v --tb=short

# Targets principales
test:           ## Ejecutar todos los tests
test-unit:      ## Solo tests unitarios (tests/unit/)
test-integration: ## Solo tests de integración (tests/integration/)
test-coverage:  ## Tests con cobertura (--cov=app --cov-report=term-missing --cov-report=html)
test-verbose:   ## Tests con output verbose (-v -s)
test-rerun:     ## Re-ejecutar solo tests fallidos (--lf)
test-marker:    ## Tests por marker (-m $(MARKER))

# Targets de cobertura
coverage-html:  ## Generar reporte HTML
coverage-check: ## Verificar cobertura >= 70% (--cov-fail-under=70)
```

---

## 4. Arquitectura de Mocks (conftest.py)

### Concepto

El archivo `conftest.py` (493 líneas) actúa como **interceptor de servicios externos**. Se ejecuta ANTES de la colección de tests y parchea los módulos pesados para que la aplicación pueda importarse sin conexión a servicios reales.

### Parches Globales (nivel de módulo)

Estos patches se aplican **antes** de cualquier importación del proyecto, garantizando que los módulos nunca intenten conectarse a servicios reales:

| # | Parche | Módulo Parcheado | Propósito |
|---|--------|-------------------|-----------|
| 1 | `firebase_admin.credentials.Certificate` | Firebase Admin SDK | Evita que Firebase intente cargar credenciales reales |
| 2 | `firebase_admin.initialize_app` | Firebase Admin SDK | Evita la inicialización real de Firebase |
| 3 | `firebase_admin._apps` | Firebase Admin SDK | Simula que no hay apps inicializadas |
| 4 | `firebase_admin.firestore.client` | Firestore | Evita conexión a base de datos Firestore |
| 5 | `influxdb_client_3.InfluxDBClient3` | InfluxDB 3 | Evita conexión a base de datos de series temporales |
| 6 | `joblib.load` | Modelos ML (scalers, configs) | Retorna objetos fake según el path del archivo |
| 7 | `torch.load` | Modelos ML (LSTM) | Retorna state_dict fake con shapes correctas |

### Variables de Entorno de Testing

`conftest.py` configura variables de entorno mínimas antes de cualquier import:

```python
os.environ.setdefault("INFLUXDB3_HOST_URL", "http://localhost:8181")
os.environ.setdefault("INFLUXDB3_DATABASE_NAME", "test_db")
os.environ.setdefault("INFLUXDB3_AUTH_TOKEN", "test_token_12345")
os.environ.setdefault("FIREBASE_WEB_API_KEY", "fake_api_key_for_testing")
```

### Mock Inteligente de joblib.load

El mock de `joblib.load` usa un `side_effect` que retorna objetos diferentes según el path solicitado:

| Path contiene | Retorna |
|---------------|---------|
| `config_lstm` | Dict con config del modelo salud (input_size=3, window_size=30) |
| `label_mapping_lstm` | Dict `{"okay": 0, "warning": 1, "bad": 2}` |
| `scaler_lstm` | MagicMock con `.transform()` que retorna el input sin modificar |
| `config_fall` | Dict con config del modelo caídas (input_size=9, window_size=20) |
| `scaler_fall` | MagicMock con `.transform()` que retorna el input sin modificar |
| Cualquier otro | MagicMock genérico |

### Mock Inteligente de torch.load

El mock de `torch.load` retorna un `state_dict` con shapes correctas:

- **Modelo salud (HealthLSTM)**: `input_size=3, hidden_size=64, num_layers=2, num_classes=3`
- **Modelo caídas (FallLSTM)**: `input_size=9, hidden_size=64, num_layers=2, output=1`

### Fixtures de Mocks de Servicios

| Fixture | Servicio Mockeado | Propósito |
|---------|-------------------|-----------|
| `mock_db` | Firestore `db` | Simula collection/document/get para pacientes y collection_group para medicamentos |
| `mock_requests_post` | `requests.post` | Captura payloads enviados a Expo (notificaciones, alertas_ml, alertas_caidas) |
| `mock_datetime` | `datetime.now()` | Fija tiempo a 2026-07-12 12:00:00 para tests de cooldown |
| `mock_datetime_peru` | `datetime.now()` | Fija tiempo a 2026-07-12 07:00:00 (timezone Peru) |
| `mock_telemetria_service` | `obtener_ultima_ventana` / `obtener_ultima_ventana_imu` | Simula datos de InfluxDB |
| `mock_ml_services` | `predecir_ventana` | Retorna "okay" con probabilidades altas |
| `mock_ml_fall_service` | `predecir_caida` | Retorna (0.10, False) - no caída |

### Flujo de Ejecución

```
1. conftest.py se carga
   ↓
2. Variables de entorno se configuran
   ↓
3. Parches globales se aplican (Firebase, InfluxDB, joblib, torch)
   ↓
4. Módulos del proyecto se importan (seguros de importar)
   ↓
5. Tests se recopilan y ejecutan
   ↓
6. Cada test recibe fixtures de datos/mocks vía dependency injection
```

---

## 5. Fixtures Disponibles (conftest.py)

### Datos Sintéticos
| Fixture | Descripción |
|---------|-------------|
| `fake_patient_data` | Paciente con 2 cuidadores asignados |
| `fake_patient_no_caregivers` | Paciente con lista vacía de cuidadores |
| `fake_patient_missing_caregivers` | Paciente sin campo cuidadores_asignados |
| `fake_medication_data` | Medicamento con 3 horas programadas |
| `fake_medication_single_hour` | Medicamento con 1 hora programada |
| `fake_telemetry_window` | 30 lecturas biométricas normales (seed=42) |
| `fake_telemetry_window_anomalous` | 30 lecturas con valores anómalos (seed=99) |
| `fake_imu_window` | 20 lecturas IMU de caminata normal (seed=42) |
| `fake_imu_window_fall` | 20 lecturas IMU con caída simulada |
| `fake_caregiver_data` | Cuidador con token Expo válido |
| `fake_caregiver_no_token` | Cuidador sin token |
| `sample_cuidadores_list` | Lista de 3 UIDs |
| `sample_cooldown_dict` | Diccionario de cooldown con entradas variadas |
| `sample_notification_payload` | Payload base para notificaciones push |

### Mocks de Servicios
| Fixture | Descripción |
|---------|-------------|
| `mock_db` | Mock completo de Firestore |
| `mock_requests_post` | Mock de requests.post para notificaciones |
| `mock_datetime` | Mock de datetime.now() para controlar tiempo |
| `mock_datetime_peru` | Mock de datetime.now() para timezone Peru |
| `mock_telemetria_service` | Mock de obtener_ultima_ventana/obtener_ultima_ventana_imu |
| `mock_ml_services` | Mock de predecir_ventana (retorna "okay") |
| `mock_ml_fall_service` | Mock de predecir_caida (retorna no-caída) |

---

## 6. Documentación de Pruebas

### 6.1 Resumen de Conjuntos de Prueba

El plan de testing está organizado en **7 conjuntos de pruebas** (1 smoke + 4 unit + 2 integration), con un total de **~106 casos de prueba**. Cada conjunto sigue la notación formal: **Objetivo → Precondición → Acción → Oráculo**.

| Conjunto | Tipo | Archivo | Tests | Módulo(s) Cubierto(s) | Criterio de Aceptación |
|----------|------|---------|-------|------------------------|------------------------|
| **Smoke** | Infraestructura | `test_smoke.py` | 13 | conftest.py, fixtures | Todos los fixtures y mocks funcionan |
| **Suite 1** | Unit | `test_ml_fall_service.py` | 24 | `ml_fall_service.py` | Cálculos IMU + predicción caídas |
| **Suite 2** | Unit | `test_alertas.py` | 23 | `alertas_ml.py`, `alertas_caidas.py` | Cooldown + payloads de alerta |
| **Suite 3** | Unit | `test_notificaciones.py` | 13 | `notificaciones_service.py` | Payload push + matching horas |
| **Suite 4** | Unit | `test_pacientes_seguridad.py` | 21 | `pacientes.py`, `security.py`, `telemetria_service.py` | Permisos + token + telemetría |
| **Suite 5** | Integration | `test_auth_flujo.py` | 6 | `pacientes.py` + `security.py` | Flujo auth end-to-end |
| **Suite 6** | Integration | `test_alertas_pipeline.py` | 6 | `alertas_ml.py` + `alertas_caidas.py` | Pipeline ML → notificación |
| | | | **~106** | | **Cobertura >= 70%** |

### 6.2 Matriz de Cubrimiento Funcional

| Funcionalidad del Sistema | Smoke | Suite 1 | Suite 2 | Suite 3 | Suite 4 | Suite 5 | Suite 6 |
|---------------------------|-------|---------|---------|---------|---------|---------|---------|
| Cálculo orientación IMU (pitch/roll/yaw) | | X | | | | | |
| Transformación ventanas IMU → features | | X | | | | | |
| Predicción caídas LSTM binaria | | X | | | | | |
| Cooldown de alertas ML (5 min) | | | X | | | | X |
| Cooldown de alertas de caídas (5 min) | | | X | | | | X |
| Payload notificación ML (bad/warning) | | | X | | | | X |
| Payload notificación de caídas | | | X | | | | X |
| Payload notificación push (medicamentos) | | | | X | | | |
| Matching de horas para medicamentos | | | | X | | | |
| Timezone America/Lima | | | | X | | | |
| Permisos de acceso a pacientes | | | | | X | X | |
| Verificación de token JWT/Firebase | | | | | X | X | |
| Extracción de datos de telemetría | | | | | X | X | |
| Flujo completo autenticación → datos | | | | | | X | |
| Pipeline datos → ML → notificación | | | | | | | X |
| Datos insuficientes no procesa | | | | | | | X |
| Fixtures y mocks funcionan | X | | | | | | |

### 6.3 Criterios de Aceptación General

1. **Todos los tests deben pasar** sin excepciones al ejecutar `make test`
2. **Cobertura de código >= 70%** verificada con `make coverage-check`
3. **Tests herméticos**: Ningún test depende de servicios externos reales
4. **Tests deterministas**: Mismos inputs producen mismos outputs (seeds fijas)
5. **Tests aislados**: No hay dependencia entre tests (estado limpio por test)

---

### FASE 0: Smoke Tests - test_smoke.py

#### Objetivo
Verificar que la infraestructura de testing funciona correctamente: fixtures de datos, mocks de servicios y el conftest.py se cargan sin errores.

#### Tests

| # | Test | Objetivo | Precondición | Acción | Oráculo |
|---|------|----------|--------------|--------|---------|
| 1 | `test_conftest_loads` | Verificar que fixture de paciente carga | conftest.py cargado | Usar `fake_patient_data` | id == "paciente_test_001", 2 cuidadores |
| 2 | `test_fake_telemetry_window` | Verificar ventana de telemetría | fixture disponible | Usar `fake_telemetry_window` | 30 registros con HR, SpO2, Temp |
| 3 | `test_fake_imu_window` | Verificar ventana IMU | fixture disponible | Usar `fake_imu_window` | 20 registros con 6 campos IMU |
| 4 | `test_mock_db` | Verificar mock de Firestore | mock_db disponible | Consultar mock | doc.exists=True, tiene cuidadores |
| 5 | `test_mock_datetime` | Verificar mock de tiempo | mock_datetime disponible | Obtener now() | año=2026, mes=7, día=12 |
| 6 | `test_mock_ml_services` | Verificar mock de ML salud | mock_ml_services disponible | Llamar mock | retorna "okay" con probs |
| 7 | `test_mock_ml_fall_service` | Verificar mock de ML caídas | mock_ml_fall_service disponible | Llamar mock | prob=0.10, es_caida=False |
| 8 | `test_mock_requests_post` | Verificar mock HTTP | mock_requests_post disponible | Verificar no llamado | notificaciones y alertas sin llamadas |
| 9 | `test_fake_patient_no_caregivers` | Verificar paciente sin cuidadores | fixture disponible | Usar fixture | cuidadores_asignados == [] |
| 10 | `test_fake_patient_missing_caregivers` | Verificar paciente sin campo | fixture disponible | Usar fixture | sin key cuidadores_asignados |
| 11 | `test_fake_medication_data` | Verificar medicamento | fixture disponible | Usar fixture | 3 horas, incluye "08:00" |
| 12 | `test_fake_imu_window_fall` | Verificar ventana con caída | fixture disponible | Usar fixture | 20 registros, penúltimo ax=28.5 |
| 13 | `test_sample_cooldown_dict` | Verificar dict cooldown | fixture disponible | Usar fixture | 3 entradas, tiene "paciente_1_warning" |

---

### FASE 1: Unit Suite 1 - ml_fall_service.py

#### Objetivo
Verificar la lógica de cálculo de orientación IMU, transformación de ventanas y predicción de caídas.

#### Tests

| # | Test | Objetivo | Precondición | Acción | Oráculo |
|---|------|----------|--------------|--------|---------|
| 1 | `test_dispositivo_plano` | Verificar cálculo con dispositivo plano | ax=0, ay=0, az=9.81 | Llamar `calcular_orientacion(0, 0, 9.81, 0, 0, 0)` | pitch≈0, roll≈0, yaw=0 |
| 2 | `test_dispositivo_vertical` | Verificar cálculo con dispositivo vertical | ax=9.81, ay=0, az=0 | Llamar `calcular_orientacion(9.81, 0, 0, 0, 0, 0)` | pitch≈-π/2 |
| 3 | `test_inclinado_45_grados` | Verificar inclinación de 45° | ángulo conocido | Llamar con valores que produzcan 45° | pitch en rango [-0.85, -0.75] |
| 4 | `test_valores_negativos` | Verificar manejo de signos negativos | aceleraciones negativas | Llamar con ax=-5, ay=-3 | pitch₁ ≈ -pitch₂ |
| 5 | `test_gravedad_cero_no_crash` | Verificar que no hay división por cero | az=0 | Llamar `calcular_orientacion(0, 0, 0, 0, 0, 0)` | No lanza excepción, retorna floats |
| 6 | `test_symmetry_pitch` | Verificar simetría del cálculo | (ax,ay,az) vs (-ax,-ay,az) | Comparar pitches | pitch₁ ≈ -pitch₂ |
| 7 | `test_yaw_siempre_cero` | Verificar que yaw es siempre 0 | cualquier input | Llamar con 4 combinaciones | yaw == 0.0 siempre |
| 8 | `test_roll_inclinacion_lateral` | Verificar roll con inclinación lateral | solo ay != 0 | Llamar con ay=5 | roll != 0 |
| 9 | `test_giroscopio_no_afecta_orientacion` | Verificar que gx/gy/gz no afectan pitch/roll | mismo accel, diferente gyro | Comparar resultados | pitch₁ == pitch₂, roll₁ == roll₂ |
| 10 | `test_shape_correcto` | Verificar forma del output | ventana de 20 valores | Llamar `transformar_ventana_imu(...)` | shape == (1, 20, 9) |
| 11 | `test_orden_features` | Verificar orden de features | valores conocidos | Inspeccionar features | [pitch,roll,yaw,gx,gy,gz,az,ax,ay] |
| 12 | `test_todos_los_tiempos_procesados` | Verificar que todos los timesteps se procesan | ventana de 20 | Verificar shapes | shape[1]==20, shape[2]==9 |
| 13 | `test_valores_no_nan` | Verificar ausencia de NaN | datos normales | Verificar resultado | No hay NaN |
| 14 | `test_valores_finitos` | Verificar valores finitos | datos normales | Verificar resultado | Todos finitos (no inf) |
| 15 | `test_window_wrong_length_raises` | Verificar validación de input | lista de 15 en vez de 20 | Llamar `predecir_caida(...)` con 15 valores | raise ValueError |
| 16 | `test_window_empty_raises` | Verificar lista vacía | lista de 0 | Llamar `predecir_caida(...)` | raise ValueError |
| 17 | `test_probabilidad_en_rango` | Verificar rango de probabilidad | modelo mockeado | Llamar `predecir_caida(...)` | 0 <= prob <= 1 |
| 18 | `test_threshold_verdadero` | Verificar prob > 0.5 → True | prob=0.6 | Comparar es_caida | es_caida = True |
| 19 | `test_threshold_falso` | Verificar prob < 0.5 → False | prob=0.4 | Comparar es_caida | es_caida = False |
| 20 | `test_threshold_limite_exacto` | Verificar caso límite exacto | prob exactamente 0.5 | Llamar con prob=0.5 | es_caida = False (> 0.5) |
| 21 | `test_probabilidad_cero` | Verificar prob=0.0 | prob=0.0 | Llamar y verificar | prob=0.0, es_caida=False |
| 22 | `test_probabilidad_uno` | Verificar prob=1.0 | prob=1.0 | Llamar y verificar | prob=1.0, es_caida=True |
| 23 | `test_valores_extremos_imu_no_crash` | Verificar robustez con valores extremos | aceleraciones altísimas | Llamar con ax=100, ay=200 | No crash, resultado válido |
| 24 | `test_model_recibe_tensor_correcto` | Verificar que modelo recibe tensor correcto | input válido | Llamar predecir_caida | Modelo recibe tensor (1,20,9) |

---

### FASE 2: Unit Suite 2 - alertas_ml.py + alertas_caidas.py

#### Objetivo
Verificar la lógica de cooldown de notificaciones y construcción de payloads para alertas de salud y caídas.

#### Tests

| # | Test | Objetivo | Precondición | Acción | Oráculo |
|---|------|----------|--------------|--------|---------|
| 1 | `test_payload_bad_title` | Título correcto para "bad" | clasificacion="bad" | Construir payload | title contiene "crítica" |
| 2 | `test_payload_warning_title` | Título correcto para "warning" | clasificacion="warning" | Construir payload | title contiene "Precaución" |
| 3 | `test_payload_okay_no_notifica` | "okay" no genera notificación | clasificacion="okay" | Verificar retorno | returns sin HTTP call |
| 4 | `test_payload_body_contiene_nombre` | Body incluye nombre del paciente | nombre="Carlos Pérez" | Construir payload | body contiene "Carlos Pérez" |
| 5 | `test_payload_to_es_token` | Campo "to" es el token enviado | token="ExponentPushToken[xyz]" | Construir payload | to == token |
| 6 | `test_payload_estructura_completa` | Payload tiene las 4 keys de Expo | — | Construir payload | keys "to","sound","title","body" presentes |
| 7 | `test_payload_usa_post_a_expo` | Se envía POST a URL de Expo | — | Verificar URL | URL contiene "exp.host" |
| 8 | `test_clasificacion_desconocida_no_notifica` | Clasificación inválida no notifica | clasificacion="desconocida" | Verificar | No se llama requests.post |
| 9 | `test_primera_alerta_fires` | Primera alerta siempre se envía | clave nueva en dict | Ejecutar revisar_todos_pacientes | enviar_notificacion se llama |
| 10 | `test_cooldown_dentro_5min_bloqueada` | Bloqueo dentro de cooldown | misma clave, <300s | Verificar dict | clave presente, delta <= 300s |
| 11 | `test_cooldown_fuera_5min_fires` | Re-envío después de cooldown | misma clave, >300s | Verificar dict | delta > 300s |
| 12 | `test_diferente_categoria_independiente` | Categorías son independientes | paciente X con "warning" | Verificar "bad" no tiene entrada | "pac_1_bad" not in dict |
| 13 | `test_diferente_paciente_independiente` | Pacientes son independientes | paciente X e Y | Verificar Y no tiene entrada | "pac_2_bad" not in dict |
| 14 | `test_payload_titulo_caida` | Título contiene "Caída" | — | Construir payload | title contiene "caída" |
| 15 | `test_payload_probabilidad_formato_85` | Formato de probabilidad | prob=0.85 | Construir body | body contiene "85.0%" |
| 16 | `test_payload_probabilidad_formato_0` | Formato con prob=0 | prob=0.0 | Construir body | body contiene "0.0%" |
| 17 | `test_payload_probabilidad_formato_100` | Formato con prob=1 | prob=1.0 | Construir body | body contiene "100.0%" |
| 18 | `test_payload_contiene_nombre` | Body contiene nombre del paciente | nombre="Carlos Pérez" | Construir body | body contiene "Carlos Pérez" |
| 19 | `test_payload_to_es_token` | Campo "to" es el token enviado | token="tok_xyz" | Construir payload | to == "tok_xyz" |
| 20 | `test_primera_alerta_caida_fires` | Primera alerta de caída se envía | paciente nuevo | Verificar dict | "pac_1" not in dict |
| 21 | `test_cooldown_caidas_dentro_5min` | Bloqueo dentro de cooldown | misma paciente, <300s | Verificar dict | delta <= 300s |
| 22 | `test_cooldown_caidas_fuera_5min` | Re-envío después de cooldown | misma paciente, >300s | Verificar dict | delta > 300s |
| 23 | `test_diferente_paciente_independiente` | Pacientes son independientes | X e Y | Verificar Y | "pac_2" not in dict |

---

### FASE 3: Unit Suite 3 - notificaciones_service.py

#### Objetivo
Verificar la construcción de payloads de notificación push y la lógica de matching de horas para medicamentos.

#### Tests

| # | Test | Objetivo | Precondición | Acción | Oráculo |
|---|------|----------|--------------|--------|---------|
| 1 | `test_payload_estructura_correcta` | Estructura del payload | token + medicamento | Construir payload | keys "to","sound","title","body" presentes |
| 2 | `test_payload_titulo_estatico` | Título siempre igual | cualquier med | Construir payload | title == "Recordatorio de Medicamento" |
| 3 | `test_payload_body_contiene_medicamento` | Body incluye nombre | med="Losartán" | Construir payload | body contiene "Losartán" |
| 4 | `test_payload_body_especifico` | Body tiene formato exacto | med="Ibuprofeno" | Construir payload | body == "Es hora de administrar: Ibuprofeno" |
| 5 | `test_payload_to_es_token` | Campo "to" es token | token="ExponentPushToken[abc]" | Construir payload | to == token |
| 6 | `test_payload_sound_default` | Campo "sound" es "default" | — | Construir payload | sound == "default" |
| 7 | `test_headers_json` | Headers correctos | — | Verificar headers | Content-Type == "application/json" |
| 8 | `test_usa_post_a_expo` | Se envía POST a URL de Expo | — | Verificar URL | URL contiene "exp.host" |
| 9 | `test_medicamento_especial_caracteres` | Caracteres especiales OK | med="Paracetamol 500mg (jarabe)" | Construir payload | body contiene el nombre completo |
| 10 | `test_envia_notificacion_a_cuidadores` | Envía a todos los cuidadores | 2 cuidadores con token | Ejecutar revisar_medicamentos_y_notificar | enviar_notificacion_push llamado 2 veces |
| 11 | `test_no_envia_si_cuidador_no_token` | No envía si sin token | cuidador sin expo_token | Ejecutar revisión | enviar_notificacion_push NO llamado |
| 12 | `test_no_envia_si_paciente_no_existe` | No envía si paciente no existe | paciente_doc.exists=False | Ejecutar revisión | enviar_notificacion_push NO llamado |
| 13 | `test_usa_hora_peru` | Usa timezone America/Lima | — | Ejecutar revisión | datetime.now llamado con ZoneInfo("America/Lima") |

---

### FASE 4: Unit Suite 4 - pacientes.py + security.py

#### Objetivo
Verificar la lógica de permisos de acceso, validación de datos y extracción de campos de telemetría.

#### Tests

| # | Test | Objetivo | Precondición | Acción | Oráculo |
|---|------|----------|--------------|--------|---------|
| 1 | `test_uid_in_list_acceso_permitido` | Acceso permitido | uid en cuidadores_asignados | Verificar permiso | acceso permitido (no excepción) |
| 2 | `test_uid_not_in_list_acceso_denegado` | Acceso denegado | uid NO en lista | Verificar permiso | HTTPException 403 |
| 3 | `test_paciente_none_404` | Paciente no existe | paciente = None | Verificar permiso | HTTPException 404 |
| 4 | `test_lista_vacia_cuidadores_403` | Lista vacía | cuidadores_asignados=[] | Verificar permiso | HTTPException 403 |
| 5 | `test_campo_faltante_cuidadores_403` | Key faltante | sin key cuidadores_asignados | Verificar permiso | HTTPException 403 (default []) |
| 6 | `test_multiples_cuidadores` | Múltiples cuidadores | 3 UIDs en lista | Verificar uid en posición 2 | acceso permitido |
| 7 | `test_cuidadores_tipo_array` | Cuidadores es iterable | lista con 1 uid | Verificar con `in` | funciona correctamente |
| 8 | `test_extract_hr_from_window` | Extracción de HR | ventana con heart_rate | Extraer campo | lista de 30 floats |
| 9 | `test_extract_spo2_from_window` | Extracción de SpO2 | ventana con spo2 | Extraer campo | lista de 30 ints/floats |
| 10 | `test_extract_temp_from_window` | Extracción de Temp | ventana con temp | Extraer campo | lista de 30 floats |
| 11 | `test_extract_imu_6_campos` | Extracción de 6 campos IMU | ventana IMU completa | Extraer 6 campos | 6 listas de 20 elementos |
| 12 | `test_ventana_orden_cronologico` | Orden cronológico | ventana normal | Verificar sort | times == sorted(times) |
| 13 | `test_ventana_imu_orden_cronologico` | Orden cronológico IMU | ventana IMU | Verificar sort | times == sorted(times) |
| 14 | `test_reverse_funciona` | reverse() funciona | lista de 3 | Invertir | orden invertido |
| 15 | `test_extract_hr_rango_realista` | HR en rango realista | ventana normal | Verificar rango | todos 60 <= hr <= 100 |
| 16 | `test_token_valido_retorna_decoded` | Token válido | token mockeado válido | Llamar verificar_token | retorna decoded dict |
| 17 | `test_token_valido_verifica_con_clock_skew` | Verifica con clock_skew=10 | token válido | Llamar verificar_token | auth.verify_id_token con clock_skew_seconds=10 |
| 18 | `test_token_invalido_lanza_401` | Token inválido | Exception en verify | Llamar verificar_token | HTTPException 401 |
| 19 | `test_token_expirado_lanza_401` | Token expirado | FirebaseError("expired") | Llamar verificar_token | HTTPException 401 |
| 20 | `test_token_401_contiene_www_auth_header` | Header WWW-Authenticate | Exception en verify | Llamar verificar_token | "WWW-Authenticate" in headers |
| 21 | `test_token_401_detalle_contiene_error` | Detail contiene error | Exception con mensaje | Llamar verificar_token | mensaje en exc_info.value.detail |

---

### FASE 5: Integration Suite 1 - test_auth_flujo.py

#### Objetivo
Verificar el flujo completo de autenticación desde el token hasta el acceso a datos del paciente.

#### Tests

| # | Test | Objetivo | Precondición | Acción | Oráculo |
|---|------|----------|--------------|--------|---------|
| 1 | `test_flujo_completo_acceso_paciente` | Flujo happy path | token válido + uid en cuidadores | GET /api/pacientes/{id} | 200 + datos paciente |
| 2 | `test_flujo_token_invalido_rechazado` | Rechazo por token | token inválido | GET /api/pacientes/{id} | 401 antes de llegar a datos |
| 3 | `test_flujo_uid_no_autorizado` | Rechazo por permiso | token válido pero uid no asignado | GET /api/pacientes/{id} | 403 |
| 4 | `test_flujo_paciente_no_existe` | Paciente inexistente | token válido + paciente_id inexistente | GET /api/pacientes/{id} | 404 |
| 5 | `test_flujo_telemetria_acceso` | Acceso a telemetría | token válido + paciente existe | GET /api/pacientes/{id}/telemetria | 200 + telemetría |
| 6 | `test_flujo_sin_header_auth` | Sin header auth | Sin header Authorization | GET /api/pacientes/{id} | 401 (HTTPBearer) |

---

### FASE 6: Integration Suite 2 - test_alertas_pipeline.py

#### Objetivo
Verificar el pipeline completo de alertas: datos de entrada → clasificación ML → decisión de notificación.

#### Tests

| # | Test | Objetivo | Precondición | Acción | Oráculo |
|---|------|----------|--------------|--------|---------|
| 1 | `test_paciente_normal_no_notifica` | No alerta para paciente normal | ventana normal + modelo "okay" | Ejecutar pipeline | NO se envía notificación |
| 2 | `test_paciente_alerta_notifica` | Alerta para paciente en riesgo | ventana anómala + modelo "bad" | Ejecutar pipeline | SÍ se envía notificación |
| 3 | `test_datos_insuficientes_no_procesa` | Datos insuficientes | <30 lecturas | Ejecutar pipeline | NO se procesa el paciente |
| 4 | `test_warning_tambien_notifica` | Warning también notifica | modelo "warning" | Ejecutar pipeline | SÍ se envía notificación |
| 5 | `test_caidas_detectada_notifica` | Alerta de caída detectada | ventana IMU caída + modelo True | Ejecutar pipeline | SÍ se envía notificación |
| 6 | `test_caidas_no_detectada_no_notifica` | Sin alerta sin caída | ventana IMU normal + modelo False | Ejecutar pipeline | NO se envía notificación |

---

## 7. Tabla de Trazabilidad

| Test | Módulo Código | Función/Línea | Funcionalidad |
|------|---------------|---------------|---------------|
| test_conftest_loads | conftest.py | fixtures | Verificación de infraestructura |
| test_fake_* | conftest.py | fixtures | Datos sintéticos |
| test_mock_* | conftest.py | fixtures | Mocks de servicios |
| test_dispositivo_plano | ml_fall_service.py | calcular_orientacion (L39-56) | Cálculo orientación IMU - plano |
| test_dispositivo_vertical | ml_fall_service.py | calcular_orientacion (L39-56) | Cálculo orientación IMU - vertical |
| test_inclinado_45_grados | ml_fall_service.py | calcular_orientacion (L39-56) | Cálculo orientación IMU - 45° |
| test_valores_negativos | ml_fall_service.py | calcular_orientacion (L39-56) | Cálculo orientación IMU - negativos |
| test_gravedad_cero_* | ml_fall_service.py | calcular_orientacion (L39-56) | Cálculo orientación IMU - gravedad cero |
| test_symmetry_pitch | ml_fall_service.py | calcular_orientacion (L39-56) | Cálculo orientación IMU - simetría |
| test_yaw_siempre_cero | ml_fall_service.py | calcular_orientacion (L39-56) | Cálculo orientación IMU - yaw |
| test_roll_inclinacion_* | ml_fall_service.py | calcular_orientacion (L39-56) | Cálculo orientación IMU - roll |
| test_giroscopio_no_afecta_* | ml_fall_service.py | calcular_orientacion (L39-56) | Cálculo orientación IMU - giroscopio |
| test_shape_correcto | ml_fall_service.py | transformar_ventana_imu (L58-81) | Transformación de features |
| test_orden_features | ml_fall_service.py | transformar_ventana_imu (L58-81) | Orden de features |
| test_todos_los_tiempos_* | ml_fall_service.py | transformar_ventana_imu (L58-81) | Procesamiento de timesteps |
| test_valores_no_nan | ml_fall_service.py | transformar_ventana_imu (L58-81) | Validación de NaN |
| test_valores_finitos | ml_fall_service.py | transformar_ventana_imu (L58-81) | Validación de infinitos |
| test_window_wrong_length_* | ml_fall_service.py | predecir_caida (L83-95) | Validación de input |
| test_window_empty_raises | ml_fall_service.py | predecir_caida (L83-95) | Validación de input vacío |
| test_probabilidad_en_rango | ml_fall_service.py | predecir_caida (L83-95) | Rango de probabilidad |
| test_threshold_verdadero | ml_fall_service.py | predecir_caida (L83-95) | Threshold > 0.5 |
| test_threshold_falso | ml_fall_service.py | predecir_caida (L83-95) | Threshold < 0.5 |
| test_threshold_limite_exacto | ml_fall_service.py | predecir_caida (L83-95) | Threshold == 0.5 |
| test_probabilidad_cero | ml_fall_service.py | predecir_caida (L83-95) | Probabilidad 0.0 |
| test_probabilidad_uno | ml_fall_service.py | predecir_caida (L83-95) | Probabilidad 1.0 |
| test_valores_extremos_imu_* | ml_fall_service.py | predecir_caida (L83-95) | Robustez valores extremos |
| test_model_recibe_tensor_* | ml_fall_service.py | predecir_caida (L83-95) | Input del modelo |
| test_payload_bad_title | alertas_ml.py | enviar_notificacion (L11-38) | Payload notificación ML |
| test_payload_warning_title | alertas_ml.py | enviar_notificacion (L11-38) | Payload notificación ML |
| test_payload_okay_no_notifica | alertas_ml.py | enviar_notificacion (L11-38) | Okay no notifica |
| test_payload_body_contiene_* | alertas_ml.py | enviar_notificacion (L11-38) | Body contiene nombre |
| test_payload_to_es_token | alertas_ml.py | enviar_notificacion (L11-38) | Token destino |
| test_payload_estructura_* | alertas_ml.py | enviar_notificacion (L11-38) | Estructura Expo |
| test_payload_usa_post_a_expo | alertas_ml.py | enviar_notificacion (L11-38) | URL de Expo |
| test_clasificacion_desconocida_* | alertas_ml.py | enviar_notificacion (L11-38) | Clasificación inválida |
| test_primera_alerta_fires | alertas_ml.py | revisar_todos_pacientes (L63-66) | Cooldown de alertas ML |
| test_cooldown_dentro_5min_* | alertas_ml.py | revisar_todos_pacientes (L63-66) | Bloqueo cooldown ML |
| test_cooldown_fuera_5min_* | alertas_ml.py | revisar_todos_pacientes (L63-66) | Re-envío cooldown ML |
| test_diferente_categoria_* | alertas_ml.py | revisar_todos_pacientes (L63-66) | Categorías independientes |
| test_diferente_paciente_* | alertas_ml.py | revisar_todos_pacientes (L63-66) | Pacientes independientes |
| test_payload_titulo_caida | alertas_caidas.py | enviar_notificacion_caida (L11-32) | Payload caídas |
| test_payload_probabilidad_* | alertas_caidas.py | enviar_notificacion_caida (L11-32) | Formato probabilidad |
| test_payload_contiene_nombre | alertas_caidas.py | enviar_notificacion_caida (L11-32) | Body nombre |
| test_payload_to_es_token | alertas_caidas.py | enviar_notificacion_caida (L11-32) | Token destino |
| test_primera_alerta_caida_* | alertas_caidas.py | revisar_caidas_todos_pacientes (L62-64) | Cooldown caídas |
| test_cooldown_caidas_* | alertas_caidas.py | revisar_caidas_todos_pacientes (L62-64) | Bloqueo cooldown caídas |
| test_push_payload_* | notificaciones_service.py | enviar_notificacion_push (L50-70) | Payload notificación push |
| test_headers_json | notificaciones_service.py | enviar_notificacion_push (L50-70) | Headers JSON |
| test_usa_post_a_expo | notificaciones_service.py | enviar_notificacion_push (L50-70) | URL de Expo |
| test_medicamento_especial_* | notificaciones_service.py | enviar_notificacion_push (L50-70) | Caracteres especiales |
| test_envia_notificacion_a_* | notificaciones_service.py | revisar_medicamentos_y_notificar (L14-19) | Envío a cuidadores |
| test_no_envia_si_cuidador_* | notificaciones_service.py | revisar_medicamentos_y_notificar (L14-19) | Sin token |
| test_no_envia_si_paciente_* | notificaciones_service.py | revisar_medicamentos_y_notificar (L14-19) | Paciente inexistente |
| test_usa_hora_peru | notificaciones_service.py | revisar_medicamentos_y_notificar (L14-19) | Timezone Peru |
| test_permission_check_* | pacientes.py | obtener_perfil_paciente (L25-44) | Verificación de permisos |
| test_extract_* | telemetria_service.py | obtener_estado_actual / obtener_estado_caida | Extracción de datos |
| test_reverse_funciona | telemetria_service.py | obtener_historial_paciente | Orden cronológico |
| test_security_token_* | security.py | verificar_token (L11-26) | Verificación de token |
| test_flujo_completo_* | pacientes.py + security.py | endpoint GET /api/pacientes/{id} | Flujo completo auth |
| test_flujo_token_invalido_* | security.py | verificar_token | Token inválido |
| test_flujo_uid_no_autorizado | pacientes.py | obtener_perfil_paciente | Permiso denegado |
| test_flujo_paciente_no_existe | pacientes_service.py | obtener_paciente_por_id | Paciente no encontrado |
| test_flujo_telemetria_* | telemetria_service.py | obtener_historial_paciente | Acceso telemetría |
| test_flujo_sin_header_auth | security.py | HTTPBearer middleware | Sin auth header |
| test_paciente_normal_* | alertas_ml.py | revisar_todos_pacientes | Pipeline ML normal |
| test_paciente_alerta_* | alertas_ml.py | revisar_todos_pacientes + enviar_notificacion | Pipeline ML alerta |
| test_datos_insuficientes_* | alertas_ml.py | revisar_todos_pacientes | Datos insuficientes |
| test_warning_tambien_* | alertas_ml.py | revisar_todos_pacientes | Warning notifica |
| test_caidas_detectada_* | alertas_caidas.py | revisar_caidas_todos_pacientes | Pipeline caídas |
| test_caidas_no_detectada_* | alertas_caidas.py | revisar_caidas_todos_pacientes | Sin caída |

---

## 8. Cobertura Esperada y Gaps

### Cobertura por Suite
| Categoría | Tests | Archivos Cubiertos |
|-----------|-------|-------------------|
| Smoke Tests | 13 | conftest.py (fixtures) |
| Unit Suite 1 (ML orientación/caídas) | 24 | ml_fall_service.py |
| Unit Suite 2 (Alertas ML + Caídas) | 23 | alertas_ml.py, alertas_caidas.py |
| Unit Suite 3 (Notificaciones) | 13 | notificaciones_service.py |
| Unit Suite 4 (Pacientes/Seguridad) | 21 | pacientes.py, security.py, telemetria_service.py |
| **Total Unit** | **94** | |
| Integration Suite 1 (Auth) | 6 | pacientes.py + security.py (flujo completo) |
| Integration Suite 2 (Pipeline) | 6 | alertas_ml.py + alertas_caidas.py (pipeline) |
| **Total Integration** | **12** | |
| **TOTAL GENERAL** | **~106** | **Target: >=70% cobertura** |

### Gaps Conocidos (no se testea)
- CRUD puro de Firestore (servicios sin lógica: `usuarios_service.py`, `pacientes_service.py`, `medicamentos_service.py`, `contactos_service.py`, `actividad_fisica_service.py`)
- Conexiones MQTT/InfluxDB reales
- Modelos ML reales (se mockean completamente)
- Infraestructura Docker
- Endpoints de autenticación (login-prueba) que dependen de Firebase real
- `routers/auth.py` (login-prueba depende de Identity Toolkit de Firebase)
- `main.py` (setup CORS, lifespan de schedulers)
- `seed_db.py` (script de inicialización)
- Endpoints CRUD directos (POST/PUT/DELETE de medicamentos, contactos, actividad física)

---

## 9. Dependencias de Testing

Agregadas a `requirements.txt`:
```
pytest==9.1.1
pytest-cov==7.1.0
pytest-mock==3.15.1
```

Configuración en `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short --strict-markers"
markers = [
    "unit: Unit tests (no external deps, fully hermetic)",
    "integration: Integration tests (mocked external services)",
    "slow: Tests that take more than 1 second",
]

[tool.coverage.run]
source = ["app"]
omit = [
    "app/models/modulo_a/*",
    "app/models/modulo_b/*",
    "app/__init__*",
    "app/core/__init__*",
    "app/models/__init__*",
    "app/routers/__init__*",
    "app/services/__init__*",
]

[tool.coverage.report]
fail_under = 70
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.",
    "if TYPE_CHECKING:",
]
```
