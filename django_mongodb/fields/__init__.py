from .auto import ObjectIdAutoField
from .duration import register_duration_field
from .embedded_model import EmbeddedModelField, ListField
from .json import register_json_field

__all__ = ["register_fields", "EmbeddedModelField", "ListField", "ObjectIdAutoField"]


def register_fields():
    register_duration_field()
    register_json_field()
