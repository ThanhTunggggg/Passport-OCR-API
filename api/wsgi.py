import os

from django.core.wsgi import get_wsgi_application
import corsheaders

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")

application = get_wsgi_application()
