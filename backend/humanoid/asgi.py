"""
ASGI config for humanoid project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'humanoid.settings')

application = get_asgi_application()
