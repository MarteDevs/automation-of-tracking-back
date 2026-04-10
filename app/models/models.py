from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from .database import Base

class Proyecto(Base):
    __tablename__ = "proyectos"

    id = Column(Integer, primary_key=True, index=True)
    nombre_proyecto = Column(String, index=True)
    fecha = Column(String) # Puedes usar Date si parseas la fecha del JSON
    costo_total = Column(Float)
    utilidad_porcentaje = Column(Float)
    otros_porcentaje = Column(Float, default=5.0)
    semanas_estimadas = Column(Integer, default=0)
    tipo_duracion = Column(String, default="SEMANAS", server_default="SEMANAS", nullable=False)

    # Relaciones: Un proyecto tiene mucha mano de obra, materiales y avances
    mano_de_obra = relationship("ManoObra", back_populates="proyecto", cascade="all, delete-orphan")
    materiales = relationship("MaterialEquipo", back_populates="proyecto", cascade="all, delete-orphan")
    avances = relationship("AvanceSemanal", back_populates="proyecto", cascade="all, delete-orphan")

class ManoObra(Base):
    __tablename__ = "mano_de_obra"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"))
    descripcion = Column(String)
    categoria = Column(String, default="Mano de Obra")
    unidad = Column(String, default="")
    cantidad_trabajadores = Column(Float)
    precio_unitario = Column(Float)
    dias = Column(Float, default=1.0)
    total = Column(Float)

    proyecto = relationship("Proyecto", back_populates="mano_de_obra")

class MaterialEquipo(Base):
    __tablename__ = "materiales_equipos"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"))
    descripcion = Column(String)
    categoria = Column(String, default="Materiales")
    unidad = Column(String)
    cantidad = Column(Float)
    precio_unitario = Column(Float, default=0.0)
    dias = Column(Float, default=1.0)
    total = Column(Float)

    proyecto = relationship("Proyecto", back_populates="materiales")

class AvanceSemanal(Base):
    __tablename__ = "avances_semanales"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"))
    semana = Column(Integer)
    porcentaje_avance = Column(Float)
    observaciones = Column(String, nullable=True)
    rutas_fotografias = Column(String, nullable=True) # JSON o URL separados por comas
    tipo_periodo = Column(String, default="SEMANA", server_default="SEMANA", nullable=False)
    fecha_fin = Column(String, nullable=True)
    dias_trabajados = Column(Float, default=0)

    proyecto = relationship("Proyecto", back_populates="avances")

