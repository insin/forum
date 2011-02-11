============
Django Forum
============

This is a basic forum application which is usable by itself as a standalone
project and should eventually be usable as a pluggable application in any
Django project.

.. contents::
   :local:
   :depth: 2

Features
========

- **Bog-standard layout** - Sections |rarr| Forums |rarr| Topics.

- **Search** posts and topics - search for keywords by section, forum,
  username, post type and date.

  Searching supports quoted phrases and ``+`` and ``-`` modifiers on
  keywords and phrases.

- **Real-time tracking** with `Redis`_ - performing ``UPDATE`` queries on
  every single page view to track view counts, active users and user
  activity on the forum? No.

  Redis does it in style.

- **Configurable post formatting** - comes with BBCode and Markdown formatters.

- **Metaposts** - each topic has regular posts, as you'd expect, and also
  metaposts. These are effectively a second thread of conversation for
  posts *about* the topic. Why, you say?

  People who want to talk about the topic itself or how it's being
  discussed, or just start a good old ding-dong with other users, rather
  than taking part in the discussion at hand, have a place to vent instead
  of dragging the topic into the realm of the off-topic.

  Moderators have another option other than deleting or hiding posts when
  topics start to take a turn for the worse in that direction.

  People who just wanted to read and post in the original topic can
  continue to do so *and* still have it out

  Inspired by my many years with the excellent people of `RLLMUK`_.

- **Avatar validation** - linked avatars are validated for format, file
  size and dimensions.

Possible Misfeatures
--------------------

- **Denormalised up the yazoo** - data such as post counts and last post
  information are maintained on all affected objects on every write.

  Trading write complexity and ease of maintenance against fewer, more
  simple reads, just because.

- **No signatures** - it's not a bug, it's a feature.

.. _`RLLMUK`: http://www.rllmukforum.com
.. |rarr| unicode:: 0x2192 .. rightward arrow

Installation
============

Dependencies
------------

**Required:**

- `Python Imaging Library`_ (PIL) is required for validation of user avatars.
- `pytz`_ is required to perform timezone conversions based on the timezone
  registered users can choose as part of their forum profile.

**Required for standalone mode:**

- `django-registration`_ is used to perform registration and validation of new
  users when running as a standalone project - it is assumed that when the forum
  is integrated into existing projects, they will already have their own
  registration mechanism in place.

**Required based on settings:**

- `Redis`_ and `redis-py`_ are required for real-time tracking fun if
  ``FORUM_USE_REDIS`` is set to ``True``. For Windows users,
  `native Redis binaries`_ are available.
- `python-markdown2`_ is required to use ``forum.formatters.MarkdownFormatter``
  to format posts using `Markdown`_ syntax.
- `postmarkup`_ and `Pygments`_ are required to use
  ``forum.formatters.BBCodeFormatter`` to format posts using `BBCode`_ syntax.
- is required by postmarkup.

**Others:**

- `Django Debug Toolbar`_ will be used if available, if the forum is in
  standalone mode and ``DEBUG`` is set to ``True``.

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

It's configured to to use Redis for real-time tracking on the forum and
for session management using ``forum.sessions.redis_session_backend``.

Pluggable Application Mode
--------------------------

**Note: this mode has not yet been fully developed or tested**

Add ``'forum'`` to your application's ``INSTALLED_APPS`` setting, then run
``syncdb`` to create its tables.

Include the forum's URLConf in your project's main URLConf at whatever URL you
like. For example::

    from django.conf.urls.defaults import *

    urlpatterns = patterns(
        (r'^forum/', include('forum.urls')),
    )

The forum application's URLs are decoupled using Django's `named URL patterns`_
feature, so it doesn't mind which URL you mount it at.

.. _`named URL patterns`: http://www.djangoproject.com/documentation/url_dispatch/#naming-url-patterns

Settings
========

The following settings may be added to your project's settings module to
configure the forum application.

``FORUM_STANDALONE``

   *Default:* ``False``

   Whether or not the forum is being used in standalone mode. If set to
   ``True``, URL configurations for the django.contrib.admin and
   django-registration apps will be included in the application's main
   URLConf.

``FORUM_USE_REDIS``

   *Default:* ``False``

   Whether or not the forum should use `Redis`_ to track real-time information
   such as topic view counts, active users and user locations on the forum.

   If set to ``False``, these details will not be displayed.

``FORUM_REDIS_HOST``

   *Default:* ``'localhost'``

   Redis host.

``FORUM_REDIS_PORT``

   *Default:* ``6379``

   Redis port.

``FORUM_REDIS_DB``

   *Default:* ``0``

   Redis database number, ``0``-``16``.

``FORUM_POST_FORMATTER``

   *Default:* ``'forum.formatters.PostFormatter'``

   The Python path to the module to be used to format raw post input. This class
   should satisfy the requirements defined below in `Post Formatter Structure`_.

``FORUM_DEFAULT_POSTS_PER_PAGE``

   *Default:* ``20``

   The number of posts which are displayed by default on any page where posts are
   listed - this applies to registered users who do not choose to override the
   number of posts per page and to anonymous users.

``FORUM_DEFAULT_TOPICS_PER_PAGE``

   *Default:* ``30``

   The number of topics which are displayed by default on any page where topics are
   listed - this applies to registered users who do not choose to override the
   number of topics per page and to anonymous users.

``FORUM_MAX_AVATAR_FILESIZE``

   *Default:* ``512 * 1024`` (512 kB)

   The maximum allowable filesize for user avatars, specified in bytes. To disable
   validation of user avatar filesizes, set this setting to ``None``.

``FORUM_ALLOWED_AVATAR_FORMATS``

   *Default:* ``('GIF', 'JPEG', 'PNG')``

   A tuple of allowed image formats for user avatars. To disable validation of user
   avatar image formats, set this setting to ``None``.

``FORUM_MAX_AVATAR_DIMENSIONS``

   *Default:* ``(64, 64)``

   A two-tuple, (width, height), of maximum allowable dimensions for user avatars.
   To disable validation of user avatar dimensions, set this setting to ``None``.

``FORUM_FORCE_AVATAR_DIMENSIONS``

   *Default:* ``True``

   Whether or not ``<img>`` tags created for user avatars should include ``width``
   and ``height`` attributes to force all avatars to be displayed with the
   dimensions specified in the ``FORUM_MAX_AVATAR_DIMENSIONS`` setting.

``FORUM_EMOTICONS``

   *Default:*

   ::

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

   A ``dict`` mapping emoticon symbols to the filenames of images they
   should be replaced with when emoticons are enabled while formatting
   posts. Images should be placed in media/img/emticons.

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

``QUICK_HELP_TEMPLATE``

   This class-level attribute should specify the location of a template providing
   quick help, suitable for embedding into posting pages.

``FULL_HELP_TEMPLATE``

   This class-level attribute should specify the location of a template file
   providing detailed help, suitable for embedding in a standalone page.

``format_post_body(body)``

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

.. _`Redis`: http://redis.io