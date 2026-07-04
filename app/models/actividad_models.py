from pydantic import BaseModel


class ObjetivoActividad(BaseModel):
    pasos_diarios: int
