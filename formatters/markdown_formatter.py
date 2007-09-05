"""
Post formatting module which uses Markdown syntax to format posts.
"""
import re

from django.conf import settings
from django.utils.html import escape

from markdown import Markdown

quote_post_re = re.compile(r'^', re.MULTILINE)

def format_post_body(body):
    """
    Formats the given raw post body as HTML.
    """
    return Markdown(body, extensions=['emoticons'], extension_configs={
        'emoticons': [('BASE_URL', '%simg/emoticons/' % settings.MEDIA_URL)],
    }, safe_mode=True).toString().strip()

def quote_post(post):
    """
    Returns a raw post body which quotes the given Post.
    """
    return u'**%s** [wrote](%s "View quoted post"):\n\n%s\n\n' % (
        escape(post.user.username),
        post.get_absolute_url(),
        quote_post_re.sub('> ', post.body),
    )
