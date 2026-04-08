from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints
from app.models.database import engine
from app.models import models

# Crea todas las tablas en la Base de Datos en el inicio
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Control de Proyectos - Soldadura")

# Configuración extendida de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluimos las rutas definidas en la capa API
app.include_router(endpoints.router)

@app.get("/")
def read_root():
    return {"mensaje": "API de Control de Proyectos operativa"}
