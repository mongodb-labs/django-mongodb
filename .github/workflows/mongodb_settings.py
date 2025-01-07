DATABASES = {
    "default": {
        "ENGINE": "django_mongodb_backend",
        "NAME": "djangotests",
    },
    "other": {
        "ENGINE": "django_mongodb_backend",
        "NAME": "djangotests-other",
    },
}
DEFAULT_AUTO_FIELD = "django_mongodb_backend.fields.ObjectIdAutoField"
PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)
SECRET_KEY = "django_tests_secret_key"
USE_TZ = False
