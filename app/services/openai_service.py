import os
import json
import asyncio
import pdfplumber
import re
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Cargamos las variables de entorno (.env)
load_dotenv()

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def parse_number(s):
    # Remove commas and convert to float
    s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None

def corregir_linea_presupuesto(line):
    # We look for lines containing RRCITA
    if "RRCITA|" not in line:
        return line

    # Split the line by spaces
    tokens = line.split()
    if len(tokens) < 5:
        return line

    # Find the last few numeric tokens
    num_indices = []
    for idx in range(len(tokens) - 1, -1, -1):
        val = parse_number(tokens[idx])
        if val is not None or tokens[idx] in [".00", ".0"]:
            num_indices.append(idx)
        else:
            break
            
    num_indices.reverse()
    if len(num_indices) < 3:
        return line

    # Let's extract the numeric tokens
    num_tokens = [tokens[i] for i in num_indices]
    prefix_tokens = tokens[:num_indices[0]]
    total_val = parse_number(num_tokens[-1])
    if total_val is None or total_val == 0:
        return line

    # Helper to generate all partitions of list into k non-empty contiguous sublists
    def get_partitions(lst, k):
        if k == 1:
            yield [lst]
            return
        for i in range(1, len(lst) - k + 2):
            for p in get_partitions(lst[i:], k - 1):
                yield [lst[:i]] + p

    for partition in get_partitions(num_tokens, 4):
        merged_vals = []
        valid = True
        for part in partition:
            combined = "".join(part)
            val = parse_number(combined)
            if val is None:
                valid = False
                break
            merged_vals.append((combined, val))
        
        if not valid:
            continue
            
        qty_str, qty_val = merged_vals[0]
        pu_str, pu_val = merged_vals[1]
        days_str, days_val = merged_vals[2]
        tot_str, tot_val = merged_vals[3]
        
        # Check if qty * pu * days = tot
        if abs(qty_val * pu_val * days_val - total_val) < 1.0:
            # Reconstruct the line
            new_line = " ".join(prefix_tokens) + f" {qty_str} {pu_str} {days_str} {tot_str}"
            return new_line

    return line

def limpiar_json_ia(texto: str) -> str:
    """Limpia la respuesta de la IA para garantizar JSON puro parseable."""
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

async def analizar_presupuesto_pdf(ruta_archivo_pdf):
    """
    Lee el texto del PDF con llamadas asíncronas y paralelas a la IA para optimizar
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

        # Corregir números divididos por espacios en las líneas antes de enviar a la IA
        lineas_corregidas = []
        for line in texto_completo.split("\n"):
            lineas_corregidas.append(corregir_linea_presupuesto(line))
        texto_completo = "\n".join(lineas_corregidas)

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

        Estructura JSON obligatoria:
        {
            "proyecto_info": {"nombre_proyecto": "", "fecha": "", "costo_total": 0.0, "utilidad_porcentaje": 0.0, "otros_porcentaje": 0.0},
            "mano_de_obra": [
                {"categoria": "MANO DE OBRA", "descripcion": "TOTAL MANO DE OBRA", "unidad": "Global", "cantidad_trabajadores": 1, "precio_unitario": 0.0, "dias": 1, "total": 0.0}
            ],
            "materiales_y_equipos": []
        }
        """

        resp1 = await client.chat.completions.create(
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
        datos_fijos = json.loads(limpiar_json_ia(raw1))

        # ─────────────────────────────────────────────────────────────
        # Preparar llamadas paralelas para secciones de variables
        # ─────────────────────────────────────────────────────────────
        import re
        def extraer_seccion(texto, desde_patron, hasta_patron=None):
            m = re.search(desde_patron, texto, re.IGNORECASE)
            if not m: return ""
            inicio = m.start()
            if hasta_patron:
                m2 = re.search(hasta_patron, texto[inicio + 1:], re.IGNORECASE)
                fin = inicio + 1 + m2.start() if m2 else len(texto)
            else:
                fin = len(texto)
            return texto[inicio:fin]

        texto_sec6 = extraer_seccion(texto_completo, r"6\.?\s*[-–]?\s*MATERIALES", r"7\.?\s*[-–]?\s*IMPLEMENTOS")
        texto_sec7_11 = extraer_seccion(texto_completo, r"7\.?\s*[-–]?\s*IMPLEMENTOS")

        instruccion_compacta = """Eres un extractor de datos JSON para presupuestos de soldadura.
Devuelve SOLO JSON compacto. Extrae TODOS los items indicados. No omitas ninguno.
Campos: categoria, descripcion, unidad, cantidad, precio_unitario, dias, total.
Formato: {"materiales_y_equipos":[{"categoria":"X","descripcion":"X","unidad":"X","cantidad":1,"precio_unitario":0.0,"dias":1.0,"total":0.0}]}
REGLA CRITICA: Para el campo "categoria", asigna uno de los siguientes nombres exactos: "MATERIALES", "IMPLEMENTOS DE SEGURIDAD", "PETROLEO", "GASOLINA", "TOPICO", o "EQUIPOS Y/OTROS SERCICIOS (VARIABLE)". NUNCA metas texto basura ni codigos raros (como "RRCITA").

REGLAS DE RECONSTRUCCIÓN DE NÚMEROS (CRÍTICAS):
1. El valor de la columna "Total S/." (última columna numérica) en el PDF es la VERDAD ABSOLUTA y NUNCA debe ser modificado ni recalculado en el JSON resultante.
2. A veces la extracción de texto del PDF introduce espacios no deseados en los números (ej. "1 26.00" en lugar de "126.00", "5 00.00" en lugar de "500.00", "4 .00" en lugar de "4.00", "2 0.00" en lugar de "20.00").
3. Si al tomar los números tal como están, la multiplicación de (cantidad * precio_unitario * dias) NO es igual al "total" de la columna, significa que la cantidad o el precio unitario están divididos por un espacio.
4. RECONSTRUYE los valores correctos de cantidad y precio_unitario para que su producto coincida EXACTAMENTE con el "total" indicado en el PDF. NUNCA alteres el "total" del PDF para acomodarlo a una cantidad o precio unitario incorrectos.
Ejemplos:
- "M2 1 26.00 18.00 1.0 2,268.00" -> total es 2268.00. Uniendo "1" y "26.00" obtenemos cantidad=126.0 y precio_unitario=18.0, ya que 126 * 18 * 1 = 2268.00.
- "UND 5 00.00 0.20 1.0 100.00" -> total es 100.00. Uniendo "5" y "00.00" obtenemos cantidad=500.0 y precio_unitario=0.20, ya que 500 * 0.2 * 1 = 100.00.
- "UND 1 2.00 105.00 1.0 1,260.00" -> total es 1260.00. Uniendo "1" y "2.00" obtenemos cantidad=12.0 y precio_unitario=105.0, ya que 12 * 105 * 1 = 1260.00.
- "UND 4 0.00 105.00 1.0 4,200.00" -> total es 4200.00. Uniendo "4" y "0.00" obtenemos cantidad=40.0 y precio_unitario=105.0, ya que 40 * 105 * 1 = 4200.00.
- "KG 2 0.00 21.00 1.0 420.00" -> total es 420.00. Uniendo "2" y "0.00" obtenemos cantidad=20.0 y precio_unitario=21.0, ya que 20 * 21 * 1 = 420.00.
- "UND 1 5.00 25.00 1.0 375.00" -> total es 375.00. Uniendo "1" y "5.00" obtenemos cantidad=15.0 y precio_unitario=25.0, ya que 15 * 25 * 1 = 375.00.
- "UND 1 .00 23.00 1.0 23.00" -> total es 23.00. Uniendo "1" y ".00" obtenemos cantidad=1.0 y precio_unitario=23.0, ya que 1 * 23 * 1 = 23.00.
"""

        # Disparamos las dos llamadas pesadas en paralelo
        async def call_ai(system_prompt, user_content, tokens=4000):
            r = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": instruccion_compacta + "\n" + system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                max_tokens=tokens,
                temperature=0
            )
            return json.loads(limpiar_json_ia(r.choices[0].message.content)).get("materiales_y_equipos", [])

        # Ejecución concurrente
        print("[IA] Lanzando extracciones paralelas...")
        results = await asyncio.gather(
            call_ai("Extrae SOLO la seccion 6 MATERIALES. IMPORTANTE: En el JSON, la 'categoria' SIEMPRE debe ser exactamente 'MATERIALES' (mayusculas).", f"Texto:\n\n{texto_sec6 or texto_completo}", tokens=8000),
            call_ai("Extrae las secciones 7, 8, 9, 10 y 11. REGLA DE CATEGORÍAS OBLIGATORIA: Para el campo 'categoria', debes usar exactamente una de estas categorías según corresponda a la sección:\n"
                    "- Para items de la sección 7 (IMPLEMENTOS DE SEGURIDAD) usa 'IMPLEMENTOS DE SEGURIDAD'.\n"
                    "- Para items de la sección 8 (PETROLEO) usa 'PETROLEO'.\n"
                    "- Para items de la sección 9 (GASOLINA) usa 'GASOLINA'.\n"
                    "- Para items de la sección 10 (TOPICO) usa 'TOPICO'.\n"
                    "- Para items de la sección 11 (EQUIPOS Y/OTROS SERCICIOS) usa 'EQUIPOS Y/OTROS SERCICIOS (VARIABLE)'.\n"
                    "No omitas ningún elemento de ninguna de estas secciones.", f"Texto:\n\n{texto_sec7_11 or paginas[-1]}", tokens=4000)
        )
        
        lista_materiales, lista_otros = results

        # Combinar resultados
        resultado_final = {
            "proyecto_info": datos_fijos.get("proyecto_info", {}),
            "mano_de_obra": datos_fijos.get("mano_de_obra", []),
            "materiales_y_equipos": lista_materiales + lista_otros
        }

        print(f"[IA] Extraccion completada en paralelo: {len(resultado_final['mano_de_obra'])} fijos, {len(resultado_final['materiales_y_equipos'])} variables.")
        return resultado_final

    except Exception as e:
        print(f"Error al procesar el documento con OpenAI: {e}")
        return None

async def generar_resumen_ejecutivo_avance(nombre_proyecto, semana, porcentaje, observaciones, tipo_periodo="SEMANA"):
    """Genera un reporte profesional usando IA de forma asíncrona."""
    try:
        obs_texto = observaciones if observaciones else "Ninguna novedad técnica reportada para este periodo."
        
        # Determinar etiquetas según el tipo de periodo
        adj_periodo = "semanal"
        if tipo_periodo == "HORA": adj_periodo = "por horas"
        elif tipo_periodo == "DIA": adj_periodo = "diario"
        
        label_periodo = "Semana"
        if tipo_periodo == "HORA": label_periodo = "Hora"
        elif tipo_periodo == "DIA": label_periodo = "Día"

        prompt = f"""
        Eres un Ingeniero Residente. Redacta un "RESUMEN EJECUTIVO" muy formal (un solo párrafo sólido) para el informe {adj_periodo} en PDF.
        Datos: Proyecto {nombre_proyecto}, {label_periodo} N° {semana}, Progreso {porcentaje}%, Obs: {obs_texto}.
        Reglas: Cero saludos, un solo párrafo fluido, tono corporativo.
        """
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error AI resumen: {e}")
        return f"En esta semana {semana}, se alcanzó un avance del {porcentaje}%. Las actividades transcurren sin detención. {obs_texto}"

async def generar_interpretacion_balance(nombre_proyecto, semana, ppto_total_igv, total_gast, total_ppto_mat, saldo_global, tipo_periodo="SEMANA"):
    """Genera una interpretación financiera del balance de materiales usando IA."""
    try:
        ahorro_porc = ((total_ppto_mat - total_gast) / total_ppto_mat * 100) if total_ppto_mat > 0 else 0
        
        label_periodo = "semana"
        if tipo_periodo == "HORA": label_periodo = "hora"
        elif tipo_periodo == "DIA": label_periodo = "día"
        elif tipo_periodo == "GLOBAL": label_periodo = "cierre"

        prompt = f"""
Eres un analista financiero de proyectos de construcción metalmecánica.
Redacta UN SOLO PÁRRAFO formal (máximo 5 líneas) interpretando el siguiente balance de materiales. Tono profesional y concreto.

Datos del Proyecto "{nombre_proyecto}" al corte de la {label_periodo} {semana}:
- Presupuesto Total del Proyecto (con IGV): S/ {ppto_total_igv:,.2f}
- Presupuesto Asignado a Materiales: S/ {total_ppto_mat:,.2f}
- Materiales Gastados (acumulado): S/ {total_gast:,.2f}
- Saldo Disponible en Materiales: S/ {saldo_global:,.2f}
- Porcentaje restante en materiales: {ahorro_porc:.1f}%

Indica si el consumo es eficiente, si hay riesgo de sobregiro, y una recomendación concreta.
REGLA CRITICA: Como el proyecto está en ejecución, NO uses la palabra "ahorro" (usa "remanente" o "saldo a favor").
Reglas: Sin saludos, sin títulos, solo el párrafo fluido.
        """
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error AI balance: {e}")
        if saldo_global >= 0:
            return f"Al corte de la semana {semana}, el consumo acumulado de materiales se mantiene dentro del presupuesto establecido, registrando un saldo positivo de S/ {saldo_global:,.2f}. Se recomienda mantener el ritmo de control para garantizar la eficiencia financiera hasta el cierre del proyecto."
        else:
            return f"Al corte de la semana {semana}, el consumo acumulado de materiales ha superado el presupuesto en S/ {abs(saldo_global):,.2f}. Se advierte riesgo de sobregiro. Se recomienda revisar el uso de insumos y ajustar las compras para las semanas restantes."
