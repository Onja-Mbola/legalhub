from enum import Enum

class RoleEnum(str, Enum):
    admin = "admin"
    avocat = "avocat"
    clarck = "clarck"

class TypeDeCas(str, Enum):
    CONSULTATION = "CONSULTATION"
    CIVIL = "CIVIL"
    PENAL = "PÉNAL"

