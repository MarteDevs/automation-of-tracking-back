from pydantic import BaseModel
from typing import List, Optional

# --- SCHEMAS BASE (Para crear/leer) ---

class ProyectoInfoBase(BaseModel):
    nombre_proyecto: str
    fecha: str
    costo_total: float
    utilidad_porcentaje: float

class ManoObraBase(BaseModel):
    descripcion: str
    cantidad_trabajadores: float
    precio_unitario: float
    total: float

class MaterialEquipoBase(BaseModel):
    descripcion: str
    cantidad: float
    unidad: str
    total: float

class AvanceSemanalBase(BaseModel):
    semana: int
    porcentaje_avance: float
    observaciones: Optional[str] = None
    rutas_fotografias: Optional[str] = None

class AvanceSemanalCreate(AvanceSemanalBase):
    pass

# --- SCHEMA DEL JSON DE OPENAI ---
# Este schema validará exactamente lo que extraiga OpenAI del PDF

class PresupuestoExtraidoSchema(BaseModel):
    proyecto_info: ProyectoInfoBase
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

class AvanceSemanalResponse(AvanceSemanalBase):
    id: int
    proyecto_id: int

    class Config:
        from_attributes = True

class ProyectoResponse(ProyectoInfoBase):
    id: int
    mano_de_obra: List[ManoObraResponse] = []
    materiales: List[MaterialEquipoResponse] = []
    avances: List[AvanceSemanalResponse] = []

    class Config:
        from_attributes = True
