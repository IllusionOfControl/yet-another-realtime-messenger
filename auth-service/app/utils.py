import random
import string


def generate_random_sequence(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_letters, k=length))
