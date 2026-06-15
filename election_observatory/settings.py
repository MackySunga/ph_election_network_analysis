from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-election-network-observatory-key")
DEBUG = os.getenv("DJANGO_DEBUG", "1").lower() not in {"0", "false", "no"}
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,0.0.0.0,*").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "election_observatory.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "dashboard" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    }
]
WSGI_APPLICATION = "election_observatory.wsgi.application"

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "dashboard" / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# The dashboard reads final CSV/HTML/PNG outputs produced by the notebooks.
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs"
RAW_DATA_DIR = BASE_DIR / "data" / "raw"

# Allow embedded local artifact iframes.
X_FRAME_OPTIONS = "SAMEORIGIN"
