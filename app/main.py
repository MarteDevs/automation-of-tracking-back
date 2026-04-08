from fastapi import FastAPI
from app.api import endpoints
from app.models.database import engine
from app.models import models

# Crea todas las tablas en la Base de Datos en el inicio
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Control de Proyectos - Soldadura")

# Incluimos las rutas definidas en la capa API
app.include_router(endpoints.router)

@app.get("/")
def read_root():
    return {"mensaje": "API de Control de Proyectos operativa"}
