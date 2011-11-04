"""
Convenience module for access of application-specific settings, which
enforces default settings when the main settings module does not contain
the appropriate settings.
"""
from django.conf import settings

STANDALONE              = getattr(settings, 'FORUM_STANDALONE',              False)
DEFAULT_POSTS_PER_PAGE  = getattr(settings, 'FORUM_DEFAULT_POSTS_PER_PAGE',  20)
DEFAULT_TOPICS_PER_PAGE = getattr(settings, 'FORUM_DEFAULT_TOPICS_PER_PAGE', 30)
POST_FORMATTER          = getattr(settings, 'FORUM_POST_FORMATTER',          'forum.formatters.PostFormatter')
MAX_AVATAR_FILESIZE     = getattr(settings, 'FORUM_MAX_AVATAR_FILESIZE',     512 * 1024)
ALLOWED_AVATAR_FORMATS  = getattr(settings, 'FORUM_ALLOWED_AVATAR_FORMATS',  ('GIF', 'JPEG', 'PNG'))
MAX_AVATAR_DIMENSIONS   = getattr(settings, 'FORUM_MAX_AVATAR_DIMENSIONS',   (64, 64))
FORCE_AVATAR_DIMENSIONS = getattr(settings, 'FORUM_FORCE_AVATAR_DIMENSIONS', True)

EMOTICONS = getattr(settings, 'FORUM_EMOTICONS', {
        ':angry:':    'angry.gif',
        ':blink:':    'blink.gif',
        ':D':         'grin.gif',
        ':huh:':      'huh.gif',
        ':lol:':      'lol.gif',
        ':o':         'ohmy.gif',
        ':ph34r:':    'ph34r.gif',
        ':rolleyes:': 'rolleyes.gif',
        ':(':         'sad.gif',
        ':)':         'smile.gif',
        ':p':         'tongue.gif',
        ':unsure:':   'unsure.gif',
        ':wacko:':    'wacko.gif',
        ';)':         'wink.gif',
        ':wub:':      'wub.gif',
    })

USE_REDIS  = getattr(settings, 'FORUM_USE_REDIS',  False)
REDIS_HOST = getattr(settings, 'FORUM_REDIS_HOST', 'localhost')
REDIS_PORT = getattr(settings, 'FORUM_REDIS_PORT', 6379)
REDIS_DB   = getattr(settings, 'FORUM_REDIS_DB',   0)

USE_NODEJS  = getattr(settings, 'FORUM_USE_NODEJS', False)
