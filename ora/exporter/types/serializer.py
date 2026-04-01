from enum import Enum
from typing import List, Optional
from pydantic import BaseModel
from ..serializers import ObjectTypes, Dependency


class OTAttribute(BaseModel):
    name: str
    datatype: str
    nullable: bool = True


class OTMethod(BaseModel):
    name: str
    parameters: List[str] = []
    return_type: Optional[str]


class ObjectTypeDetails(BaseModel):
    type: ObjectTypes = ObjectTypes.OBJECT_TYPE
    schema: str
    name: str
    status: str
    has_methods: bool = False
    attributes: List[OTAttribute] = []
    methods: List[OTMethod] = []
    dependencies: List[Dependency] = []


class CollectionTypes(Enum):
    TABLE = 'table'
    VARRAY = 'varray'


class CollectionTypeDetails(BaseModel):
    type: ObjectTypes = ObjectTypes.COLLECTION_TYPE
    schema: str
    name: str
    collection_type: CollectionTypes  # TABLE или VARRAY
    element_type: str
    dependencies: List[Dependency] = []
