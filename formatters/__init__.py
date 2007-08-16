def get_formatter():
    from django.conf import settings
    try:
        formatter_module = settings.FORUM_POST_FORMATTER
    except AttributeError:
        formatter_module = 'forum.formatters.bbcode_formatter'
    try:
        return __import__(formatter_module, {}, {}, [''])
    except ImportError, e:
        raise EnvironmentError("Could not import post formatter '%s' (Is it on sys.path? Does it have syntax errors?): %s" % (formatter_module, e))

post_formatter = get_formatter()
