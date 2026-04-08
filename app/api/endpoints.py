from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
from app.services.openai_service import analizar_presupuesto_pdf

router = APIRouter()

@router.post("/api/v1/procesar-presupuesto/")
async def procesar_presupuesto(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")

    import uuid
    # 1. Guardar el archivo temporalmente con un nombre único en la capa temp/
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = f"temp/{unique_filename}"
    os.makedirs("temp", exist_ok=True)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 2. Enviar a la capa de Servicio (OpenAI)
        datos_extraidos = analizar_presupuesto_pdf(temp_path)
    finally:
        # 3. Limpiar archivo temporal siempre, pase lo que pase
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"No se pudo eliminar el archivo temporal: {e}")

    if not datos_extraidos:
        raise HTTPException(status_code=500, detail="Error al procesar con IA")

    # (Futuro: Aquí llamaremos a la capa Models para guardar en base de datos)

    return {"status": "success", "data": datos_extraidos}
