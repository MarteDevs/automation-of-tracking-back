# 🏗️ API Backend - Sistema de Control de Proyectos de Soldadura

## 📖 Descripción del Proyecto
Esta es una API RESTful desarrollada en Python para automatizar la gestión, costeo y seguimiento de proyectos del área de soldadura (Distribuidora Derek). El sistema ingesta archivos PDF de presupuestos crudos, utiliza Inteligencia Artificial (OpenAI) para extraer y estructurar los datos, y los almacena en una base de datos relacional para permitir el control de avances semanales y la generación de reportes estandarizados.

## 🚀 Tecnologías y Arquitectura
El proyecto utiliza una **Arquitectura en Capas** (Controladores, Servicios, Modelos) para separar la lógica de negocio del acceso a datos, garantizando escalabilidad y fácil mantenimiento.

*   **Framework Web:** [FastAPI](https://fastapi.tiangolo.com/) (Rápido, asíncrono y auto-documentado).
*   **Motor de IA:** API de OpenAI (para extracción estructurada de texto/JSON).
*   **Base de Datos:** SQLite (Desarrollo) / Listo para migrar a MySQL (Producción).
*   **ORM:** SQLAlchemy.
*   **Servidor ASGI:** Uvicorn.

## 📊 Estructura de Datos Analizada (Extracción de PDF)
El sistema ha sido entrenado y estructurado para comprender y procesar los siguientes formatos de las plantillas de control de la empresa:

1.  **Datos Generales del Proyecto (Cabecera):**
    *   Nombre de la obra, cliente, ubicación.
    *   Cálculo de Costo Directo, Gastos Generales (10%), Utilidad (15%) e IGV (18%).
2.  **Mano de Obra (Desglosada):**
    *   Cargos (ej. Maestro soldador, Ayudante, Ingeniero Residente).
    *   Días trabajados, precio unitario (tarea/día).
    *   Cálculo de Leyes Sociales (ej. 104.08%) y viáticos (Alimentación).
3.  **Materiales, Herramientas y Equipos:**
    *   Insumos directos (Planchas, tubos, soldadura, pintura).
    *   Costos variables (Alquiler de máquinas, torno, plasma, herramientas manuales).
    *   Costos fijos operacionales (Vigilancia, energía, alquiler de local).
4.  **Implementos de Seguridad (EPP):**
    *   Guantes, cascos, respiradores, arnés, etc.
5.  **Control de Avances (Gestión Semanal):**
    *   Registro del porcentaje de avance (ej. "Habilitación de material 70%", "Lavado 50%").
    *   Evidencia fotográfica y observaciones.

## 📁 Estructura del Directorio

```text
proyecto_control_soldadura/
│
├── app/                      # Código fuente de la aplicación
│   ├── __init__.py
│   ├── main.py               # Punto de entrada de FastAPI
│   ├── api/                  # Capa de Presentación (Endpoints/Rutas)
│   │   └── endpoints.py
│   ├── services/             # Capa de Lógica de Negocio (IA y Procesamiento)
│   │   └── openai_service.py # Integración con OpenAI para procesar PDFs
│   ├── models/               # Capa de Datos (Tablas y Conexión BD)
│   │   ├── database.py       # Configuración del motor y sesión SQLAlchemy
│   │   └── models.py         # Definición de tablas (Proyectos, ManoObra, etc.)
│   └── schemas/              # Capa de Validación (Pydantic Models)
│       └── project_schema.py 
│
├── temp/                     # Almacenamiento temporal de PDFs subidos
├── .env                      # Variables de entorno (API Keys, Credenciales)
├── requirements.txt          # Dependencias de Python
└── README.md                 # Documentación del proyecto
