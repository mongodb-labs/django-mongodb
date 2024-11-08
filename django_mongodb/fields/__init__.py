from .auto import ObjectIdAutoField
from .duration import register_duration_field
from .embedded_model import EmbeddedModelField, register_embedded_model_field
from .json import register_json_field
from .objectid import ObjectIdField

__all__ = ["register_fields", "EmbeddedModelField", "ObjectIdAutoField", "ObjectIdField"]


def register_fields():
    register_duration_field()
    register_embedded_model_field()
    register_json_field()
