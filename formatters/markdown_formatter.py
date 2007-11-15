"""
Post formatting module which uses Markdown syntax to format posts.
"""
import re

from django.conf import settings
from django.utils.html import escape

from forum.formatters import emoticons
from markdown import Markdown

QUICK_HELP_TEMPLATE = 'forum/help/markdown_formatting_quick.html'
FULL_HELP_TEMPLATE = 'forum/help/markdown_formatting.html'

md = Markdown(safe_mode='escape')
emoticon_processor = emoticons.Emoticons(
    base_url='%sforum/img/emoticons/' % settings.MEDIA_URL)
quote_post_re = re.compile(r'^', re.MULTILINE)

def format_post_body(body, process_emoticons=True):
    """
    Formats the given raw post body as HTML.
    """
    md.reset()
    result = md.toString(body).strip()
    if process_emoticons:
        return emoticon_processor.process(result)
    return result

def quote_post(post):
    """
    Returns a raw post body which quotes the given Post.
    """
    return u'**%s** [wrote](%s "View quoted post"):\n\n%s\n\n' % (
        escape(post.user.username),
        post.get_absolute_url(),
        quote_post_re.sub('> ', post.body),
    )
