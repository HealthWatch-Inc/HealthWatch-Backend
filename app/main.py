from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import medicamentos, usuarios, pacientes, auth, actividad_fisica, contactos, ml, notificaciones
from contextlib import asynccontextmanager
from app.routers import pacientes, auth, medicamentos, usuarios, actividad_fisica
from app.services.alertas_ml import scheduler_ml
from app.services.alertas_caidas import scheduler_caidas
from app.services.notificaciones_service import scheduler
import logging
import warnings

# logs
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
logging.getLogger('apscheduler.scheduler').setLevel(logging.WARNING)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando motor de notificaciones (medicamentos)...")
    scheduler.start()
    print("Iniciando motor de clasificación automática ML (salud)...")
    scheduler_ml.start()
    print("Iniciando motor de detección automática de caídas...")
    scheduler_caidas.start()
    yield
    print("Deteniendo motores...")
    scheduler.shutdown()
    scheduler_ml.shutdown()
    scheduler_caidas.shutdown()

app = FastAPI(
    title="HealthWatch-Backend-API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pacientes.router)
app.include_router(auth.router)
app.include_router(medicamentos.router)
app.include_router(usuarios.router)
app.include_router(actividad_fisica.router)
app.include_router(contactos.router)
app.include_router(ml.router)
app.include_router(notificaciones.router)

# Ruta pública base
@app.get("/")
def leer_raiz():
    return {"mensaje": "API funcionando correctamente."}