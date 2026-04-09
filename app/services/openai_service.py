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
        Eres un analista financiero experto en presupuestos metalmecánicos y soldadura.
        Analiza el texto provisto y centraliza la información en un formato JSON estricto.
        No agregues saludos, explicaciones ni formato Markdown (```json). Devuelve SOLO el JSON puro.
        
        REGLAS CRÍTICAS PARA LA EXTRACCIÓN:
        1. Para el "nombre_proyecto", busca debajo de los subtítulos "TRABAJOS REALIZADOS" (Ej: "AGUZADO CHOTANAS").
        2. NO asignes el nombre de la Unidad Minera ("ESPERANZA") ni "FALTA GUARDAR" a los proyectos.
        3. El Presupuesto se divide en COSTOS FIJOS (del 1 al 5) y COSTOS VARIABLES (del 6 al 11).
        4. Agrupa en `mano_de_obra` (que es el contenedor de Costos Fijos) TODO lo correspondiente a: "MANO DE OBRA", "LOCAL", "VIGILANCIA", "ENERGIA", "HERRAMIENTAS Y/O VARIOS OTROS SERVICIOS (FIJO)".
        5. Agrupa en `materiales_y_equipos` (que es el contenedor de Costos Variables) TODO lo correspondiente a: "MATERIALES", "IMPLEMENTOS DE SEGURIDAD", "PETROLEO", "GASOLINA", "TOPICO", "EQUIPOS Y/OTROS SERCICIOS (VARIABLE)".
        6. En cada item, asegúrate de recuperar correctamente la unidad de medida (Ej: Tarea, %, M2), su cantidad (Ej: CANT.TRAB o CANT.), su Precio Unitario (P.U o PRECIO) y los días laborados (DIAS). P.U puede ser cero si así está en texto.
        7. El total de cada fila debe ser CANT * P.U * DIAS.
        8. Etiqueta el campo `categoria` indicando EXACTAMENTE el título de la rúbrica o sección numerada a la que pertenece (Ej: "MANO DE OBRA", "LOCAL", "VIGILANCIA", "ENERGIA", "HERRAMIENTAS", "MATERIALES", "IMPLEMENTOS DE SEGURIDAD", "PETROLEO", "EQUIPOS"). ¡JAMÁS ASIGNES el cargo o nombre de una sub-tarea ("Maestro soldador", "torno") como categoría! Por ejemplo, todos los trabajadores e ingenieros deben tener la categoría "MANO DE OBRA".
        
        Usa esta estructura exacta (DEBES INCLUIR LAS LLAVES `mano_de_obra` y `materiales_y_equipos` para la compatibilidad del sistema, aunque internamente guarden Costos Fijos y Costos Variables respectivamente):
        {
            "proyecto_info": {
                "nombre_proyecto": "",
                "fecha": "",
                "costo_total": 0.0,
                "utilidad_porcentaje": 0.0
            },
            "mano_de_obra": [
                {"categoria": "Local", "descripcion": "Alquiler...", "unidad": "M2", "cantidad_trabajadores": 0, "precio_unitario": 0.0, "dias": 0.0, "total": 0.0}
            ],
            "materiales_y_equipos": [
                {"categoria": "Materiales", "descripcion": "Acero...", "unidad": "Kg", "cantidad": 0, "precio_unitario": 0.0, "dias": 0.0, "total": 0.0}
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
