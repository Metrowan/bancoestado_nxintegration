from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv("../../.env") #Cambiar esto por ".env" cuando se esté en desarrollo

class Settings(BaseSettings):
    KEYCLOAK_ISSUER: str = os.getenv("KEYCLOAK_ISSUER", "")
    KEYCLOAK_CLIENT_ID: str = os.getenv("KEYCLOAK_CLIENT_ID", "")
    KEYCLOAK_CLIENT_SECRET: str = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
    KEYCLOAK_PUBLIC_KEY: str = os.getenv("KEYCLOAK_PUBLIC_KEY", "")
    SPLYNX_CONNECTION: str = os.getenv("SPLYNX_CONNECTION", "")
    BANCOESTADO_CONNECTION: str = os.getenv("BANCOESTADO_CONNECTION", "")
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "")
    RABBITMQ_ADMIN: str = os.getenv("RABBITMQ_ADMIN", "")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "")
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

settings = Settings()
