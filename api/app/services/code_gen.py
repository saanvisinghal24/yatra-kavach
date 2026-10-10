import secrets

ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"

def generate_group_code(length: int = 6) -> str:
    """Generate a high-entropy group code using the unambiguous alphabet."""
    return "".join(secrets.choice(ALPHABET) for _ in range(length))

def make_pass_token(code: str) -> str:
    """Format the pass token string for QR generation."""
    return f"YK1:{code}"
