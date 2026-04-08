import requests
import json

url = "http://localhost:8000/api/v1/procesar-presupuesto/"
pdf_path = r"d:\vps-program-proyects\proyecto_control_soldadura\temp\AGUZADO_CHOTANAS_ESPERANZA_CHOTANAS.pdf"

print(f"Probando endpoint con archivo: {pdf_path}")

try:
    with open(pdf_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files)

    print("Status Code:", response.status_code)
    print("Response:")
    try:
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    except Exception as e:
        print(response.text)
except FileNotFoundError:
    print(f"Error: El archivo {pdf_path} no existe.")
except Exception as e:
    print(f"Error en la petición: {e}")
