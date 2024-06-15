from .auto import MongoAutoField
from .json import register_json_field

__all__ = ["register_fields", "MongoAutoField"]


def register_fields():
    register_json_field()
