import re

from django.conf import settings
from django.utils.html import escape, linebreaks, urlize
from django.utils.text import normalize_newlines, wrap

from forum.formatters.emoticons import Emoticons

quote_post_re = re.compile(r'^', re.MULTILINE)

class PostFormatter(object):
    """
    Base post formatting object.

    If used as a post formatter itself, performs basic formatting,
    preserving linebreaks and converting URLs to links.
    """
    QUICK_HELP_TEMPLATE = 'forum/help/basic_formatting_quick.html'
    FULL_HELP_TEMPLATE  = 'forum/help/basic_formatting.html'

    def __init__(self, emoticons=None):
        if emoticons is None: emoticons = {}
        self.emoticon_processor = Emoticons(emoticons,
            base_url='%sforum/img/emoticons/' % settings.STATIC_URL)

    def format_post(self, body, process_emoticons=True):
        """
        Formats the given post body, replacing emoticon symbols with
        images if ``emoticons`` is ``True``.
        """
        if process_emoticons:
            return self.emoticon_processor.process(self.format_post_body(body))
        else:
            return self.format_post_body(body)

    def format_post_body(self, body):
        """
        Formats the given raw post body as HTML.
        """
        return linebreaks(urlize(escape(body.strip())))

    def quote_post(self, post):
        """
        Returns a raw post body which quotes the given Post.
        """
        return u'%s wrote:\n\n%s\n\n' % (
            escape(post.user.username),
            quote_post_re.sub('> ', wrap(normalize_newlines(post.body), 80)),
        )

class MarkdownFormatter(PostFormatter):
    """
    Post formatter which uses Markdown to format posts.
    """
    QUICK_HELP_TEMPLATE = 'forum/help/markdown_formatting_quick.html'
    FULL_HELP_TEMPLATE  = 'forum/help/markdown_formatting.html'

    def __init__(self, *args, **kwargs):
        super(MarkdownFormatter, self).__init__(*args, **kwargs)
        from markdown2 import Markdown
        self.md = Markdown(safe_mode='escape')

    def format_post_body(self, body):
        """
        Formats the given raw post body as HTML using Markdown
        formatting.
        """
        self.md.reset()
        return self.md.convert(body).strip()

    def quote_post(self, post):
        """
        Returns a raw post body which quotes the given Post using
        Markdown syntax.
        """
        return u'**%s** [wrote](%s "View quoted post"):\n\n%s\n\n' % (
            escape(post.user.username),
            post.get_absolute_url(),
            quote_post_re.sub('> ', post.body),
        )

class BBCodeFormatter(PostFormatter):
    """
    Post formatter which uses BBCode syntax to format posts.
    """
    QUICK_HELP_TEMPLATE = 'forum/help/bbcode_formatting_quick.html'
    FULL_HELP_TEMPLATE  = 'forum/help/bbcode_formatting.html'

    def __init__(self, *args, **kwargs):
        super(BBCodeFormatter, self).__init__(*args, **kwargs)
        import postmarkup
        self.pm = postmarkup.create()

    def format_post_body(self, body):
        """
        Formats the given raw post body as HTML using BBCode formatting.
        """
        return self.pm(body).strip()

    def quote_post(self, post):
        """
        Returns a raw post body which quotes the given Post using BBCode
        syntax.
        """
        return u'[quote="%s"]%s[/quote]' % (escape(post.user.username), post.body)

def get_post_formatter():
    """
    Creates a post formatting object as specified by current settings.
    """
    from django.core import exceptions
    from forum import app_settings
    try:
        dot = app_settings.POST_FORMATTER.rindex('.')
    except ValueError:
        raise exceptions.ImproperlyConfigured, '%s isn\'t a post formatting module' % app_settings.POST_FORMATTER
    modulename, classname = app_settings.POST_FORMATTER[:dot], app_settings.POST_FORMATTER[dot+1:]
    try:
        mod = __import__(modulename, {}, {}, [''])
    except ImportError, e:
        raise exceptions.ImproperlyConfigured, 'Error importing post formatting module %s: "%s"' % (modulename, e)
    try:
        formatter_class = getattr(mod, classname)
    except AttributeError:
        raise exceptions.ImproperlyConfigured, 'Post formatting module "%s" does not define a "%s" class' % (modulename, classname)
    return formatter_class(emoticons=app_settings.EMOTICONS)

# For convenience, make a single instance of the currently specified post
# formatter available for reuse.
post_formatter = get_post_formatter()
