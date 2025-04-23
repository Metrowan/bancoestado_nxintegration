from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv("../../.env")

class Settings(BaseSettings):
    KEYCLOAK_ISSUER: str = os.getenv("KEYCLOAK_ISSUER", "")
    KEYCLOAK_CLIENT_ID: str = os.getenv("KEYCLOAK_CLIENT_ID", "")
    KEYCLOAK_CLIENT_SECRET: str = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
    KEYCLOAK_PUBLIC_KEY: str = os.getenv("KEYCLOAK_PUBLIC_KEY", "")
    SPLYNX_CONNECTION: str = os.getenv("SPLYNX_CONNECTION", "")
    BANCOESTADO_CONNECTION: str = os.getenv("BANCOESTADO_CONNECTION", "")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

settings = Settings()
