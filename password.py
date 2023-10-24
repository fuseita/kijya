from string import ascii_uppercase, digits
from random import choices

def random_string(n: int) -> str:
    return ''.join(choices(ascii_uppercase + digits, k=n))

print(random_string(60))
