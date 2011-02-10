============
Django Forum
============

This is a basic forum application which should eventually be usable as a
pluggable application in a Django project, or by itself as a standalone
project.

Installation
============

Dependencies
------------

The following must be installed before you can use the forum application:

- `Redis`_ and `redis-py` are required for real-time tracking fun.
  For Windows users, there are `native redis binaries`_ available.
- `Python Imaging Library`_ (PIL) is required for validation of user avatars.
- `pytz`_ is required to perform timezone conversions based on the timezone
  registered users can choose as part of their forum profile.

Additionally, the following must be installed if you plan to use the
forum in standalone mode:

- `django-registration`_ is used to perform registration and validation of new
  users when running as a standalone project - it is assumed that when the forum
  is integrated into existing projects, they will already have their own
  registration mechanism in place.
- `Django Debug Toolbar`_ - 'nuff said.

The following modules are only required in certain circumstances:

- `python-markdown2`_ is required to use ``forum.formatters.MarkdownFormatter``
  to format posts using `Markdown`_ syntax.
- `postmarkup`_ is required to use ``forum.formatters.BBCodeFormatter``
  to format posts using a `BBCode`_-like syntax.

  - `_Pygments`_ is required by postmarkup.

.. _`Redis`: http://redis.io
.. _`redis-py`: https://github.com/andymccurdy/redis-py
.. _`native redis binaries`: https://github.com/dmajkic/redis/downloads
.. _`Python Imaging Library`: http://www.pythonware.com/products/pil/
.. _`pytz`: http://pytz.sourceforge.net/
.. _`django-registration`: http://code.google.com/p/django-registration/
.. _`Django Debug Toolbar`: http://robhudson.github.com/django-debug-toolbar/
.. _`python-markdown2`: http://code.google.com/p/python-markdown2
.. _`Markdown`: http://daringfireball.net/projects/markdown/
.. _`postmarkup`: http://code.google.com/p/postmarkup/
.. _`BBCode`: http://en.wikipedia.org/wiki/BBCode
.. _`Pygments`: http://pygments.org

Standalone Mode
---------------

At the time of typing, the codebase comes with a complete development
``settings.py`` module which can be used to run the forum in standalone
mode.

Pluggable Application Mode
--------------------------

**Note: this mode has not yet been fully developed or tested**

Add ``'forum'`` to your application's ``INSTALLED_APPS`` setting, then execute
``python manage.py syncdb`` from the command-line to install the tables it requires.

Include the forum's URLConf in your project's main URLConf at whatever URL you
like. For example::

    from django.conf.urls.defaults import *

    urlpatterns = patterns(
        (r'^forum/', include('forum.urls')),
    )

The forum application's URLs are decoupled using Django's `named URL patterns`_
feature, so it doesn't mind which URL you choose to have it accessible at.

.. _`named URL patterns`: http://www.djangoproject.com/documentation/url_dispatch/#naming-url-patterns

Settings
========

The following settings may be added to your project's settings module to
configure the forum application.

FORUM_STANDALONE
----------------

Default: ``False``

Whether or not the forum is being used in standalone mode. If ``True``,
URL configurations for the django.contrib.admin and django-registration
applications will be included in the application's main URLConf.

FORUM_POST_FORMATTER
--------------------

Default: ``'forum.formatters.PostFormatter'``

The Python path to the module to be used to format raw post input. This class
should satisfy the requirements defined below in `Post Formatter Structure`_.

FORUM_DEFAULT_POSTS_PER_PAGE
----------------------------

Default: ``20``

The number of posts which are displayed by default on any page where posts are
listed - this applies to registered users who do not choose to override the
number of posts per page and to anonymous users.

FORUM_DEFAULT_TOPICS_PER_PAGE
-----------------------------

Default: ``30``

The number of topics which are displayed by default on any page where topics are
listed - this applies to registered users who do not choose to override the
number of topics per page and to anonymous users.

FORUM_MAX_AVATAR_FILESIZE
--------------------------

Default: ``512 * 1024`` (512 kB)

The maximum allowable filesize for user avatars, specified in bytes. To disable
validation of user avatar filesizes, set this setting to ``None``.

FORUM_ALLOWED_AVATAR_FORMATS
----------------------------

Default: ``('GIF', 'JPEG', 'PNG')``

A tuple of allowed image formats for user avatars. To disable validation of user
avatar image formats, set this setting to ``None``.

FORUM_MAX_AVATAR_DIMENSIONS
---------------------------

Default: ``(64, 64)``

A two-tuple, (width, height), of maximum allowable dimensions for user avatars.
To disable validation of user avatar dimensions, set this setting to ``None``.

FORUM_FORCE_AVATAR_DIMENSIONS
-----------------------------

Default: ``True``

Whether or not ``<img>`` tags created for user avatars should include ``width``
and ``height`` attributes to force all avatars to be displayed with the
dimensions specified in the ``FORUM_MAX_AVATAR_DIMENSIONS`` setting.

FORUM_EMOTICONS
---------------

Default::

    {':angry:':    'angry.gif',
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
     ':wub:':      'wub.gif'}

A dict mapping emoticon symbols to the filenames of images they should be
replaced with when emoticons are enabled while formatting posts.

FORUM_REDIS_HOST
----------------

Default: ``'localhost``

FORUM_REDIS_PORT
----------------

Default: ``6379``

FORUM_REDIS_DB
--------------

Default: ``0``

Post Formatters
===============

Post formatting classes are responsible for taking raw input entered by forum
users and transforming and escaping it for display, as well as performing any
other operations which are dependent on the post formatting syntax being used.

The following post formatting classes are bundled with the forum application:

- ``forum.formatters.PostFormatter``
- ``forum.formatters.MarkdownFormatter``
- ``forum.formatters.BBCodeFormatter``

Post Formatter Structure
------------------------

When creating a custom post formatting class, you should subclass
``forum.formatters.PostFormatter`` and override the following:

QUICK_HELP_TEMPLATE
~~~~~~~~~~~~~~~~~~~

This class-level attribute should specify the location of a template providing
quick help, suitable for embedding into posting pages.

FULL_HELP_TEMPLATE
~~~~~~~~~~~~~~~~~~

This class-level attribute should specify the location of a template file
providing detailed help, suitable for embedding in a standalone page.

``format_post_body(body)``
~~~~~~~~~~~~~~~~~~~~~~~~~~

This method should accept raw post text input by the user, returning a version
of it which has been transformed and escaped for display. It is important that
the output of this function has been made safe for direct inclusion in
templates, as no further escaping will be performed.

For example, given the raw post text::

    [quote]T
    <es>
    t![/quote]

...a BBCode post formatter might return something like::

    <blockquote>T<br>
    &lt;es&gt;<br>
    t!</blockquote>

``quote_post(post)``
~~~~~~~~~~~~~~~~~~~~

This method should accept a ``Post`` object and return the raw post text for a
a "quoted" version of the post's content. The ``Post`` object itself is passed,
as opposed to just the raw post text, as the quote may wish to include other
details such as the name of the user who made the post, the time the post was
made at, a link back to the quoted post... and so on.

Note that the raw post text returned by this function will be escaped when it is
displayed to the user for editing, so to avoid double escaping it should *not*
be escaped by this function.

For example, given a ``Post`` whose raw ``body`` text is::

    T<es>t!

...a BBCode post formatter might return something like::

    [quote]T<es>t![/quote]
