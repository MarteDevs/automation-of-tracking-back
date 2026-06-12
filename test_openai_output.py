import asyncio
import os
import sys
import json
import pdfplumber
from openai import AsyncOpenAI
from dotenv import load_dotenv

sys.path.append(os.path.abspath("."))
load_dotenv()

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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

import re

async def test_openai():
    pdf_path = r"d:\vps-program-proyects\control_soldadura\HABILITADO_TECHO_DINO_ALMACEN_NUEVO_DINO_TECHO.pdf"
    paginas = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                paginas.append(text)
    texto_completo = "\n".join(paginas)

    # Let's apply our correction
    from app.services.openai_service import corregir_linea_presupuesto
    lineas_corregidas = []
    for line in texto_completo.split("\n"):
        lineas_corregidas.append(corregir_linea_presupuesto(line))
    texto_completo = "\n".join(lineas_corregidas)

    texto_sec7_11 = extraer_seccion(texto_completo, r"7\.?\s*[-–]?\s*IMPLEMENTOS")

    instruccion_compacta = """Eres un extractor de datos JSON para presupuestos de soldadura.
Devuelve SOLO JSON compacto. Extrae TODOS los items indicados. No omitas ninguno.
Campos: categoria, descripcion, unidad, cantidad, precio_unitario, dias, total.
Formato: {"materiales_y_equipos":[{"categoria":"X","descripcion":"X","unidad":"X","cantidad":1,"precio_unitario":0.0,"dias":1.0,"total":0.0}]}
REGLA CRITICA: Para el campo "categoria", asigna un titulo claro y legible como "MATERIALES", "EQUIPOS", o "IMPLEMENTOS". NUNCA metas texto basura ni codigos raros (como "RRCITA")."""

    system_prompt = "Extrae SOLO las secciones 7 al 11. IMPORTANTE: Asigna la 'categoria' al nombre semántico de su sección (ej: EQUIPOS DE PROTECCION, IMPLEMENTOS, etc)."

    print("Calling OpenAI API...")
    r = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": instruccion_compacta + "\n" + system_prompt},
            {"role": "user", "content": texto_sec7_11}
        ],
        response_format={"type": "json_object"},
        max_tokens=4000,
        temperature=0
    )
    raw = r.choices[0].message.content
    print("=== RAW RESPONSE ===")
    print(raw)

if __name__ == "__main__":
    asyncio.run(test_openai())
