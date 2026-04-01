from typing import List, Optional
from pydantic import BaseModel
from ..serializers import ObjectTypes, Parameter, Dependency


class Routine(BaseModel):
    schema: str
    name: str
    parameters: List[Parameter] = []
    dependencies: List[Dependency] = []
    signature: Optional[str] = None
    definition: Optional[str] = None


class Function(Routine):
    type: ObjectTypes = ObjectTypes.FUNCTION
    return_type: Optional[str] = None


class Procedure(Routine):
    type: ObjectTypes = ObjectTypes.PROCEDURE
