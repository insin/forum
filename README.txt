============
Django Forum
============

:author: Jonathan Buchanan

This is a basic forum application which should eventually be usable as a
pluggable application in a Django project, or by itself as a standalone project.


Installation
============

Dependencies
------------

The following must be installed before you can use the forum application:

- `Django`_ is obviously required, but you'll need a recent SVN checkout to use
  the forum application - it *will not* work with version 0.96, which is the
  latest Django release at the time of writing.
- `Python Imaging Library`_ (PIL) is required for validation of user avatars.
- `pytz`_ is required to perform timezone conversions based on the timezone
  registered users can choose as part of their forum profile.

Additionally, the following must be installed if you plan to use the
forum in standalone mode:

- `django-registration`_ is used to perform registration and validation of new
  users when running as a standalone project - it is assumed that when the forum
  is integrated into existing projects, they will already have their own
  registration mechanism in place.

The following modules are only required in certain circumstances:

- `python-markdown`_ is required to use the
  ``forum.formatters.markdown_formatter`` module to to format posts using
  `Markdown`_ syntax.
- `postmarkup`_ is required to use the
  ``forum.formatters.bbcode_formatter`` module to format posts using a
  `BBCode`_-like syntax.

.. _`Django`: http://www.djangoproject.com/
.. _`Python Imaging Library`: http://www.pythonware.com/products/pil/
.. _`pytz`: http://pytz.sourceforge.net/
.. _`django-registration`: http://code.google.com/p/django-registration/
.. _`python-markdown`: http://www.freewisdom.org/projects/python-markdown/
.. _`Markdown`: http://daringfireball.net/projects/markdown/
.. _`postmarkup`: http://code.google.com/p/postmarkup/
.. _`BBCode`: http://en.wikipedia.org/wiki/BBCode

Get The Code
------------

The forum application is currently available as a `darcs`_ repository. Execute
the following command from somewhere on your Python path to grab the codebase::

    darcs get http://www.jonathanbuchanan.plus.com/repos/forum/

Should you wish to update the codebase at a later date with any subsequent
patches which have added to the repository, navigate to the ``forum`` directory
from the command-line and execute the following command::

    darcs pull

.. _`darcs`: http://www.darcs.net

Standalone Mode
---------------

At the time of writing, the codebase comes with the standard Django
``manage.py`` convenience module for administrating projects and a complete
``settings.py`` module which is filesystem agnostic and uses sqlite as
the project's database engine.

Quick Start
~~~~~~~~~~~

For a quick start, navigate to the ``forum`` directory from the command-line and
execute the following commands::

    python manage.py syncdb --noinput

    python create-test-data.py

    python manage.py runserver

Ensure that the application's static media files are accessible - the default
``MEDIA_URL`` setting points at ``http://localhost/media/forum/``, as the
default settings assume that you're going to be running a webserver locally to
serve up static media. If you're running `Apache`_, adding the following line to
your ``httpd.conf`` and restarting the server will ensure that the application's
media is accessible::

    Alias /media/forum /full/path/to/forum/media

Don't forget to replace ``/full/path/to/`` above with the actual full path to
your local copy of the codebase, of course.

.. _`Apache`: http://httpd.apache.org

Pluggable Application Mode
--------------------------

**Note: this has not yet been tested** -- See the `TODO list`_ for more
information on the testing which is yet to be performed.

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

.. _`TODO list`: http://www.jonathanbuchanan.plus.com/repos/forum/TODO.txt
.. _`named URL patterns`: http://www.djangoproject.com/documentation/url_dispatch/#naming-url-patterns

Additional Configuration
------------------------

If the server you're running the forum application on is sitting behind a
reverse proxy, add ``'django.middleware.http.SetRemoteAddrFromForwardedFor'`` to
the list of ``MIDDLEWARE_CLASSES`` in your settings module, to ensure that the
IP address each post was made from is recorded accurately.

In this situation, without this middleware in place all posts would appear to be
made from the server's local IP. The forum application does not attempt to use
the contents of the ``HTTP_X_FORWARDED_FOR`` header manually in this situation
due to the ease with which this could be exploited to "fake" post IP addresses
when not sitting behind a trusted reverse proxy, as discussed in the
`SetRemoteAddrFromForwardedFor documentation`_.

.. _`SetRemoteAddrFromForwardedFor documentation`: http://www.djangoproject.com/documentation/middleware/#django-middleware-http-setremoteaddrfromforwardedfor


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

FORUM_POST_FORMATTING_MODULE
----------------------------

Default: ``'forum.formatters.basic_formatter'``

The Python path to the module to be used to format raw post input. This module
should satisfy the requirements defined below in `Post Formatting Module
Structure`_.

FORUM_DEFAULT_POSTS_PER_PAGE
----------------------------

Default: ``20``

The number of posts which are displayed by default on any page where posts are
listed - this applies to registered users who do not choose to override the
number of posts per page and to anonymous users.

FORUM_DEFAULT_TOPICS_PER_PAGE
-----------------------------

Default: ``20``

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


Post Formatting Modules
=======================

Post formatting modules are responsible for taking raw input entered by forum
users and transforming and escaping it for display, as well as performing any
other operations which are dependent on the post formatting syntax being used.

The following post formatting modules are bundled with the forum application:

- ``forum.formatters.basic_formatter``
- ``forum.formatters.markdown_formatter``
- ``forum.formatters.bbcode_formatter``

Post Formatting Module Structure
--------------------------------

Post formatting modules must provide the following:

QUICK_HELP_TEMPLATE
~~~~~~~~~~~~~~~~~~~

This variable should specify the location of a template providing quick help,
suitable for embedding into posting pages.

FULL_HELP_TEMPLATE
~~~~~~~~~~~~~~~~~~

This variable should specify the location of a template file providing detailed
help, suitable for embedding in a standalone page.

``format_post_body(body)``
~~~~~~~~~~~~~~~~~~~~~~~~~~

This function should accept raw post text input by the user, returning a version
of it which has been transform and escaped for display. It is important that the
output of this function has been made safe for direct inclusion in templates, as
no further escaping will be performed.

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

This function should accept a ``Post`` object and return the raw post text for a
a "quoted" version of the post's content. The ``Post`` object itself is passed,
as opposed to just the raw post text, as the quote may wish to include other
details such as the name of the user who made the post, the time the post was
made at, a link back to the quoted post... and so on.

Note that the raw post text returned by this function will be escaped when it is
displayed to the user for editing, so to avoid double escaping, it should not
be escaped by this function.

For example, given a ``Post`` whose raw ``body`` text is::

    T<es>t!

...a BBCode post formatter might return something like::

    [quote]T<es>t![/quote]
