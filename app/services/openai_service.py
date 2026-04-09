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
        
        REGLAS CRÍTICAS PARA LA EXTRACCIÓN:
        1. Para el "nombre_proyecto", busca la descripción exacta del servicio o fabricación. Este nombre suele estar ubicado directamente **debajo de los subtítulos "TRABAJOS REALIZADOS"**.
        2. NO asignes el nombre de la Unidad Minera o nombres muy grandes (ejemplo: "SOLEDAD", "ESPERANZA") como el nombre del proyecto.
        3. Ignora estados del Excel como "FALTA GUARDAR", no deben ir en el titulo.
        
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

def generar_resumen_ejecutivo_avance(nombre_proyecto, semana, porcentaje, observaciones):
    """Genera un reporte profesional organizado por bloques estructurados usando IA para incrustar en el PDF."""
    try:
        obs_texto = observaciones if observaciones else "Ninguna novedad técnica reportada para este periodo."
        prompt = f"""
        Eres un Ingeniero Residente encargado del control de obra en un proyecto metalmecánico/soldadura.
        La tarea es redactar un "RESUMEN EJECUTIVO" muy formal (muy concentrado en un solo párrafo sólido) para el informe en PDF.
        Resume todas las actividades logradas sin hacer listas, solo fluyendo en prosa profesional y continua.

        Datos del Contexto:
        - Proyecto: {nombre_proyecto}
        - Semana Evaluada: N° {semana}
        - Progreso Total Alcanzado: {porcentaje}%
        - Observaciones dictadas: {obs_texto}
        
        Reglas:
        - Cero saludos (ni hola, ni buenos días).
        - Debe ser un solo párrafo continuo, sin viñetas, sin subtítulos y sin asteriscos.
        - Tono corporativo, en tercera persona, redactado fluidamente para rellenar un cuadro.
        """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error AI resumen: {e}")
        return f"En esta semana {semana}, se alcanzó un avance del {porcentaje}%. Las actividades transcurren sin detención. {obs_texto}"
