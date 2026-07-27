from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Single source of truth for all backend configuration.
    Every module reads from here instead of touching os.environ directly,
    so Phase 2 (AI keys, collab service urls, etc.) only means adding
    fields here — nothing else changes.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Sketch2Code AI"
    ENV: str = "development"

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/sketch2code"

    JWT_SECRET_KEY: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    FRONTEND_ORIGIN: str = "http://localhost:5173"

    EMAIL_SENDER: str = "noreply@sketch2code.ai"
    EMAIL_BACKEND: str = "console"  # "console" | "smtp"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # --- AI vision provider (handwriting OCR for Feature 1, code-gen later) ---
    AI_PROVIDER: str = "gemini"  # "gemini" | "openai"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # --- Google OAuth client ID ---
    GOOGLE_CLIENT_ID: str = ""

    # --- Admin bootstrap ---
    # Comma-separated emails that are automatically granted admin access
    # on signup/login — a deliberately simple bootstrap mechanism (no
    # separate CLI/migration needed) rather than a fabricated "admin
    # since day one" flag with no real trigger behind it.
    ADMIN_EMAILS: str = ""

    @property
    def admin_emails_list(self) -> list[str]:
        return [e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()]


settings = Settings()
