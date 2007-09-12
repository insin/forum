"""
Convenience module for access of application-specific settings, which
enforces default settings when the main settings module does not contain
the appropriate settings.
"""
from django.conf import settings

try:
    STANDALONE = settings.FORUM_STANDALONE
except AttributeError:
    STANDALONE = False

try:
    DEFAULT_POSTS_PER_PAGE = settings.FORUM_DEFAULT_POSTS_PER_PAGE
except AttributeError:
    DEFAULT_POSTS_PER_PAGE = 20

try:
    DEFAULT_TOPICS_PER_PAGE = settings.FORUM_DEFAULT_TOPICS_PER_PAGE
except AttributeError:
    DEFAULT_TOPICS_PER_PAGE = 30

try:
    POST_FORMATTING_MODULE = settings.FORUM_POST_FORMATTING_MODULE
except AttributeError:
    POST_FORMATTING_MODULE = 'forum.formatters.basic_formatter'

try:
    MAX_AVATAR_FILESIZE = settings.FORUM_MAX_AVATAR_FILESIZE
except AttributeError:
    MAX_AVATAR_FILESIZE = 512 * 1024 # 512 kB

try:
    ALLOWED_AVATAR_FORMATS = settings.FORUM_ALLOWED_AVATAR_FORMATS
except AttributeError:
    ALLOWED_AVATAR_FORMATS = ('GIF', 'JPEG', 'PNG')

try:
    MAX_AVATAR_DIMENSIONS = settings.FORUM_MAX_AVATAR_DIMENSIONS
except AttributeError:
    MAX_AVATAR_DIMENSIONS = (64, 64)

try:
    FORCE_AVATAR_DIMENSIONS = settings.FORUM_FORCE_AVATAR_DIMENSIONS
except AttributeError:
    FORCE_AVATAR_DIMENSIONS = True
