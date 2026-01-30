from secrets import choice
from string import ascii_uppercase, digits

def random_string(n: int) -> str:
    alphabet = ascii_uppercase + digits
    return ''.join(choice(alphabet) for _ in range(n))

print(random_string(60))
