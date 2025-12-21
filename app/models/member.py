from enum import Enum

from sqlmodel import SQLModel

from app.models.user import UserPublic


class AccessLevel(str, Enum):
    VIEW = "view"
    EDIT = "edit"
    
class MemberPublic(SQLModel):
    user: UserPublic
    access: AccessLevel
    
class MemberUpdate(SQLModel):
    access: AccessLevel