import asyncio
import os
import sys
import sqlite3

sys.path.append(os.path.abspath("."))

from app.services.openai_service import analizar_presupuesto_pdf
from app.schemas.project_schema import PresupuestoExtraidoSchema
from app.models import models
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup test DB session
DATABASE_URL = "sqlite:///control_soldadura.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def run_import():
    db = SessionLocal()
    pdf_path = r"d:\vps-program-proyects\control_soldadura\HABILITADO_TECHO_DINO_ALMACEN_NUEVO_DINO_TECHO.pdf"
    
    print("Running parser...")
    datos_extraidos = await analizar_presupuesto_pdf(pdf_path)
    if not datos_extraidos:
        print("Failed to parse.")
        return
        
    datos_validados = PresupuestoExtraidoSchema(**datos_extraidos)
    print(f"Total variables: {len(datos_validados.materiales_y_equipos)}")
    
    # Let's see if we have PETROLEO, GASOLINA, TOPICO in datos_validados
    found_cats = set()
    for mat in datos_validados.materiales_y_equipos:
        found_cats.add(mat.categoria)
    print("Found categories in validated data:", found_cats)

    # Let's save a test project to DB (ID = 999)
    try:
        # Clear if exists
        db.query(models.MaterialEquipo).filter(models.MaterialEquipo.proyecto_id == 999).delete()
        db.query(models.Proyecto).filter(models.Proyecto.id == 999).delete()
        db.commit()
        
        nuevo_proyecto = models.Proyecto(
            id=999,
            nombre_proyecto="TEST IMPORT PROJECT",
            fecha="12/06/2026",
            costo_total=100.0,
            utilidad_porcentaje=10.0,
            otros_porcentaje=5.0
        )
        db.add(nuevo_proyecto)
        db.flush()

        # Group and save materials
        materiales_agrupados = {}
        for mat in datos_validados.materiales_y_equipos:
            desc_key = mat.descripcion.strip() if mat.descripcion else ""
            key = (
                desc_key.upper(),
                (mat.unidad or "").strip().upper(),
                (mat.categoria or "Materiales").strip().upper(),
                mat.dias or 1.0
            )
            if key not in materiales_agrupados:
                materiales_agrupados[key] = {
                    "categoria": mat.categoria or "Materiales",
                    "descripcion": desc_key,
                    "unidad": mat.unidad,
                    "cantidad": 0.0,
                    "precio_unitario": mat.precio_unitario or 0.0,
                    "dias": mat.dias or 1.0,
                    "total": 0.0
                }
            item = materiales_agrupados[key]
            item["cantidad"] += mat.cantidad or 0.0
            item["total"] += mat.total or 0.0

        for key, item in materiales_agrupados.items():
            dias_val = item["dias"] or 1.0
            cant_val = item["cantidad"]
            if cant_val > 0:
                item["precio_unitario"] = item["total"] / (cant_val * dias_val)
            else:
                item["precio_unitario"] = 0.0

            nuevo_mat = models.MaterialEquipo(
                proyecto_id=999,
                categoria=item["categoria"],
                descripcion=item["descripcion"],
                cantidad=item["cantidad"],
                unidad=item["unidad"],
                precio_unitario=item["precio_unitario"],
                dias=item["dias"],
                total=item["total"]
            )
            db.add(nuevo_mat)
        
        db.commit()
        print("Saved successfully to Project 999.")
        
        # Verify categories saved in DB
        conn = sqlite3.connect("control_soldadura.db")
        cursor = conn.cursor()
        cursor.execute("SELECT categoria, COUNT(*), SUM(total) FROM materiales_equipos WHERE proyecto_id=999 GROUP BY categoria")
        for row in cursor.fetchall():
            print("DB saved category:", row)
        conn.close()

    except Exception as e:
        db.rollback()
        print("Error during save:", e)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_import())
