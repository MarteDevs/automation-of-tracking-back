import os
import json
import pdfplumber
from openai import OpenAI
from dotenv import load_dotenv

# Cargamos las variables de entorno (.env)
load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def analizar_presupuesto_pdf(ruta_archivo_pdf):
    """
    Lee el texto del PDF y solicita a OpenAI una extracción estructurada en JSON.
    """
    try:
        # Extraer texto del PDF
        texto_pdf = ""
        with pdfplumber.open(ruta_archivo_pdf) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    texto_pdf += text + "\n"
        
        instrucciones = """
        Eres un asistente experto en costos de proyectos metalmecánicos y soldadura.
        Analiza el texto provisto y extrae la información en un formato JSON estricto.
        No agregues saludos, explicaciones ni formato Markdown (```json). Devuelve SOLO el JSON puro.
        
        Usa esta estructura exacta:
        {
            "proyecto_info": {
                "nombre_proyecto": "",
                "fecha": "",
                "costo_total": 0.0,
                "utilidad_porcentaje": 0.0
            },
            "mano_de_obra": [
                {"descripcion": "", "cantidad_trabajadores": 0, "precio_unitario": 0.0, "total": 0.0}
            ],
            "materiales_y_equipos": [
                {"descripcion": "", "cantidad": 0, "unidad": "", "total": 0.0}
            ]
        }
        """

        # Usamos gpt-4o-mini ("mini") como indicó el usuario
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": instrucciones},
                {"role": "user", "content": f"Aquí está el contenido del presupuesto en texto: \n\n{texto_pdf}"}
            ],
            response_format={"type": "json_object"}
        )

        texto_limpio = response.choices[0].message.content.strip()
        datos_json = json.loads(texto_limpio)
        
        return datos_json

    except Exception as e:
        print(f"Error al procesar el documento con OpenAI: {e}")
        return None

if __name__ == "__main__":
    ruta_prueba = r"d:\vps-program-proyects\proyecto_control_soldadura\temp\AGUZADO_CHOTANAS_ESPERANZA_CHOTANAS.pdf" 
    resultado = analizar_presupuesto_pdf(ruta_prueba)
    print(json.dumps(resultado, indent=4, ensure_ascii=False))
