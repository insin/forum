"""
Convenience module for access of application-specific settings, which
enforces default settings when the main settings module does not contain
the appropriate settings.
"""
from django.conf import settings

try:
    DEFAULT_POSTS_PER_PAGE = settings.FORUM_DEFAULT_POSTS_PER_PAGE
except AttributeError:
    DEFAULT_POSTS_PER_PAGE = 20

try:
    DEFAULT_TOPICS_PER_PAGE = settings.FORUM_DEFAULT_TOPICS_PER_PAGE
except AttributeError:
    DEFAULT_TOPICS_PER_PAGE = 20

try:
    POST_FORMATTING_MODULE = settings.FORUM_POST_FORMATTING_MODULE
except AttributeError:
    POST_FORMATTING_MODULE = 'forum.formatters.basic_formatter'
