from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class ClientCreate(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class ClientUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class ClientOut(BaseModel):
    id: UUID
    full_name: str
    email: Optional[str]
    phone: Optional[str]

    class Config:
        orm_mode = True
