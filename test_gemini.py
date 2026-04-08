from app.services.openai_service import analizar_presupuesto_pdf
import json

pdf_path = r"d:\vps-program-proyects\proyecto_control_soldadura\temp\AGUZADO_CHOTANAS_ESPERANZA_CHOTANAS.pdf"
print(f"Llamando al Servicio con el archivo {pdf_path}")

resultado = analizar_presupuesto_pdf(pdf_path)
print("Resultado:")
print(json.dumps(resultado, indent=4, ensure_ascii=False))
