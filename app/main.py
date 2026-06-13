from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import pacientes, auth
from app.routers import medicamentos, usuarios, pacientes, auth
from contextlib import asynccontextmanager
from app.services.alertas_ml import scheduler_ml
from app.services.notificaciones_service import scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando motor de notificaciones (medicamentos)...")
    scheduler.start()
    print("Iniciando motor de clasificación automática ML...")
    scheduler_ml.start()
    yield
    print("Deteniendo motores...")
    scheduler.shutdown()
    scheduler_ml.shutdown()

app = FastAPI(
    title="HealthWatch-Backend-API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081"], # El puerto de tu frontend
    allow_credentials=True,
    allow_methods=["*"], # Esto permite OPTIONS, GET, POST, etc.
    allow_headers=["*"],
)

app.include_router(pacientes.router)
app.include_router(auth.router)
app.include_router(medicamentos.router)
app.include_router(usuarios.router)

# Ruta pública base
@app.get("/")
def leer_raiz():
    return {"mensaje": "API funcionando correctamente."}