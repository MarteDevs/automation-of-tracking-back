import pdfplumber
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

def test():
    pdf_path = r"d:\vps-program-proyects\control_soldadura\HABILITADO_TECHO_DINO_ALMACEN_NUEVO_DINO_TECHO.pdf"
    paginas = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                paginas.append(text)
    texto_completo = "\n".join(paginas)

    texto_sec7_11 = extraer_seccion(texto_completo, r"7\.?\s*[-–]?\s*IMPLEMENTOS")
    print("=== EXTRACTED SEC7_11 TEXT ===")
    print(texto_sec7_11)

if __name__ == "__main__":
    test()
