from pydantic import BaseModel
from typing import List


class MedicamentoCreate(BaseModel):
    nombre: str
    horas: List[str]
    frecuencia: str
