import hmac
import hashlib
from app.config import get_settings

settings = get_settings()

def compute_checkpoint_hmac(checkpoint_id: int, qr_key_version: int, secret: str = None) -> str:
    """
    Compute 8-character hex HMAC-SHA256 for checkpoint.
    Format: hmac8 = HMAC-SHA256(secret, f"{checkpoint_id}|{qr_key_version}")[:8]
    """
    secret_key = (secret or settings.QR_HMAC_SECRET).encode("utf-8")
    message = f"{checkpoint_id}|{qr_key_version}".encode("utf-8")
    digest = hmac.new(secret_key, message, hashlib.sha256).hexdigest()
    return digest[:8]

def make_checkpoint_qr_payload(checkpoint_id: int, qr_key_version: int, secret: str = None) -> str:
    """Format: YK1:CP:<checkpoint_id>:<hmac8>"""
    hmac8 = compute_checkpoint_hmac(checkpoint_id, qr_key_version, secret)
    return f"YK1:CP:{checkpoint_id}:{hmac8}"

def verify_checkpoint_qr(raw_qr: str, qr_key_version: int, secret: str = None) -> tuple[bool, int, str]:
    """
    Parse and verify a checkpoint QR code string.
    Returns (is_valid, checkpoint_id, error_message).
    """
    parts = raw_qr.strip().split(":")
    if len(parts) != 4 or parts[0] != "YK1" or parts[1] != "CP":
        return False, 0, "Malformed checkpoint QR format. Expected 'YK1:CP:<id>:<hmac>'"

    try:
        checkpoint_id = int(parts[2])
    except ValueError:
        return False, 0, "Invalid checkpoint ID format."

    provided_hmac = parts[3].lower()
    expected_hmac = compute_checkpoint_hmac(checkpoint_id, qr_key_version, secret).lower()

    if not hmac.compare_digest(provided_hmac, expected_hmac):
        return False, checkpoint_id, "Checkpoint QR signature verification failed (possible forgery)."

    return True, checkpoint_id, ""
