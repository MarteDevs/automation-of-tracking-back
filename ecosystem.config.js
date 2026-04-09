module.exports = {
  apps: [
    {
      name: 'control-soldadura-api',
      
      // Llamamos al archivo nativo de Python para evadir problemas de Binarios Node JS (ELF Error)
      script: 'start.py',
      
      // Asignamos el interprete Oficial de tu Entorno Virtual
      interpreter: './venv/bin/python',
      
      // Auto-reinicio por control de limite de RAM en libreria FPDF PDF
      max_memory_restart: '500M',

      env: {
        NODE_ENV: 'production'
      }
    }
  ]
};
