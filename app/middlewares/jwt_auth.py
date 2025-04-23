from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from app.config import settings

class JWTValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing or invalid Authorization header"})

        token = auth_header.split(" ", 1)[1]
        try:
            jwt.decode(
                token,
                settings.KEYCLOAK_PUBLIC_KEY,
                algorithms=["RS256"],
                issuer=settings.KEYCLOAK_ISSUER,
                audience="account",
                options={"verify_exp": False}
            )
        except JWTError as e:
            return JSONResponse(status_code=401, content={"detail": f"Token inválido: {str(e)}"})

        # Si todo va bien, sigue con la request
        return await call_next(request)
