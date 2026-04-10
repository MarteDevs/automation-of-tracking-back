from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import shutil
import os
import uuid

from app.services.openai_service import analizar_presupuesto_pdf, generar_resumen_ejecutivo_avance
from app.services.pdf_service import crear_pdf_avance
from app.models.database import get_db
from app.models import models
from app.schemas import project_schema
from fastapi import Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import FileResponse
from collections import defaultdict
import time
import jwt

# Llave elevada a nivel criptográfico superior (32 bytes) para cumplir con el RFC 7518
SECRET_KEY = "S0Ld4dur4_S3cur3_M4g1cK3y12345678"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

router = APIRouter()

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Credenciales invalidadas o sesión expirada")

@router.post("/api/v1/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    u = form_data.username.upper()
    p = form_data.password
    valid_users = {"JORGE": "POLTAND1", "ADMIN": "ADMIN"}
    
    if u in valid_users and valid_users[u] == p:
        encoded = jwt.encode({"sub": u, "exp": time.time() + 86400}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": encoded, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Usuario o Contraseña incorrectas")

# Anti-Spam: Memoria Volátil para proteger la billetera de OpenAI (Rate Limiting rudimentario)
ip_ratios = defaultdict(list)

def check_rate_limit(request: Request):
    ip = request.client.host
    now = time.time()
    # Limpiamos el historial viejo (retenemos registros de los últimos 60 segundos)
    ip_ratios[ip] = [t for t in ip_ratios[ip] if now - t < 60]
    
    # Límite Max: 4 PDFs por minuto por persona.
    if len(ip_ratios[ip]) >= 4:
        raise HTTPException(status_code=429, detail="Demasiadas solicitudes en muy poco tiempo. El firewall Anti-Spam entró en acción. Espere 1 minuto...")
    
    ip_ratios[ip].append(now)

@router.put("/api/v1/proyectos/{proyecto_id}/configuracion", response_model=project_schema.ProyectoResponse, dependencies=[Depends(get_current_user)])
def actualizar_configuracion_proyecto(proyecto_id: int, config: project_schema.ProyectoUpdate, db: Session = Depends(get_db)):
    proyecto = db.query(models.Proyecto).filter(models.Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    proyecto.semanas_estimadas = config.semanas_estimadas
    proyecto.tipo_duracion = config.tipo_duracion
    proyecto.fecha = config.fecha
    db.commit()
    db.refresh(proyecto)
    return proyecto

@router.post("/api/v1/procesar-presupuesto/", response_model=project_schema.ProyectoResponse, dependencies=[Depends(check_rate_limit), Depends(get_current_user)])
async def procesar_presupuesto(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")

    # 1. Guardar el archivo temporalmente con un nombre único
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = f"temp/{unique_filename}"
    os.makedirs("temp", exist_ok=True)
    
    # 0. Verificar tamaño del archivo (Max 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="El archivo PDF excede el límite de 10MB.")
    await file.seek(0) # Reset para poder copiar el archivo despues

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
            utilidad_porcentaje=datos_validados.proyecto_info.utilidad_porcentaje,
            otros_porcentaje=datos_validados.proyecto_info.otros_porcentaje
        )
        db.add(nuevo_proyecto)
        db.flush() # Importante: Obtenemos el ID generado del proyecto (nuevo_proyecto.id)

        # 5.2 Guardar registros de Mano de Obra (Costos Fijos)
        for mo in datos_validados.mano_de_obra:
            nueva_mo = models.ManoObra(
                proyecto_id=nuevo_proyecto.id,
                categoria=mo.categoria,
                descripcion=mo.descripcion,
                unidad=mo.unidad,
                cantidad_trabajadores=mo.cantidad_trabajadores,
                precio_unitario=mo.precio_unitario,
                dias=mo.dias,
                total=mo.total
            )
            db.add(nueva_mo)

        # 5.3 Guardar registros de Materiales y Equipos (Costos Variables)
        for mat in datos_validados.materiales_y_equipos:
            nuevo_mat = models.MaterialEquipo(
                proyecto_id=nuevo_proyecto.id,
                categoria=mat.categoria,
                descripcion=mat.descripcion,
                cantidad=mat.cantidad,
                unidad=mat.unidad,
                precio_unitario=mat.precio_unitario,
                dias=mat.dias,
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

@router.get("/api/v1/proyectos/", response_model=List[project_schema.ProyectoResponse], dependencies=[Depends(get_current_user)])
def listar_proyectos(db: Session = Depends(get_db)):
    proyectos = db.query(models.Proyecto).all()
    return proyectos

@router.get("/api/v1/proyectos/{proyecto_id}", response_model=project_schema.ProyectoResponse, dependencies=[Depends(get_current_user)])
def obtener_proyecto(proyecto_id: int, db: Session = Depends(get_db)):
    proyecto = db.query(models.Proyecto).filter(models.Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return proyecto

@router.post("/api/v1/proyectos/{proyecto_id}/avances/", response_model=project_schema.AvanceSemanalResponse, dependencies=[Depends(get_current_user)])
def crear_avance_semanal(proyecto_id: int, avance: project_schema.AvanceSemanalCreate, db: Session = Depends(get_db)):
    proyecto = db.query(models.Proyecto).filter(models.Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    nuevo_avance = models.AvanceSemanal(
        proyecto_id=proyecto_id,
        semana=avance.semana,
        porcentaje_avance=avance.porcentaje_avance,
        observaciones=avance.observaciones,
        rutas_fotografias=avance.rutas_fotografias,
        tipo_periodo=avance.tipo_periodo,
        fecha_fin=avance.fecha_fin,
        dias_trabajados=avance.dias_trabajados
    )
    
    try:
        db.add(nuevo_avance)
        db.commit()
        db.refresh(nuevo_avance)
        return nuevo_avance
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al registrar el avance: {str(e)}")

@router.get("/api/v1/proyectos/{proyecto_id}/avances/{avance_id}/descargar-pdf", dependencies=[Depends(get_current_user)])
def descargar_reporte_pdf(proyecto_id: int, avance_id: int, db: Session = Depends(get_db)):
    proyecto = db.query(models.Proyecto).filter(models.Proyecto.id == proyecto_id).first()
    avance = db.query(models.AvanceSemanal).filter(models.AvanceSemanal.id == avance_id, models.AvanceSemanal.proyecto_id == proyecto_id).first()
    
    if not proyecto or not avance:
        raise HTTPException(status_code=404, detail="Proyecto o Avance no encontrados")

    # Generamos la IA
    texto_ia = generar_resumen_ejecutivo_avance(
        proyecto.nombre_proyecto, 
        avance.semana, 
        avance.porcentaje_avance, 
        avance.observaciones
    )
    
    # Dibujamos el PDF
    pdf_path = crear_pdf_avance(proyecto, avance, texto_ia)
    
    # Sanitizar el nombre del proyecto para el nombre de archivo
    import re
    nom_limpio = re.sub(r'[^\w\s-]', '', proyecto.nombre_proyecto).strip().replace(" ", "_")
    
    label_periodo = "Semana" if getattr(avance, 'tipo_periodo', 'SEMANA') == 'SEMANA' else "Dia"
    
    return FileResponse(
        path=pdf_path, 
        filename=f"{nom_limpio}_{label_periodo}_{avance.semana}.pdf",
        media_type="application/pdf"
    )

@router.post("/api/v1/upload-imagen/", dependencies=[Depends(get_current_user)])
async def upload_imagen(files: List[UploadFile] = File(...)):
    rutas = []
    
    # Procesar max 4 iteraciones de seguridad
    archivos_procesables = files[:4]
    
    for file in archivos_procesables:
        ext = file.filename.split('.')[-1].lower()
        if ext not in ['jpg', 'jpeg', 'png']:
            continue
            
        filename = f"{uuid.uuid4().hex}.{ext}"
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        save_path = os.path.join(base_dir, "uploads", "evidencias", filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Verificar tamaño individual (Max 10MB)
        MAX_IMG_SIZE = 10 * 1024 * 1024
        file_size = 0
        
        # Obtener tamaño sin leer todo el contenido a memoria si es posible
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_IMG_SIZE:
            print(f"Archivo {file.filename} omitido por exceso de tamaño ({file_size} bytes)")
            continue

        try:
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            rutas.append(f"uploads/evidencias/{filename}")
        except Exception as e:
            print(f"Error parcial ignorado {e}")
            pass
            
    if not rutas:
        raise HTTPException(status_code=400, detail="No se guardó material grafico válido (solo admite JPG/PNG).")
        
    return {"ruta_fotografias": ",".join(rutas)}

@router.delete("/api/v1/proyectos/{proyecto_id}/avances/{avance_id}", dependencies=[Depends(get_current_user)])
def eliminar_avance_semanal(proyecto_id: int, avance_id: int, db: Session = Depends(get_db)):
    avance = db.query(models.AvanceSemanal).filter(
        models.AvanceSemanal.id == avance_id, 
        models.AvanceSemanal.proyecto_id == proyecto_id
    ).first()
    
    if not avance:
        raise HTTPException(status_code=404, detail="El registro de seguimiento solicitado no existe.")

    try:
        db.delete(avance)
        db.commit()
        return {"mensaje": "Seguimiento eliminado correctamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al intentar eliminar el registro: {str(e)}")

@router.delete("/api/v1/proyectos/{proyecto_id}", dependencies=[Depends(get_current_user)])
def eliminar_proyecto(proyecto_id: int, db: Session = Depends(get_db)):
    proyecto = db.query(models.Proyecto).filter(models.Proyecto.id == proyecto_id).first()
    
    if not proyecto:
        raise HTTPException(status_code=404, detail="El proyecto solicitado no existe.")

    try:
        db.delete(proyecto)
        db.commit()
        return {"mensaje": "Proyecto eliminado satisfactoriamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar el proyecto: {str(e)}")


