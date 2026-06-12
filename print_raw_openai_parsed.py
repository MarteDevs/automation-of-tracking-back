import asyncio
import os
import sys

sys.path.append(os.path.abspath("."))

from app.services.openai_service import analizar_presupuesto_pdf
from app.schemas.project_schema import PresupuestoExtraidoSchema

async def run_test():
    pdf_path = r"d:\vps-program-proyects\control_soldadura\HABILITADO_TECHO_DINO_ALMACEN_NUEVO_DINO_TECHO.pdf"
    datos_extraidos = await analizar_presupuesto_pdf(pdf_path)
    if not datos_extraidos:
        print("Failed to parse.")
        return
    datos_validados = PresupuestoExtraidoSchema(**datos_extraidos)
    print(f"Total parsed materials: {len(datos_validados.materiales_y_equipos)}")
    for idx, mat in enumerate(datos_validados.materiales_y_equipos):
        print(f"Index {idx}: Desc={mat.descripcion!r} | Cat={mat.categoria!r} | Cant={mat.cantidad} | Total={mat.total}")

if __name__ == "__main__":
    asyncio.run(run_test())
