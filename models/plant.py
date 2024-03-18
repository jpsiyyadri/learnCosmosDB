from pydantic import BaseModel


class Plant(BaseModel):
    name: str
    description: str
    price: float
    id: str
