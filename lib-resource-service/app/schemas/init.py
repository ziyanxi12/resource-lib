from pydantic import BaseModel
from typing import Optional


class TypeResult(BaseModel):
    added:   int
    updated: int
    error:   Optional[str] = None


class InitImportResponse(BaseModel):
    component:    Optional[TypeResult] = None
    svg:          Optional[TypeResult] = None
    illustration: Optional[TypeResult] = None
    template:     Optional[TypeResult] = None
