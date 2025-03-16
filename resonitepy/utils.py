"""
This module define some generic function use at multiple
places in the package.
"""

import warnings
from functools import wraps

from .classes import OwnerType

def getOwnerType(ownerId: str) -> str:
    if ownerId.startswith('U-'):
        return OwnerType.USER
    elif ownerId.startswith('G-'):
        return OwnerType.GROUP
    elif ownerId.startswith('M-'):
        return OwnerType.MACHINE
    else:
        return OwnerType.INVALID

def deprecated_alias(new_func):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated; please use {new_func.__name__} instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator