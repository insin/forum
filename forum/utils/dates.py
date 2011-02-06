import datetime

from django.conf import settings
from django.utils import dateformat

import pytz
from forum.models import ForumProfile

def user_timezone(dt, user):
    """
    Converts the given datetime to the given User's timezone, if they
    have one set in their forum profile.

    Adapted from http://www.djangosnippets.org/snippets/183/
    """
    tz = settings.TIME_ZONE
    if user.is_authenticated():
        profile = ForumProfile.objects.get_for_user(user)
        if profile.timezone:
            tz = profile.timezone
    try:
        result = dt.astimezone(pytz.timezone(tz))
    except ValueError:
        # The datetime was stored without timezone info, so use the
        # timezone configured in settings.
        result = dt.replace(tzinfo=pytz.timezone(settings.TIME_ZONE)) \
                    .astimezone(pytz.timezone(tz))
    return result

def format_datetime(dt, user, date_format, time_format, separator=' '):
    """
    Formats a datetime, using ``'Today'`` or ``'Yesterday'`` instead of
    the given date format when appropriate.

    If a User is given and they have a timezone set in their profile,
    the datetime will be translated to their local time.
    """
    if user:
        dt = user_timezone(dt, user)
        today = user_timezone(datetime.datetime.now(), user).date()
    else:
        today = datetime.date.today()
    date_part = dt.date()
    delta = date_part - today
    if delta.days == 0:
        date = u'Today'
    elif delta.days == -1:
        date = u'Yesterday'
    else:
        date = dateformat.format(dt, date_format)
    return u'%s%s%s' % (date, separator,
                        dateformat.time_format(dt.time(), time_format))
