from pydantic import BaseModel

class UserOut(BaseModel):
    id: int
    nom: str
    email: str
    role: str

    class Config:
        orm_mode = True
