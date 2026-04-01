from typing import List, Optional
from pydantic import BaseModel
from ..serializers import ObjectTypes, Parameter, Dependency


class PackagePublicRoutine(BaseModel):
    name: str
    overload: int
    type: ObjectTypes
    parameters: List[Parameter] = []
    return_type: Optional[str] = None


class Package(BaseModel):
    type: ObjectTypes = ObjectTypes.PACKAGE
    schema: str
    name: str
    spec_dependencies: List[Dependency] = []
    body_dependencies: List[Dependency] = []
    has_body: bool = True
    public_routines: List[PackagePublicRoutine] = []
