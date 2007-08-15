import datetime

from django import template
from django.utils import dateformat

register = template.Library()

##################
# Inclusion Tags #
##################

@register.inclusion_tag('forum/pagination.html', takes_context=True)
def paginator(context, what, adjacent_pages=2):
    """
    Adds pagination context variables for use in displaying first,
    adjacent and last page links, in addition to those created by the
    ``object_list`` generic view.
    """
    page_numbers = [n for n in \
                    range(context['page'] - adjacent_pages,
                          context['page'] + adjacent_pages + 1) \
                    if n > 0 and n <= context['pages']]
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
        'show_first': 1 not in page_numbers,
        'show_last': context['pages'] not in page_numbers,
    }

###########
# Filters #
###########

@register.filter
def post_time(posted_at):
    today = datetime.date.today()
    post_date = posted_at.date()
    if post_date == today:
        date = u'Today'
    elif post_date == today - datetime.timedelta(days=1):
        date = u'Yesterday'
    else:
        date = u'on %s' % dateformat.format(post_date, 'M dS Y')
    return u'%s at %s' % (date,
                          dateformat.time_format(posted_at.time(), 'H:i A'))

@register.filter
def joined_date(date):
    return dateformat.format(date, 'M dS Y')
