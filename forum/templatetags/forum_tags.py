from math import ceil
from urlparse import urljoin

from django import template
from django.conf import settings
from django.template import loader
from django.utils import dateformat
from django.utils.safestring import mark_safe

from forum import auth
from forum.formatters import post_formatter
from forum.models import Topic, Post
from forum.utils.dates import format_datetime

register = template.Library()

#################
# Template Tags #
#################

@register.simple_tag
def add_last_read_times(topics, user):
    """
    Adds last read times to the given Topics for the given User.
    """
    Topic.objects.add_last_read_times(topics, user)
    return mark_safe(u'')

@register.simple_tag
def add_view_counts(topics):
    """
    Adds view count details to the given Topics.
    """
    Topic.objects.add_view_counts(topics)
    return mark_safe(u'')

@register.simple_tag
def add_topic_view_counts(posts):
    """
    Adds view count details to the given Topics.
    """
    Post.objects.add_topic_view_counts(posts)
    return mark_safe(u'')

@register.simple_tag
def emoticon_help():
    """
    Creates a help section for the currently configured set of emoticons.
    """
    return mark_safe(loader.render_to_string('forum/help/emoticons.html', {
        'emoticons': post_formatter.emoticon_processor.emoticons
    }))

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
def partition(l, n):
    """
    Partitions a list into lists of size ``n``.

    From http://www.djangosnippets.org/snippets/6/
    """
    try:
        n = int(n)
        thelist = list(l)
    except (ValueError, TypeError):
        return [l]
    lists = [list() for i in range(int(ceil(len(l) / float(n))))]
    for i, item in enumerate(l):
        lists[i/n].append(item)
    return lists

##########################
# Authentication Filters #
##########################

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

#######################
# Date / Time Filters #
#######################

@register.filter
def forum_datetime(st, user=None):
    """
    Formats a general datetime.
    """
    return mark_safe(format_datetime(st, user, 'M jS Y', 'H:i A', ', '))

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

########################
# Topic / Post Filters #
########################

@register.filter
def is_first_post(post):
    """
    Determines if the given post is the first post in a topic.
    """
    return post.num_in_topic == 1 and not post.meta

@register.filter
def topic_status_image(topic):
    """
    Returns HTML for an image representing a topic's status.
    """
    if has_new_posts(topic):
        src = u'forum/img/new_posts.gif'
        description = u'New Posts'
    else:
        src = u'forum/img/no_new_posts.gif'
        description = u'No New Posts'
    return mark_safe(u'<img src="%s" alt="%s" title="%s">' % (
        urljoin(settings.STATIC_URL, src), description, description))

@register.filter
def has_new_posts(topic):
    """
    Returns ``True`` if the given topic has new posts for the current
    User, based on the presence and value of a ``last_read`` attribute.
    """
    if hasattr(topic, 'last_read'):
        return topic.last_read is None or topic.last_post_at > topic.last_read
    else:
        return False

@register.filter
def topic_pagination(topic, posts_per_page):
    """
    Creates topic listing page links for the given topic, with the given
    number of posts per page.

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
