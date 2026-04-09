from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.api import endpoints
from app.models.database import engine
from app.models import models

# Crea todas las tablas en la Base de Datos en el inicio
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Control de Proyectos - Soldadura")

load_dotenv()
# Lee los dominios directamente desde el .env y genera Lista nativa.
origenes = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

# Configuración extendida de CORS (Extraccion Segura Env)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluimos las rutas definidas en la capa API
app.include_router(endpoints.router)

@app.get("/")
def read_root():
    return {"mensaje": "API de Control de Proyectos operativa"}
