from fastapi import FastAPI
from app.api import endpoints

app = FastAPI(title="API Control de Proyectos - Soldadura")

# Incluimos las rutas definidas en la capa API
app.include_router(endpoints.router)

@app.get("/")
def read_root():
    return {"mensaje": "API de Control de Proyectos operativa"}
