import random
import string


def generate() -> str:
    """
    direct reimpl of secretID.js from account.neosvr.com
    """
    length = 12
    valid_chars = string.ascii_letters + string.digits
    return "".join(random.choices(valid_chars, k=length))
