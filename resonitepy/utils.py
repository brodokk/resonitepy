"""
This module define some generic function use at multiple
places in the package.
"""

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