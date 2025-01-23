import os

from django_mongodb_backend import parse_uri

PARSED_URI = parse_uri(os.getenv("MONGODB_URI")) if os.getenv("MONGODB_URI") else {}

# Temporary fix for https://github.com/mongodb-labs/mongo-orchestration/issues/268
if "USER" in PARSED_URI and "PASSWORD" in PARSED_URI:
    PARSED_URI["OPTIONS"]["tls"] = True

DATABASES = {
    "default": {
        **PARSED_URI,
        "ENGINE": "django_mongodb_backend",
        "NAME": "djangotests",
    },
    "other": {
        **PARSED_URI,
        "ENGINE": "django_mongodb_backend",
        "NAME": "djangotests-other",
    },
}

DEFAULT_AUTO_FIELD = "django_mongodb_backend.fields.ObjectIdAutoField"
PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)
SECRET_KEY = "django_tests_secret_key"
USE_TZ = False
