import pdfplumber
import os

def extract_all_materials(pdf_path):
    print(f"Extracting all materials from {os.path.basename(pdf_path)}:")
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            for line in text.split("\n"):
                if "RRCITA" in line or "IMPLEMENTOS DE SEGURIDAD" in line.upper():
                    print(line)

if __name__ == "__main__":
    extract_all_materials(r"d:\vps-program-proyects\control_soldadura\HABILITADO_TECHO_DINO_ALMACEN_NUEVO_DINO_TECHO.pdf")
