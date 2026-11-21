import ctypes
from typing import Any


def serialize_page(value: object) -> Any:
    if isinstance(value, ctypes.Structure):
        return {name: serialize_page(getattr(value, name)) for name, *_ in value._fields_ if not name.startswith("_")}
    if isinstance(value, ctypes.Array):
        return [serialize_page(item) for item in value]
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value
