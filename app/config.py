import os


class Config:
    # No fallback secret in production: a committed default would let anyone
    # reading this repo forge a signed session cookie, including admin.
    SECRET_KEY = os.environ["SECRET_KEY"] if not os.getenv("FLASK_DEBUG") \
        else os.getenv("SECRET_KEY", "dev-only-insecure-do-not-use-in-prod")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///taksunusa.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "true").lower() != "false"

    # Must stay at or below nginx's client_max_body_size, or the upload is
    # rejected by the proxy before Flask can explain why.
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "app/static/uploads")

    SITE_URL = os.getenv("SITE_URL", "https://taksunusaspa.com").rstrip("/")
    LANGUAGES = ["en", "id"]
    DEFAULT_LANG = os.getenv("DEFAULT_LANG", "en")
    CURRENCY = "IDR"
    WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "6282339566156")
