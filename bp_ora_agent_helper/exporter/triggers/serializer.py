from typing import List, Optional
from pydantic import BaseModel
from ..serializers import ObjectTypes, Dependency


class TriggerDetails(BaseModel):
    type: ObjectTypes = ObjectTypes.TRIGGER

    schema: str
    name: str
    dependencies: List[Dependency] = []
    referenced_columns: List[str] = []
    definition: Optional[str] = None
    summary: Optional[str] = None
