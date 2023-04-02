"""
This module define some generic function use at multiple
places in the package.
"""

from enum import Enum
from .classes import OwnerType

def nested_asdict_factory(data):
    """Factory for convert dataclasses as dict.

    Can be use when a dataclass have an Enum.
    Example:

    ```
    dataclasses.asdict(
        <dataclass>,
        dict_factory=nested_asdict_factory,
    )
    ```
    """

    def convert_value(obj):
        if isinstance(obj, Enum):
            return obj.value
        return obj

    return dict((k, convert_value(v)) for k, v in data)

def getOwnerType(ownerId: str) -> str:
    if ownerId.startswith('U-'):
        return OwnerType.USER
    elif ownerId.startswith('G-'):
        return OwnerType.GROUP
    elif ownerId.startswith('M-'):
        return OwnerType.MACHINE
    else:
        return OwnerType.INVALID