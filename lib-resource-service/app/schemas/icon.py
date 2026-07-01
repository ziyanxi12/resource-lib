from pydantic import BaseModel


class IconSyncResponse(BaseModel):
    added:   int
    updated: int
    message: str
