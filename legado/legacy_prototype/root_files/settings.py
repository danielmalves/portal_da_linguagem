LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "/portal"

INSTALLED_APPS = [
    # Django defaults...
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Seus apps
    "apps.accounts",
    "apps.billing",
    "apps.files",
    "apps.orders",
    "apps.payments",
    "apps.quotes",
    "apps.staffing",
    "apps.core",
]
