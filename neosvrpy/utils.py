"""
This module define some generic function use at multiple
places in the package.
"""

from enum import Enum

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
