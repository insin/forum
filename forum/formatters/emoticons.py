"""
Emoticon Replacement
====================

Converts emoticon symbols to images, with the symbols set as their
``alt`` text.

Basic usage::

   >>> em = Emoticons({':p': 'tongue.gif'})
   >>> em.process(u'Cheeky :p')
   u'Cheeky <img src="tongue.gif" alt=":p">'

Example showing usage of all arguments::

   >>> em = Emoticons({':p': 'cheeky.png'},
   ...     base_url='http://localhost/', xhtml=True)
   >>> em.process(u'Cheeky :p')
   u'Cheeky <img src="http://localhost/cheeky.png" alt=":p" />'

Other tests::

   >>> em = Emoticons({})
   >>> em.process(u'Cheeky :p')
   u'Cheeky :p'

"""
import re

class Emoticons:
    """
    Replacement of multiple string pairs in one go based on
    http://effbot.org/zone/python-replace.htm
    """
    def __init__ (self, emoticons, base_url='', xhtml=False):
        """
        emoticons
           A dict mapping emoticon symbols to image filenames.

        base_url
           The base URL to be prepended to image filenames when
           generating image URLs.

        xhtml
           If ``True``, a closing slash will be added to image tags.
        """
        self.emoticons = dict(
            [(k, '<img src="%s%s" alt="%s"%s>' % (base_url, v, k,
                                                  xhtml and ' /' or '')) \
             for k, v in emoticons.items()])
        keys = emoticons.keys()
        keys.sort() # lexical order
        keys.reverse() # use longest match first
        self.pattern = re.compile('|'.join([re.escape(key) for key in keys]))

    def process(self, text):
        """
        Returns a version of the given text with emoticon symbols
        replaced with HTML for their image equivalents.

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
