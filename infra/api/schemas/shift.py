from pydantic import BaseModel


class ShiftCreate(BaseModel):
    pass

class ShiftResponse(BaseModel):
    id: str
    status: str

class ShiftUpdate(BaseModel):
    status: str