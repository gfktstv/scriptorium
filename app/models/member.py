from enum import Enum

from sqlmodel import SQLModel


class AccessLevel(str, Enum):
    VIEW = "view"
    EDIT = "edit"
    
class MemberUpdate(SQLModel):
    access: AccessLevel