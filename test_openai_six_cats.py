import asyncio
import os
import sys
import pdfplumber
import re
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

async def test_openai():
    pdf_path = r"d:\vps-program-proyects\control_soldadura\HABILITADO_TECHO_DINO_ALMACEN_NUEVO_DINO_TECHO.pdf"
    paginas = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                paginas.append(text)
    texto_completo = "\n".join(paginas)

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
REGLA CRITICA: Para el campo "categoria", asigna exactamente uno de los siguientes nombres semánticos: "IMPLEMENTOS DE SEGURIDAD", "PETROLEO", "GASOLINA", "TOPICO", o "EQUIPOS Y/OTROS SERCICIOS (VARIABLE)"."""

    system_prompt = """Extrae las secciones 7, 8, 9, 10 y 11. REGLA DE CATEGORÍAS OBLIGATORIA: Para el campo 'categoria', debes usar exactamente el nombre semántico de su sección:
- Para items de la sección 7 (IMPLEMENTOS DE SEGURIDAD) usa 'IMPLEMENTOS DE SEGURIDAD'.
- Para items de la sección 8 (PETROLEO) usa 'PETROLEO'.
- Para items de la sección 9 (GASOLINA) usa 'GASOLINA'.
- Para items de la sección 10 (TOPICO) usa 'TOPICO'.
- Para items de la sección 11 (EQUIPOS Y/OTROS SERCICIOS) usa 'EQUIPOS Y/OTROS SERCICIOS (VARIABLE)'.
No omitas ningún elemento de ninguna de estas secciones."""

    print("Calling OpenAI API for sections 7-11...")
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
