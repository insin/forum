"""
Convenience module for access of application-specific settings, which
enforces default settings when the main settings module does not contain
the appropriate settings.
"""
from django.conf import settings

STANDALONE              = getattr(settings, 'FORUM_STANDALONE',              False)
DEFAULT_POSTS_PER_PAGE  = getattr(settings, 'FORUM_DEFAULT_POSTS_PER_PAGE',  20)
DEFAULT_TOPICS_PER_PAGE = getattr(settings, 'FORUM_DEFAULT_TOPICS_PER_PAGE', 30)
POST_FORMATTING_MODULE  = getattr(settings, 'FORUM_POST_FORMATTING_MODULE',  'forum.formatters.basic_formatter')
MAX_AVATAR_FILESIZE     = getattr(settings, 'FORUM_MAX_AVATAR_FILESIZE',     512 * 1024)
ALLOWED_AVATAR_FORMATS  = getattr(settings, 'FORUM_ALLOWED_AVATAR_FORMATS',  ('GIF', 'JPEG', 'PNG'))
MAX_AVATAR_DIMENSIONS   = getattr(settings, 'FORUM_MAX_AVATAR_DIMENSIONS',   (64, 64))
FORCE_AVATAR_DIMENSIONS = getattr(settings, 'FORUM_FORCE_AVATAR_DIMENSIONS', True)
