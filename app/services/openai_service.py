import os
import json
import pdfplumber
from openai import OpenAI
from dotenv import load_dotenv

# Cargamos las variables de entorno (.env)
load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def limpiar_json_ia(texto: str) -> str:
    """Limpia la respuesta de la IA para garantizar JSON puro parseabe."""
    texto = texto.strip()
    # Eliminar bloques de codigo markdown ```json ... ``` o ``` ... ```
    if texto.startswith("```"):
        lineas = texto.split("\n")
        # Quitar primera y ultima linea del bloque
        texto = "\n".join(lineas[1:-1]).strip()
    # Si aun tiene triple backtick al final
    if texto.endswith("```"):
        texto = texto[:-3].strip()
    return texto

def analizar_presupuesto_pdf(ruta_archivo_pdf):
    """
    Lee el texto del PDF con dos llamadas a la IA para garantizar
    la extracción completa de todas las secciones (1-11).
    """
    try:
        # ── Extraer texto completo del PDF por páginas ──
        paginas = []
        with pdfplumber.open(ruta_archivo_pdf) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    paginas.append(text)

        texto_completo = "\n".join(paginas)

        # ─────────────────────────────────────────────────────────────
        # LLAMADA 1: Proyecto + Costos Fijos (secciones 1-5)
        # ─────────────────────────────────────────────────────────────
        instrucciones_fijos = """
        Eres un analista financiero experto en presupuestos metalmecánicos.
        Extrae ÚNICAMENTE la información del proyecto y los COSTOS FIJOS (secciones 1 al 5).
        No agregues saludos ni formato Markdown. Devuelve SOLO el JSON puro y válido.

        REGLAS:
        1. Para "nombre_proyecto", extrae el texto bajo "TRABAJOS REALIZADOS".
        2. Para "costo_total" usa el valor final etiquetado COSTO TOTAL.
        3. Para "utilidad_porcentaje", busca el valor % de la fila "Utilidad".
        4. Para "otros_porcentaje", busca el valor % de la fila "otros" o "Gastos Generales".
        5. Para "mano_de_obra" (Costos Fijos):
           - Seccion MANO DE OBRA (1): Crea UNA SOLA fila con descripcion="TOTAL MANO DE OBRA", precio_unitario=IGUAL al valor numerico del TOTAL MANO DE OBRA, cantidad_trabajadores=1, dias=1, total=IGUAL ese mismo valor numerico.
           - Seccion LOCAL (2): extrae el item normalmente.
           - Seccion VIGILANCIA (3): extrae el item normalmente.
           - Seccion ENERGIA (4): extrae el item normalmente.
           - Seccion HERRAMIENTAS (5): extrae el item normalmente.
           - Etiqueta categoria con el nombre exacto de la seccion.
        6. Para "materiales_y_equipos" devuelve una lista VACIA: []

        Estructura JSON obligatoria (rellena los 0.0 con los valores reales):
        {
            "proyecto_info": {"nombre_proyecto": "", "fecha": "", "costo_total": 0.0, "utilidad_porcentaje": 0.0, "otros_porcentaje": 0.0},
            "mano_de_obra": [
                {"categoria": "MANO DE OBRA", "descripcion": "TOTAL MANO DE OBRA", "unidad": "Global", "cantidad_trabajadores": 1, "precio_unitario": 0.0, "dias": 1, "total": 0.0}
            ],
            "materiales_y_equipos": []
        }
        """

        resp1 = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": instrucciones_fijos},
                {"role": "user", "content": f"Presupuesto:\n\n{texto_completo}"}
            ],
            response_format={"type": "json_object"},
            max_tokens=4000,
            temperature=0
        )
        raw1 = resp1.choices[0].message.content
        print(f"[DEBUG R1 inicio]: {raw1[:300]}")
        print(f"[DEBUG R1 final ]: {raw1[-200:]}")
        datos_fijos = json.loads(limpiar_json_ia(raw1))

        # ─────────────────────────────────────────────────────────────
        # Extraer secciones del texto para focus en cada llamada
        # ─────────────────────────────────────────────────────────────
        import re

        def extraer_seccion(texto, desde_patron, hasta_patron=None):
            """Extrae el fragmento de texto entre dos patrones."""
            m = re.search(desde_patron, texto, re.IGNORECASE)
            if not m:
                return ""
            inicio = m.start()
            if hasta_patron:
                m2 = re.search(hasta_patron, texto[inicio + 1:], re.IGNORECASE)
                fin = inicio + 1 + m2.start() if m2 else len(texto)
            else:
                fin = len(texto)
            return texto[inicio:fin]

        # Texto solo de sección 6 (MATERIALES)
        texto_sec6 = extraer_seccion(texto_completo, r"6\.?\s*[-–]?\s*MATERIALES", r"7\.?\s*[-–]?\s*IMPLEMENTOS")
        # Texto de secciones 7 a 11
        texto_sec7_11 = extraer_seccion(texto_completo, r"7\.?\s*[-–]?\s*IMPLEMENTOS")

        instruccion_compacta = """Eres un extractor de datos JSON para presupuestos de soldadura.
Devuelve SOLO JSON compacto (sin saltos de linea innecesarios, sin indentacion) como una sola linea.
Extrae TODOS los items de las secciones indicadas. No omitas ninguno aunque P.U. sea cero.
Campos por item: categoria (nombre de seccion), descripcion, unidad, cantidad, precio_unitario, dias, total.
total = cantidad * precio_unitario * dias.
Formato de salida OBLIGATORIO (compacto):
{"materiales_y_equipos":[{"categoria":"X","descripcion":"X","unidad":"X","cantidad":1,"precio_unitario":0.0,"dias":1.0,"total":0.0}]}"""

        # ─── Llamada 2a: Solo MATERIALES (seccion 6) ───
        resp2a = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": instruccion_compacta + "\nExtrae SOLO la seccion 6 MATERIALES."},
                {"role": "user", "content": f"Texto de seccion MATERIALES:\n\n{texto_sec6 or texto_completo}"}
            ],
            response_format={"type": "json_object"},
            max_tokens=8000,
            temperature=0
        )
        raw2a = resp2a.choices[0].message.content
        print(f"[DEBUG R2a final]: {raw2a[-100:]}")
        lista_materiales = json.loads(limpiar_json_ia(raw2a)).get("materiales_y_equipos", [])

        # ─── Llamada 2b: Secciones 7-11 (Implementos, Petroleo, Gasolina, Topico, Equipos) ───
        resp2b = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": instruccion_compacta + "\nExtrae SOLO las secciones 7 (IMPLEMENTOS DE SEGURIDAD), 8 (PETROLEO), 9 (GASOLINA), 10 (TOPICO), 11 (EQUIPOS)."},
                {"role": "user", "content": f"Texto secciones 7 al 11:\n\n{texto_sec7_11 or paginas[-1]}"}
            ],
            response_format={"type": "json_object"},
            max_tokens=4000,
            temperature=0
        )
        raw2b = resp2b.choices[0].message.content
        print(f"[DEBUG R2b final]: {raw2b[-100:]}")
        lista_otros = json.loads(limpiar_json_ia(raw2b)).get("materiales_y_equipos", [])

        # ─────────────────────────────────────────────────────────────
        # MERGE: Combinar todas las respuestas
        # ─────────────────────────────────────────────────────────────
        resultado_final = {
            "proyecto_info": datos_fijos.get("proyecto_info", {}),
            "mano_de_obra": datos_fijos.get("mano_de_obra", []),
            "materiales_y_equipos": lista_materiales + lista_otros
        }

        print(f"✔ Extraccion completada: {len(resultado_final['mano_de_obra'])} costos fijos, {len(resultado_final['materiales_y_equipos'])} costos variables ({len(lista_materiales)} materiales + {len(lista_otros)} otros)")
        return resultado_final

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
