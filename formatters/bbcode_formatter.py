"""
Post formatting module which uses BBCode syntax to format posts.
"""
import re

from django.utils.html import escape
from postmarkup import render_bbcode

def format_post_body(body):
    """
    Formats the given raw post body as HTML.
    """
    return render_bbcode(body).strip()

def quote_post(post):
    """
    Returns a raw post body which quotes the given Post.
    """
    return u'[quote]%s[/quote]' % escape(post.body)
