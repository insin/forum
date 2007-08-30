from forum import app_settings

def get_post_formatter():
    try:
        return __import__(app_settings.POST_FORMATTING_MODULE, {}, {}, [''])
    except ImportError, e:
        raise EnvironmentError('Could not import post formatting module "%s" (Is it on sys.path? Does it have syntax errors?): %s' % (app_settings.POST_FORMATTING_MODULE, e))

post_formatter = get_post_formatter()
