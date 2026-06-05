from fastapi import FastAPI
from app.routers import medicamentos, usuarios, pacientes, auth
from contextlib import asynccontextmanager
from app.services.notificaciones_service import scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando motor de notificaciones...")
    scheduler.start()
    
    yield

    print("Deteniendo motor de notificaciones...")
    scheduler.shutdown()

app = FastAPI(
    title="HealthWatch-Backend-API",
    lifespan=lifespan
)

app.include_router(pacientes.router)
app.include_router(auth.router)
app.include_router(medicamentos.router)
app.include_router(usuarios.router)

# Ruta pública base
@app.get("/")
def leer_raiz():
    return {"mensaje": "API funcionando correctamente."}