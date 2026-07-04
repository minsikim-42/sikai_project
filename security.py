from fastapi import Header, HTTPException

from config import SERVER_MODE, API_KEY


def verify_api_key(authorization: str = Header(None)):
    # Tailscale 모드면 검사 안 함
    if SERVER_MODE == "tailscale":
        return

    # Public 모드면 검사
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key"
        )