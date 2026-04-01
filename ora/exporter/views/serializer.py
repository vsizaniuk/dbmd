from typing import List, Optional
from pydantic import BaseModel
from ..serializers import ObjectTypes, Dependency


class ViewColumn(BaseModel):
    name: str
    type: str
    description: Optional[str] = None


class ViewSchema(BaseModel):
    type: ObjectTypes = ObjectTypes.VIEW
    schema: str
    name: str
    description: Optional[str] = None
    columns: List[ViewColumn]
    definition: str
    dependencies: List[Dependency] = []
    summary: Optional[str] = None