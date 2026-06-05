from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import pacientes, auth

app = FastAPI(
    title="HealthWatch-Backend-API",
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

# Ruta pública base
@app.get("/")
def leer_raiz():
    return {"mensaje": "API funcionando correctamente."}