import datetime
from urlparse import urljoin

from django import template
from django.conf import settings
from django.utils import dateformat
from django.utils.safestring import mark_safe

import pytz
from forum import auth
from forum.models import ForumProfile, TopicTracker

register = template.Library()

#################
# Template Tags #
#################

@register.simple_tag
def add_last_read_times(topics, user):
    """
    Adds last read details to the given topics for the given user.
    """
    TopicTracker.objects.add_last_read_to_topics(topics, user)
    return mark_safe(u'')

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
def can_edit_topic(user, topic):
    return user.is_authenticated() and \
           auth.user_can_edit_topic(user, topic)

@register.filter
def can_edit_user_profile(user, user_to_edit):
    return user.is_authenticated() and \
           auth.user_can_edit_user_profile(user, user_to_edit)

@register.filter
def is_admin(user):
    """
    Returns ``True`` if the given user has admin permissions,
    ``False`` otherwise.
    """
    return user.is_authenticated() and \
           auth.is_admin(user)

@register.filter
def is_moderator(user):
    """
    Returns ``True`` if the given user has moderation permissions,
    ``False`` otherwise.
    """
    return user.is_authenticated() and \
           auth.is_moderator(user)

@register.filter
def can_see_post_actions(user, topic):
    """
    Returns ``True`` if the given User should be able to see the post
    action list for posts in the given topic, ``False`` otherwise.

    This function is used as part of ensuring that moderators have
    unrestricted access to locked Topics.
    """
    if user.is_authenticated():
        return not topic.locked or auth.is_moderator(user)
    else:
        return False

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
    return mark_safe(format_datetime(st, user, 'M jS Y', 'H:i A', ', '))

@register.filter
def is_first_post(post):
    """
    Determines if the given post is the first post in a topic.
    """
    return post.num_in_topic == 1 and not post.meta

@register.filter
def post_time(posted_at, user=None):
    """
    Formats a Post time.
    """
    return mark_safe(format_datetime(posted_at, user, r'\o\n M jS Y', r'\a\t H:i A'))

@register.filter
def joined_date(date):
    """
    Formats a joined date.
    """
    return mark_safe(dateformat.format(date, 'M jS Y'))

@register.filter
def topic_status_image(topic):
    """
    Returns HTML for an image representing a topic's status.
    """
    if has_new_posts(topic):
        src = u'img/new_posts.gif'
        description = u'New Posts'
    else:
        src = u'img/no_new_posts.gif'
        description = u'No New Posts'
    return mark_safe(u'<img src="%s" alt="%s" title="%s">' % (
        urljoin(settings.MEDIA_URL, src), description, description))

@register.filter
def has_new_posts(topic):
    """
    Returns ``True`` if the given topic has new posts, based on the
    presence and value of a ``last_read`` attribute.
    """
    last_read = getattr(topic, 'last_read', False)
    return last_read is not False and \
       (last_read is None or topic.last_post_at > last_read)

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
        html = u''
    else:
        page_link = u'<a class="pagelink" href="%s?page=%%s">%%s</a>' % \
            topic.get_absolute_url()
        if pages < 6:
            html = u' '.join([page_link % (page, page) \
                              for page in xrange(1, pages + 1)])
        else:
            html = u' '.join([page_link % (1 ,1), u'&hellip;'] + \
                [page_link % (page, page) \
                 for page in xrange(pages - 2, pages + 1)])
    return mark_safe(html)
