import uvicorn

if __name__ == "__main__":
    # Script puente seguro para aislar PM2 de los binarios ELF de Linux.
    # Lanza `app.main:app` natívamente a través de Python puro.
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, workers=2)
