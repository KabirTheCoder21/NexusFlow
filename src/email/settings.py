from pydantic_settings import BaseSettings, SettingsConfigDict
class EmailSettings(BaseSettings):

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str

    MAIL_SERVER: str
    MAIL_PORT: int

    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    FRONTEND_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",   # Ignore unrelated env vars
    )


email_settings = EmailSettings()