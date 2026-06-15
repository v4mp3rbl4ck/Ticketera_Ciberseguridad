from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    APP_NAME: str = 'Ticketera Ciberseguridad y Networking'
    API_V1_PREFIX: str = '/api/v1'
    ENVIRONMENT: str = 'production'
    APP_TIMEZONE: str = 'America/Santiago'
    SECRET_KEY: str = 'change-me'
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Seguridad / hardening
    PASSWORD_MIN_LENGTH: int = 10
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBER: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    LOGIN_RATE_LIMIT_ATTEMPTS: int = 5
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 300

    # Cabeceras y modo de seguridad
    ENABLE_CSP: bool = True
    CONTENT_SECURITY_POLICY: str = "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self'"
    FORCE_HTTPS: bool = False
    SECURITY_STRICT_STARTUP: bool = False
    TRUSTED_HOSTS: str = 'localhost,127.0.0.1'
    AUDIT_DENIED_ACCESS: bool = True
    DATABASE_URL: str = 'sqlite:///./ticketera.db'
    AUTO_CREATE_TABLES: bool = True
    CORS_ORIGINS: str = 'http://localhost,http://localhost:5173,http://127.0.0.1:5173'

    BUSINESS_HOUR_START: str = '09:00'
    BUSINESS_HOUR_END: str = '18:00'
    BUSINESS_DAYS: str = '0,1,2,3,4'

    UPLOAD_DIR: str = '/app/uploads'
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_UPLOAD_EXTENSIONS: str = '.png,.jpg,.jpeg,.gif,.webp,.pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.log,.zip'
    BLOCKED_UPLOAD_EXTENSIONS: str = '.exe,.bat,.cmd,.ps1,.sh,.php,.jsp,.asp,.aspx,.js,.html,.htm,.svg,.msi,.dll,.scr,.jar,.vbs,.wsf'

    SMTP_ENABLED: bool = False
    SMTP_HOST: str = ''
    SMTP_PORT: int = 587
    SMTP_USER: str = ''
    SMTP_PASSWORD: str = ''
    SMTP_FROM: str = 'ticketera@empresa.cl'
    SMTP_TLS: bool = True

    REPORTS_ENABLED: bool = True
    BACKUP_RETENTION_DAYS: int = 30

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]

    @property
    def business_days_list(self) -> list[int]:
        return [int(day.strip()) for day in self.BUSINESS_DAYS.split(',') if day.strip()]

    @property
    def upload_path(self) -> Path:
        return Path(self.UPLOAD_DIR)

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def allowed_upload_extensions(self) -> set[str]:
        return {item.strip().lower() for item in self.ALLOWED_UPLOAD_EXTENSIONS.split(',') if item.strip()}

    @property
    def blocked_upload_extensions(self) -> set[str]:
        return {item.strip().lower() for item in self.BLOCKED_UPLOAD_EXTENSIONS.split(',') if item.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
