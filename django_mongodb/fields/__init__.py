from .auto import MongoAutoField
from .duration import register_duration_field
from .json import register_json_field

__all__ = ["register_fields", "MongoAutoField"]


def register_fields():
    register_duration_field()
    register_json_field()
