import jwt
from typing import Optional
from uuid import UUID
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from civix_api.config import settings

oauth2_scheme = HTTPBearer(auto_error=False)

def get_user_id_from_token(token: str) -> UUID:
    try:
        payload = jwt.decode(
            token,
            settings.civix_jwt_secret,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]}
        )
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing 'sub' claim in JWT.",
            )
        try:
            return UUID(str(sub))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 'sub' claim format. Must be a valid UUID.",
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except jwt.exceptions.MissingRequiredClaimError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing '{e.claim}' claim in JWT.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )
