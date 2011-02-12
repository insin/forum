import os
import sys

activate_this = 'C:/virtualenvs/forum/Scripts/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

os.environ['DJANGO_SETTINGS_MODULE'] = 'forum.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
