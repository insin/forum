from forum import app_settings

# Two-tuples of (attribute name, must be callable), defining the minimum
# required of a post formatting module.
POST_FORMATTING_MODULE_REQUIREMENTS = (
    ('QUICK_HELP_TEMPLATE', False),
    ('FULL_HELP_TEMPLATE', False),
    ('format_post_body', True),
    ('quote_post', True),
)

def get_post_formatter():
    try:
        mod = __import__(app_settings.POST_FORMATTING_MODULE, {}, {}, [''])
        for attr, must_be_callable in POST_FORMATTING_MODULE_REQUIREMENTS:
            if not hasattr(mod, attr) or \
               must_be_callable and not callable(getattr(mod, attr)):
                raise ValueError('The "%s" module does not define a %s"%s" attribute, which is required for it to be used as a post formatter.' % (
                    app_settings.POST_FORMATTING_MODULE, must_be_callable and 'callable ' or '', attr))
        return mod
    except ImportError, e:
        raise EnvironmentError('Could not import post formatting module "%s" (Is it on sys.path? Does it have syntax errors?): %s' % (app_settings.POST_FORMATTING_MODULE, e))

post_formatter = get_post_formatter()
