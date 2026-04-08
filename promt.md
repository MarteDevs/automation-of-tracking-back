Actúa como un Arquitecto de Software y Desarrollador Backend Senior experto en Python, FastAPI, SQLAlchemy y la API de OpenAI.

CONTEXTO DEL PROYECTO:
Estoy desarrollando una API RESTful para "Distribuidora Derek" (Área de Soldadura). El objetivo del sistema es automatizar la creación de informes de control de proyectos a partir de PDFs de presupuestos en crudo y permitir el seguimiento del avance semanal de las obras. 

TECNOLOGÍAS Y ARQUITECTURA:
- Framework: FastAPI
- Base de Datos: SQLite (para desarrollo local) con vistas a migrar a MySQL.
- ORM: SQLAlchemy
- IA: API de OpenAI (gpt-4o-mini o similar) para extracción de datos estructurados.
- Arquitectura: Capas (Layered Architecture) separando la lógica en: Controladores (api/endpoints), Servicios (services/ia_service), Datos (models/database, models/models) y Validación (schemas).

ANÁLISIS DE DATOS Y FLUJO (REGLAS DE NEGOCIO):
El sistema debe procesar PDFs que contienen costeo de proyectos metalmecánicos. Los datos extraídos deben mapearse a las siguientes entidades relacionales en la base de datos:

1. Tabla "Proyectos" (Plantilla 01):
   - Datos base: nombre_proyecto, fecha, costo_total, utilidad_porcentaje, cliente, ubicacion.
   - Debe calcular y manejar: Costo Directo, Gastos Generales (10%), Utilidad (15%) e IGV (18%).

2. Tabla "ManoObra" (Relacionada a Proyectos):
   - Desglose de trabajadores: descripcion (ej. Maestro soldador, Ayudante), cantidad_trabajadores, precio_unitario (por día/tarea), total. Incluye cálculo de "Leyes Sociales" (ej. 104.08%) y viáticos (Alimentación).

3. Tabla "MaterialesEquipos" (Relacionada a Proyectos):
   - Insumos directos, costos variables (maquinaria, alquiler), implementos de seguridad (EPP) y costos fijos (vigilancia, energía).
   - Campos: descripcion, cantidad, unidad, total.

4. Tabla "AvancesSemanales" (Plantilla 02):
   - Para seguimiento del proyecto a lo largo del tiempo.
   - Campos: proyecto_id, semana (int), porcentaje_avance (float), observaciones (texto), rutas_fotografias (texto/JSON).

ESTRUCTURA DEL DIRECTORIO ACTUAL:
proyecto/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── endpoints.py (Aquí está el endpoint POST /procesar-presupuesto/)
│   ├── services/
│   │   └── openai_service.py (Aquí está la lógica que conecta con OpenAI para extraer el JSON del PDF)
│   ├── models/
│   │   ├── database.py (Config de SQLAlchemy)
│   │   └── models.py (Definición de las 4 tablas mencionadas)
│   └── schemas/
│       └── project_schema.py (Modelos Pydantic para validación)
├── temp/
└── .env

ESTADO ACTUAL:
Ya tengo configurado FastAPI, la conexión a la base de datos SQLite y el endpoint que recibe el PDF, se lo envía a OpenAI y me devuelve un JSON estructurado correctamente.

OBJETIVO INMEDIATO:
[AQUÍ ESCRIBIRÁS LO QUE NECESITAS EN ESE MOMENTO. POR EJEMPLO: "Necesito que me generes los esquemas de Pydantic en `project_schema.py` para validar el JSON que me devuelve OpenAI antes de guardarlo en la base de datos" O "Necesito la lógica CRUD para insertar el JSON extraído en las tablas de SQLAlchemy"].
