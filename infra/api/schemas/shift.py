from uuid import UUID

from pydantic import BaseModel


class ShiftCreate(BaseModel):
    pass


class ShiftResponse(BaseModel):
    id: UUID
    status: str


class ShiftUpdate(BaseModel):
    status: str
