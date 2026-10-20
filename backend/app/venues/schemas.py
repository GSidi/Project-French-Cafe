"""Venues: Pydantic request/response models -- the JSON contract."""
from pydantic import BaseModel

class VenueSummary(BaseModel):
    id: int
    name: str
    address: str | None
    free_tables: int
    total_tables: int

