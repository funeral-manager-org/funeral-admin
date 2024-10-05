import socket
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, ValidationError
from dotenv import load_dotenv
import os

load_dotenv(".env.development")


class CloudFlareSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.development", env_file_encoding="utf-8", extra="ignore")
    EMAIL: str = Field(default=os.environ.get("CLOUDFLARE_EMAIL"))
    TOKEN: str = Field(default=os.environ.get("CLOUDFLARE_TOKEN"))
    X_CLIENT_SECRET_TOKEN: str = Field(default=os.environ.get("CLIENT_SECRET"))


class RedisSettings(BaseSettings):
    """
    # NOTE: maybe should use Internal pydantic Settings
    # TODO: please finalize Redis Cache Settings """
    model_config = SettingsConfigDict(env_file=".env.development", env_file_encoding="utf-8", extra="ignore")
    CACHE_TYPE: str = Field(default=os.environ.get("CACHE_TYPE"))
    CACHE_REDIS_HOST: str = Field(default=os.environ.get("CACHE_REDIS_HOST"))
    CACHE_REDIS_PORT: int = Field(default=os.environ.get("CACHE_REDIS_PORT"))
    REDIS_PASSWORD: str = Field(default=os.environ.get("REDIS_PASSWORD"))
    REDIS_USERNAME: str = Field(default=os.environ.get("REDIS_USERNAME"))
    CACHE_REDIS_DB: str = Field(default=os.environ.get("CACHE_REDIS_DB"))
    CACHE_REDIS_URL: str = Field(default=os.environ.get("MICROSOFT_REDIS_URL"))
    CACHE_DEFAULT_TIMEOUT: int = Field(default=60 * 60 * 6)


class CacheSettings(BaseSettings):
    """Google Mem Cache Settings"""
    # NOTE: TO USE Flask_cache with redis set Cache type to redis and setup CACHE_REDIS_URL
    model_config = SettingsConfigDict(env_file=".env.development", env_file_encoding="utf-8", extra="ignore")
    CACHE_TYPE: str = Field(default=os.environ.get("CACHE_TYPE"))
    CACHE_DEFAULT_TIMEOUT: int = Field(default=60 * 60 * 3)
    MEM_CACHE_SERVER_URI: str = Field(default="")
    CACHE_REDIS_URL: str = Field(default=os.environ.get("CACHE_REDIS_URL"))
    MAX_CACHE_SIZE: int = Field(default=1024)
    USE_CLOUDFLARE_CACHE: bool = Field(default=True)


class MySQLSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.development", env_file_encoding="utf-8", extra="ignore")
    PRODUCTION_DB: str = Field(default=os.environ.get("PRODUCTION_SQL_DB"))
    DEVELOPMENT_DB: str = Field(default=os.environ.get("DEV_SQL_DB"))


class Logging(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.development", env_file_encoding="utf-8", extra="ignore")
    filename: str = Field(default="fm.logs")


class PayPalSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.development", env_file_encoding="utf-8", extra="ignore")
    CLIENT_ID: str = Field(default=os.environ.get("PAYPAL_API_CLIENT_ID"))
    SECRET_KEY: str = Field(default=os.environ.get("PAYPAL_SECRET_KEY"))


class BrainTreeSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.development", env_file_encoding="utf-8", extra="ignore")
    MERCHANT_ID: str = Field(default=os.environ.get('BRAIN_TREE_MERCHANT_ID'))
    PUBLIC_KEY: str = Field(default=os.environ.get('BRAIN_TREE_PUBLIC_KEY'))
    PRIVATE_KEY: str = Field(default=os.environ.get('BRAIN_TREE_PRIVATE_KEY'))


class TwilioSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.development", env_file_encoding="utf-8", extra="ignore")
    TWILIO_SID: str = Field(default=os.environ.get('TWILIO_ACCOUNT_SID'))
    TWILIO_TOKEN: str = Field(default=os.environ.get('TWILIO_AUTH_TOKEN'))
    TWILIO_NUMBER: str = Field(default=os.environ.get('TWILIO_NUMBER'))


class VonageSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.development", env_file_encoding="utf-8", extra="ignore")
    API_KEY: str = Field(default=os.environ.get('VONAGE_API_KEY'))
    SECRET: str = Field(default=os.environ.get('VONAGE_SECRET'))


class ResendSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.development", env_file_encoding="utf-8", extra="ignore")
    API_KEY: str = Field(default=os.environ.get("RESEND_API_KEY"))
    from_: str = Field(default="norespond@funeral-manager.org")


class EmailSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.development", env_file_encoding="utf-8", extra="ignore")
    RESEND: ResendSettings = ResendSettings()


class PayfastSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.development", env_file_encoding="utf-8", extra="ignore")
    MERCHANT_ID: str = Field(default=os.environ.get("PAYFAST_MERCHANT_ID"))
    MERCHANT_KEY: str = Field(default=os.environ.get("PAYFAST_MERCHANT_KEY"))
    SANDBOX_MERCHANT_ID: str = Field(default=os.environ.get("PAYFAST_SANDBOX_MERCHANT_ID"))
    SANDBOX_MERCHANT_KEY: str = Field(default=os.environ.get("PAYFAST_SANDBOX_MERCHANT_KEY"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.development", env_file_encoding="utf-8", extra="ignore")
    APP_NAME: str = Field(default='Last Base')
    LOGO_URL: str = Field(default="https://last-shelter.vip/static/images/custom/logo.png")
    SECRET_KEY: str = Field(default=os.environ.get("SECRET_KEY"))
    CLIENT_SECRET: str = Field(default=os.environ.get("CLIENT_SECRET"))
    MYSQL_SETTINGS: MySQLSettings = MySQLSettings()
    CLOUDFLARE_SETTINGS: CloudFlareSettings = CloudFlareSettings()
    EMAIL_SETTINGS: EmailSettings = EmailSettings()
    DEVELOPMENT_SERVER_NAME: str = Field(default="mothetho")
    LOGGING: Logging = Logging()
    HOST_ADDRESSES: str = Field(default=os.environ.get('HOST_ADDRESSES'))
    PAYFAST: PayfastSettings = PayfastSettings()
    FLUTTERWAVE_SECRET_ID: str = Field(default=os.environ.get("FLUTTERWAVE_SECRET_ID"))
    FLUTTERWAVE_FLW_SECRET_KEY: str = Field(default=os.environ.get("FLUTTERWAVE_SECRET_KEY"))
    FLUTTERWAVE_HASH: str = Field(default=os.environ.get("FLUTTERWAVE_HASH"))
    PAYPAL_SETTINGS: PayPalSettings = PayPalSettings()
    ADMIN_EMAIL: str = "admin@last-shelter.vip"
    AUTH_CODE: str = "sdasdasdas"
    TWILIO: TwilioSettings = TwilioSettings()
    VONAGE: VonageSettings = VonageSettings()
    SENTRY_DSN: str = Field(default=os.environ.get("SENTRY_DSN"))
    CACHE_SETTINGS: CacheSettings = CacheSettings()
    REDIS_CACHE: RedisSettings = RedisSettings()
    DEBUG: bool = Field(default=True)
    DEMO_ACCOUNT: str = "demo@funeral-manager.org"


def config_instance() -> Settings:
    """
    :return:
    """
    try:
        return Settings()
    except ValidationError as e:
        print(str(e))


def is_development():
    return socket.gethostname() == config_instance().DEVELOPMENT_SERVER_NAME
