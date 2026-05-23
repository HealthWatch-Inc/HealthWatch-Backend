from fastapi import FastAPI
from app.routers import pacientes, auth

app = FastAPI(
    title="HealthWatch-Backend-API",
)

app.include_router(pacientes.router)
app.include_router(auth.router)

# Ruta pública base
@app.get("/")
def leer_raiz():
    return {"mensaje": "API funcionando correctamente."}