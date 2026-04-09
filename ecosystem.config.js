module.exports = {
  apps: [
    {
      name: 'control-soldadura-api',
      
      // NOTA: Si tu VPS es Linux/Ubuntu, la ruta del entorno virtual es:
      script: './venv/bin/python',
      
      // Si tu VPS es Windows Server, asegúrate de cambiar la linea anterior a:
      // script: '.\\venv\\Scripts\\python.exe',

      // Llamamos al paquete de uvicorn via modulo python
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2',
      
      // PM2 usará el motor que declaramos en `script` directamente
      interpreter: 'none',
      
      // Auto-reinicio si la aplicación consume más de 500MB de RAM (ideal para la libreria FPDF)
      max_memory_restart: '500M',

      env: {
        NODE_ENV: 'production'
      }
    }
  ]
};
