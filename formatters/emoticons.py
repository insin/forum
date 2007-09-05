"""
Emoticon Replacement
====================

Converts emoticon symbols to images, with the symbols set as their
``alt`` text.

Basic usage::

   >>> em = Emoticons()
   >>> em.replace(u'Cheeky :p')
   u'Cheeky <img src="tongue.gif" alt=":p">'

Example showing usage of all arguments::

   >>> em = Emoticons(emoticons={':p': 'cheeky'},
   ...     base_url='http://localhost/', file_extension='png',
   ...     xhtml=True)
   >>> em.replace(u'Cheeky :p')
   u'Cheeky <img src="http://localhost/cheeky.png" alt=":p" />'

"""
import re

DEFAULT_EMOTICONS = {
    ':angry:':    'angry',
    ':blink:':    'blink',
    ':D':         'grin',
    ':huh:':      'huh',
    ':lol:':      'lol',
    ':o':         'ohmy',
    ':ph34r:':    'ph34r',
    ':rolleyes:': 'rolleyes',
    ':(':         'sad',
    ':)':         'smile',
    ':p':         'tongue',
    ':unsure:':   'unsure',
    ':wacko:':    'wacko',
    ';)':         'wink',
    ':wub:':      'wub',
}

class Emoticons:
    """
    Replacement of multiple string pairs in one go based on
    http://effbot.org/zone/python-replace.htm
    """
    def __init__ (self, emoticons=None, base_url='', file_extension='gif',
        xhtml=False):
        """
        emoticons
           A dict mapping emoticon symbols to image names.

        base_url
           The base URL to be prepended to image names to generating
           image URLs.

        file_extension
           The file extension to be appended to image names when
           generating image URLs.

        xhtml
           If ``True``, a closing slash will be added to image tags.
        """
        if emoticons is None: emoticons = DEFAULT_EMOTICONS
        self.emoticons = dict(
            [(k, '<img src="%s%s.%s" alt="%s"%s>' % (base_url, v,
                                                     file_extension, k,
                                                     xhtml and ' /' or '')) \
             for k, v in emoticons.items()])
        keys = emoticons.keys()
        keys.sort() # lexical order
        keys.reverse() # use longest match first
        self.pattern = re.compile('|'.join([re.escape(key) for key in keys]))

    def replace(self, text):
        """
        text
           The text to be processed.
        """
        def repl(match, get=self.emoticons.get):
            item = match.group(0)
            return get(item, item)
        return self.pattern.sub(repl, text)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
