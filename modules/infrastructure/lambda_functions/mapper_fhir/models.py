from pydantic import BaseModel, Field
from typing import Optional, List


class Documento(BaseModel):
    tipo: str = Field(..., description="Tipo de documento (CC, TI, CE, etc.)")
    numero: str = Field(..., description="Número de documento")


class Contacto(BaseModel):
    telefono: Optional[str] = None
    email: Optional[str] = None
    metodo_comunicacion_preferido: Optional[str] = None


class Direccion(BaseModel):
    linea: str
    ciudad: str
    departamento: str
    pais: str


class Especialidad(BaseModel):
    nombre: str
    codigo: Optional[str] = None


class DatosAcademicos(BaseModel):
    universidad: str
    titulo: Optional[str] = None
    anio_graduacion: Optional[int] = None


class ProfesionalData(BaseModel):
    nombres: str
    apellidos: str

    documento: Documento

    rethus: str = Field(..., description="Registro RETHUS del profesional")
    profesion: str = Field(..., description="Profesión del profesional")
    especialidad: str = Field(..., description="Especialidad principal")

    datos_academicos: DatosAcademicos

    contacto: Optional[Contacto] = None
    direccion: Optional[Direccion] = None
    especialidades: Optional[List[Especialidad]] = None
    institucion: Optional[str] = None



class Location(BaseModel):
    identifier_value: Optional[str] = None
    identifier_system: Optional[str] = "urn:demo:location"

    status: Optional[str] = None
    name: Optional[str] = None
    alias: Optional[List[str]] = None
    description: Optional[str] = None
    mode: Optional[str] = None

    # type_codings: [{system, code, display}]
    type_codings: Optional[List[dict]] = None

    # address (puede venir como objeto)
    address: Optional[dict] = None

    # o address plano
    address_line: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    # position
    position: Optional[dict] = None  # {"longitude":..., "latitude":..., "altitude":...}

    managing_organization_id: Optional[str] = None
    part_of_location_id: Optional[str] = None


class PayerDataIn(BaseModel):
    name: str
    identifier_type: str
    identifier_value: str
    provider_identifier: str
    provider_class: str
    phone: str
    address_line: str
    city: str
    country: str
    active: bool


class Nacionalidad(BaseModel):
    codigo_pais: str = Field(..., min_length=2, max_length=2, description="ISO-3166-1 alpha-2")
    pais: str

class Residencia(BaseModel):
    codigo_pais: str = Field(..., min_length=2, max_length=2)
    pais: str
    codigo_municipio: str
    municipio: str
    zona_territorial: str

class PatientData(BaseModel):
    # Obligatorios (Res 1888)
    primer_nombre: str
    segundo_nombre: str
    primer_apellido: str
    segundo_apellido: str

    documento: Documento
    fecha_nacimiento: str

    nacionalidad: Nacionalidad

    sexo_biologico: str
    identidad_genero: str
    etnia: str
    comunidad_etnica: str
    categoria_discapacidad: str

    residencia: Residencia

    # Opcionales (no los pide la 1888 en tu lista)
    contacto: Optional[Contacto] = None
    direccion: Optional[Direccion] = None
    informacion_discapacidad: Optional[dict] = None
    necesidades_especiales: Optional[dict] = None
    cuidador_principal: Optional[dict] = None
    informacion_medica: Optional[dict] = None