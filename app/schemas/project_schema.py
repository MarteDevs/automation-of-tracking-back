from pydantic import BaseModel, model_validator
from typing import List, Optional, Any

# --- SCHEMAS BASE (Para crear/leer) ---

class ProyectoBase(BaseModel):
    nombre_proyecto: str
    fecha: str
    costo_total: float
    utilidad_porcentaje: float
    otros_porcentaje: Optional[float] = 5.0
    semanas_estimadas: Optional[int] = 0
    tipo_duracion: Optional[str] = "SEMANAS"
    ruta_pdf: Optional[str] = None

class ProyectoCreate(ProyectoBase):
    pass

class ProyectoUpdate(BaseModel):
    semanas_estimadas: int
    tipo_duracion: str
    fecha: str

class ManoObraBase(BaseModel):
    descripcion: str
    categoria: Optional[str] = "Mano de Obra"
    unidad: Optional[str] = ""
    cantidad_trabajadores: Optional[float] = None
    precio_unitario: float
    dias: Optional[float] = 1.0
    total: float

    @model_validator(mode='before')
    @classmethod
    def aceptar_cantidad_como_alias(cls, data: Any) -> Any:
        """Si la IA manda 'cantidad' en vez de 'cantidad_trabajadores', lo normalizamos."""
        if isinstance(data, dict):
            if data.get('cantidad_trabajadores') is None and 'cantidad' in data:
                data['cantidad_trabajadores'] = data['cantidad']
            # Si sigue siendo None, default a 1.0
            if data.get('cantidad_trabajadores') is None:
                data['cantidad_trabajadores'] = 1.0
        return data

class MaterialEquipoBase(BaseModel):
    descripcion: str
    categoria: Optional[str] = "Materiales"
    cantidad: float
    unidad: str
    precio_unitario: Optional[float] = 0.0
    dias: Optional[float] = 1.0
    total: float

class ConsumoMaterialBase(BaseModel):
    nombre_material: str
    cantidad_usada: float
    unidad: Optional[str] = ""

class AvanceSemanalBase(BaseModel):
    semana: int
    porcentaje_avance: float
    observaciones: Optional[str] = None
    rutas_fotografias: Optional[str] = None
    tipo_periodo: str = "SEMANA"  # SEMANA o DIA
    fecha_fin: Optional[str] = None
    dias_trabajados: Optional[float] = 0
    ruta_pdf: Optional[str] = None

class AvanceSemanalCreate(AvanceSemanalBase):
    consumos_materiales: Optional[List[ConsumoMaterialBase]] = []

# --- SCHEMA DEL JSON DE OPENAI ---
# Este schema validará exactamente lo que extraiga OpenAI del PDF

class PresupuestoExtraidoSchema(BaseModel):
    proyecto_info: ProyectoBase
    mano_de_obra: List[ManoObraBase]
    materiales_y_equipos: List[MaterialEquipoBase]

# --- SCHEMAS DE RESPUESTA DE LA BASE DE DATOS ---
# Incluyen el 'id' generado por la BD y configuran el orm_mode (from_attributes en Pydantic V2)

class ManoObraResponse(ManoObraBase):
    id: int
    proyecto_id: int

    class Config:
        from_attributes = True

class MaterialEquipoResponse(MaterialEquipoBase):
    id: int
    proyecto_id: int

    class Config:
        from_attributes = True

class ConsumoMaterialResponse(ConsumoMaterialBase):
    id: int
    avance_id: int

    class Config:
        from_attributes = True

class AvanceSemanalResponse(AvanceSemanalBase):
    id: int
    proyecto_id: int
    consumos: List[ConsumoMaterialResponse] = []

    class Config:
        from_attributes = True

class ProyectoResponse(ProyectoBase):
    id: int
    mano_de_obra: List[ManoObraResponse] = []
    materiales: List[MaterialEquipoResponse] = []
    avances: List[AvanceSemanalResponse] = []

    class Config:
        from_attributes = True
