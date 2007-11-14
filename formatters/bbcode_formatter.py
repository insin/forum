"""
Post formatting module which uses BBCode syntax to format posts.
"""
import re

from django.conf import settings
from django.utils.html import escape

from forum.formatters import emoticons
from postmarkup import render_bbcode

QUICK_HELP_TEMPLATE = 'forum/help/bbcode_formatting_quick.html'
FULL_HELP_TEMPLATE = 'forum/help/bbcode_formatting.html'

emoticon_processor = emoticons.Emoticons(
    base_url='%sforum/img/emoticons/' % settings.MEDIA_URL)

def format_post_body(body):
    """
    Formats the given raw post body as HTML.
    """
    return emoticon_processor.replace(render_bbcode(body).strip())

def quote_post(post):
    """
    Returns a raw post body which quotes the given Post.
    """
    return u'[quote]%s[/quote]' % post.body
