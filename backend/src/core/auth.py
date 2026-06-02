import jwt
import httpx
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from uuid import UUID
from src.config import settings


security_scheme = HTTPBearer()


class AuthenticatedUser(BaseModel):
    id: UUID
    email: EmailStr


class JWTValidator:
    def __init__(self):
        self.jwks_url = settings.AUTH_JWKS_URL
        self.jwks_cache = None

    async def _fetch_jwks(self) -> dict:
        if self.jwks_cache:
            return self.jwks_cache
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.jwks_url)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch authentication public keys."
                )
            self.jwks_cache = response.json()
            return self.jwks_cache

    async def validate_token(self, credentials: HTTPAuthorizationCredentials = Security(security_scheme)) -> AuthenticatedUser:
        token = credentials.credentials
        try:
            unverified_headers = jwt.get_unverified_header(token)
            kid = unverified_headers.get("kid")
            
            jwks = await self._fetch_jwks()
            public_key = None
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                    break
                    
            if not public_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token signing key identifier."
                )

            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=settings.AUTH_AUDIENCE,
                issuer=settings.AUTH_ISSUER
            )
            
            return AuthenticatedUser(
                id=payload["sub"], 
                email=payload["email"]
            )

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired."
            )
        except (jwt.InvalidTokenError, KeyError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials."
            )


auth_validator = JWTValidator()
