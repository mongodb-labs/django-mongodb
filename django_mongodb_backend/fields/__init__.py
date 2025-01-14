from .array import ArrayField
from .auto import ObjectIdAutoField
from .duration import register_duration_field
from .embedded_model import EmbeddedModelField
from .json import register_json_field
from .objectid import ObjectIdField

__all__ = [
    "register_fields",
    "ArrayField",
    "EmbeddedModelField",
    "ObjectIdAutoField",
    "ObjectIdField",
]


def register_fields():
    register_duration_field()
    register_json_field()
