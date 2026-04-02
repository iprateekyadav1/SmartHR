"""
config.py — Central configuration for SmartHR
All environment-specific settings live here so changing
deployment (dev → prod) only requires editing this one file.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # ── Database ──────────────────────────────────────────────────────────────
    # SQLite file stored inside project folder.
    # SQLAlchemy uses this URI to know which DB engine to talk to.
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'smarthr.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False   # Saves memory; we don't need the overhead

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "smarthr-dev-secret-2024")

    # ── Session ───────────────────────────────────────────────────────────────
    SESSION_COOKIE_SAMESITE = "Lax"   # prevents CSRF in modern browsers
    SESSION_COOKIE_HTTPONLY = True    # JS cannot read the session cookie
    PERMANENT_SESSION_LIFETIME = 3600 # 1 hour session timeout

    # ── File Uploads (resumes) ────────────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024   # 5 MB limit


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


# Active config selected here — swap to ProductionConfig before deployment
active_config = DevelopmentConfig
