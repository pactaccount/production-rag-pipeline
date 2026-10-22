"""Public error messages for upstream provider failures."""

from fastapi import HTTPException


def provider_http_error(exc: Exception) -> HTTPException:
    message = str(exc).lower()
    if "429" in message or "quota exceeded" in message or "rate limit" in message:
        return HTTPException(
            status_code=429,
            detail="The demo provider is temporarily rate limited. Please retry in about a minute.",
            headers={"Retry-After": "60"},
        )
    return HTTPException(
        status_code=502,
        detail="The document request could not be completed. Please retry later.",
    )
