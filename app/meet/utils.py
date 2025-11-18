import time
import random
import hashlib
from django.conf import settings
from agora_token_builder import RtcTokenBuilder


AGORA_ROLE = {"publisher": 1, "subscriber": 2}


def generate_meet_id() -> str:
    def random_chars(length: int) -> str:
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return "".join(random.choice(chars) for _ in range(length))

    part1 = random_chars(3)
    part2 = random_chars(4)
    part3 = random_chars(3)
    return f"{part1}-{part2}-{part3}"


def uuid_to_agora_uid(user_uuid: str) -> int:
    """Convert UUID string to Agora-compatible UID"""
    hash_object = hashlib.md5(user_uuid.encode())
    hash_hex = hash_object.hexdigest()

    return int(hash_hex[:8], 16) % (2**32 - 1)


def generate_meet_token(channel_name: str, user_id: str, expires_in: int = 3600) -> str:
    """Generate an Agora Meet token."""
    app_id = settings.AGORA_APP_ID
    app_certificate = settings.AGORA_APP_CERTIFICATE
    user_id = uuid_to_agora_uid(str(user_id)) if user_id else 0

    if not app_certificate:
        raise ValueError("AGORA_APP_CERTIFICATE environment variable is required")

    expire_time = int(time.time()) + expires_in

    privilege_expire = expire_time

    # Build token with voice and video privileges
    token = RtcTokenBuilder.buildTokenWithUid(
        appId=app_id,
        appCertificate=app_certificate,
        channelName=channel_name,
        uid=0,
        role=AGORA_ROLE["publisher"],
        privilegeExpiredTs=privilege_expire,
    )

    return token
