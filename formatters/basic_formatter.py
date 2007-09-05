"""
Post formatting module which barely formats posts at all, but doesn't
have any external dependencies, which makes it a safe default.
"""
import re

from django.conf import settings
from django.utils.html import escape, linebreaks, urlize
from django.utils.text import normalize_newlines, wrap

from forum.formatters import emoticons

QUICK_HELP_TEMPLATE = 'forum/help/basic_formatting_quick.html'
FULL_HELP_TEMPLATE = 'forum/help/basic_formatting.html'

emoticon_processor = emoticons.Emoticons(
    base_url='%simg/emoticons/' % settings.MEDIA_URL)
quote_post_re = re.compile(r'^', re.MULTILINE)

def format_post_body(body):
    """
    Formats the given raw post body as HTML.
    """
    return emoticon_processor.replace(linebreaks(urlize(escape(body.strip()))))

def quote_post(post):
    """
    Returns a raw post body which quotes the given Post.
    """
    return u'%s wrote:\n\n%s\n\n' % (
        escape(post.user.username),
        quote_post_re.sub('> ', wrap(normalize_newlines(post.body), 80)),
    )
