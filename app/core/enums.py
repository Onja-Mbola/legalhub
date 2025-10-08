from enum import Enum

class RoleEnum(str, Enum):
    admin = "admin"
    avocat = "avocat"
    clerk = "clerk"

class TypeDeCas(str, Enum):
    CONSULTATION = "CONSULTATION"
    CIVIL = "CIVIL"
    PENAL = "PÉNAL"

