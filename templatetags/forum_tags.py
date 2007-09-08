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

def format_datetime(dt, user, date_format, time_format, separator=' '):
    """
    Formats a datetime, using ``'Today'`` or ``'Yesterday'`` instead of
    the given date format when appropriate.

    If a User is given and they have a timezone set in their profile,
    the datetime will be translated to their local time.
    """
    if user:
        dt = user_tz(dt, user)
        today = user_tz(datetime.datetime.now(), user).date()
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

@register.filter
def forum_datetime(st, user=None):
    """
    Formats a general datetime.
    """
    return format_datetime(st, user, 'M jS Y', 'H:i A', ', ')

@register.filter
def post_time(posted_at, user=None):
    """
    Formats a Post time.
    """
    return format_datetime(posted_at, user, r'\o\n M jS Y', r'\a\t H:i A')

@register.filter
def joined_date(date):
    return dateformat.format(date, 'M jS Y')

@register.filter
def topic_pagination(topic, posts_per_page):
    """
    Creates topic listing page links for the given topic, when the given
    number of posts are displayed on each page.

    Topics with between 2 and 5 pages will have page links displayed for
    each page.

    Topics with more than 5 pages will have page links displayed for the
    first page and the last 3 pages.
    """
    hits = (topic.post_count - 1)
    if hits < 1:
        hits = 0
    pages = hits // posts_per_page + 1
    if pages < 2:
        return u''
    else:
        page_link = u'<a class="pagelink" href="%s?page=%%s">%%s</a>' % \
            topic.get_absolute_url()
        if pages < 6:
            return u' '.join([page_link % (page, page) \
                              for page in xrange(1, pages + 1)])
        else:
            return u' '.join([page_link % (1 ,1), u'&hellip;'] + \
                [page_link % (page, page) \
                 for page in xrange(pages - 2, pages + 1)])
