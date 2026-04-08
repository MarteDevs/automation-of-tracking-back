from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import shutil
import os
import uuid

from app.services.openai_service import analizar_presupuesto_pdf
from app.models.database import get_db
from app.models import models
from app.schemas import project_schema

router = APIRouter()

@router.post("/api/v1/procesar-presupuesto/", response_model=project_schema.ProyectoResponse)
async def procesar_presupuesto(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")

    # 1. Guardar el archivo temporalmente con un nombre único
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = f"temp/{unique_filename}"
    os.makedirs("temp", exist_ok=True)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 2. Enviar a la capa de Servicio (OpenAI)
        datos_extraidos = analizar_presupuesto_pdf(temp_path)
    finally:
        # 3. Limpiar archivo temporal siempre
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"No se pudo eliminar el archivo temporal: {e}")

    if not datos_extraidos:
        raise HTTPException(status_code=500, detail="Error al procesar con IA. OpenAI puede no haber respondido.")

    # 4. Validar el formato exacto del JSON con Pydantic Schematic
    try:
        datos_validados = project_schema.PresupuestoExtraidoSchema(**datos_extraidos)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"El formato devuelto por la IA es inválido o faltan campos obligatorios: {str(e)}")

    # 5. Guardar los datos extraídos y validados en la Base de Datos Relacional
    try:
        # 5.1 Guardar información cabecera del Proyecto
        nuevo_proyecto = models.Proyecto(
            nombre_proyecto=datos_validados.proyecto_info.nombre_proyecto,
            fecha=datos_validados.proyecto_info.fecha,
            costo_total=datos_validados.proyecto_info.costo_total,
            utilidad_porcentaje=datos_validados.proyecto_info.utilidad_porcentaje
        )
        db.add(nuevo_proyecto)
        db.flush() # Importante: Obtenemos el ID generado del proyecto (nuevo_proyecto.id)

        # 5.2 Guardar registros de Mano de Obra
        for mo in datos_validados.mano_de_obra:
            nueva_mo = models.ManoObra(
                proyecto_id=nuevo_proyecto.id,
                descripcion=mo.descripcion,
                cantidad_trabajadores=mo.cantidad_trabajadores,
                precio_unitario=mo.precio_unitario,
                total=mo.total
            )
            db.add(nueva_mo)

        # 5.3 Guardar registros de Materiales y Equipos
        for mat in datos_validados.materiales_y_equipos:
            nuevo_mat = models.MaterialEquipo(
                proyecto_id=nuevo_proyecto.id,
                descripcion=mat.descripcion,
                cantidad=mat.cantidad,
                unidad=mat.unidad,
                total=mat.total
            )
            db.add(nuevo_mat)

        # Guardar todos los cambios definitivamente en la base de datos
        db.commit()
        db.refresh(nuevo_proyecto)
        
        # El endpoint responderá utilizando el `response_model=ProyectoResponse`
        return nuevo_proyecto
        
    except Exception as e:
        db.rollback() # Prevenir base de datos corrupta
        raise HTTPException(status_code=500, detail=f"Error interno al guardar en Base de Datos: {str(e)}")

from typing import List

@router.get("/api/v1/proyectos/", response_model=List[project_schema.ProyectoResponse])
def listar_proyectos(db: Session = Depends(get_db)):
    proyectos = db.query(models.Proyecto).all()
    return proyectos

@router.get("/api/v1/proyectos/{proyecto_id}", response_model=project_schema.ProyectoResponse)
def obtener_proyecto(proyecto_id: int, db: Session = Depends(get_db)):
    proyecto = db.query(models.Proyecto).filter(models.Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return proyecto

@router.post("/api/v1/proyectos/{proyecto_id}/avances/", response_model=project_schema.AvanceSemanalResponse)
def crear_avance_semanal(proyecto_id: int, avance: project_schema.AvanceSemanalCreate, db: Session = Depends(get_db)):
    proyecto = db.query(models.Proyecto).filter(models.Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    nuevo_avance = models.AvanceSemanal(
        proyecto_id=proyecto_id,
        semana=avance.semana,
        porcentaje_avance=avance.porcentaje_avance,
        observaciones=avance.observaciones,
        rutas_fotografias=avance.rutas_fotografias
    )
    
    try:
        db.add(nuevo_avance)
        db.commit()
        db.refresh(nuevo_avance)
        return nuevo_avance
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al registrar el avance: {str(e)}")

