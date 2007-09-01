import datetime

import pytz
from django import template
from django.conf import settings
from django.utils import dateformat

from forum import auth
from forum.models import ForumProfile

register = template.Library()

##################
# Inclusion Tags #
##################

@register.inclusion_tag('forum/pagination.html', takes_context=True)
def paginator(context, what, adjacent_pages=3):
    """
    Adds pagination context variables for use in displaying first,
    adjacent and last page links, in addition to those created by the
    ``object_list`` generic view.
    """
    page_numbers = [n for n in \
                    range(context['page'] - adjacent_pages,
                          context['page'] + adjacent_pages + 1) \
                    if n > 0 and n <= context['pages']]
    show_first = 1 not in page_numbers
    show_last = context['pages'] not in page_numbers
    return {
        'what': what,
        'hits': context['hits'],
        'results_per_page': context['results_per_page'],
        'page': context['page'],
        'pages': context['pages'],
        'page_numbers': page_numbers,
        'next': context['next'],
        'previous': context['previous'],
        'has_next': context['has_next'],
        'has_previous': context['has_previous'],
        'show_first': show_first,
        'show_first_divider': show_first and page_numbers[0] != 2,
        'show_last': show_last,
        'show_last_divider': show_last and page_numbers[-1] != context['pages'] - 1,
    }

###########
# Filters #
###########

@register.filter
def can_edit_post(user, post):
    return user.is_authenticated() and \
           auth.user_can_edit_post(user, post)

@register.filter
def can_edit_user_profile(user, user_to_edit):
    return user.is_authenticated() and \
           auth.user_can_edit_user_profile(user, user_to_edit)

@register.filter
def is_moderator(user):
    return user.is_authenticated() and \
           ForumProfile.objects.get_for_user(user).is_moderator()

@register.filter
def user_tz(dt, user):
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

@register.filter
def post_time(posted_at, user=None):
    """
    Formats a Post time.

    If a User is given and they have a timezone set in their profile,
    the time will be translated to their local time.
    """
    if user:
        posted_at = user_tz(posted_at, user)
        today = user_tz(datetime.datetime.now(), user).date()
    else:
        today = datetime.date.today()
    post_date = posted_at.date()
    if post_date == today:
        date = u'Today'
    elif post_date == today - datetime.timedelta(days=1):
        date = u'Yesterday'
    else:
        date = u'on %s' % dateformat.format(post_date, 'M jS Y')
    return u'%s at %s' % (date,
                          dateformat.time_format(posted_at.time(), 'H:i A'))

@register.filter
def joined_date(date):
    return dateformat.format(date, 'M jS Y')
