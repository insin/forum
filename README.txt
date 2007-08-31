============
Django Forum
============

:author: Jonathan Buchanan

This is a basic forum application which should eventually be usable as a
pluggable application in a Django project, or by itself as a standalone project.


TODO
====

Now
---

Smaller features which can be implemented now.

- Implement navigation / forum and topic breadcrumbs.
- Add method to post formatting modules for display of help text on post forms.
- Tidy HTML where appropriate - for example, there are currently a lot of
  redundant ``<dt>`` elements in the user profiles displayed next to posts
  (which are being hidden using CSS), while the labels they contain are being
  doubled up in the corresponding ``<dd>`` elements - yuck!
- Validation of avatars:

  - Simple URL filename check.
  - Restrict based on their dimensions (loading images with PIL) or simply force
    them to appear at a certain size as a quick fix.

Later
-----

Features which require a bit more consideration - as in does the application
*really* need the added complexity they bring? It has a very simple structure at
the moment.

- Forum groups with ordering defined per group
- Subforums
- Tracking the posts a user has viewed and when they last viewed them.
- Tracking which posts were replied to / offering a threaded view for topics.

Installation
============

Dependencies
------------

The following must be installed before you can use the forum application:

- `Django`_ is obviously required, but you'll need a recent SVN checkout to use
  the forum application - it *will not* work with version 0.96, which is the
  latest Django release at the time of writing.
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

.. _`Django`: http://www.djangoproject.com
.. _`pytz`: http://pytz.sourceforge.net/
.. _`django-registration`: http://code.google.com/p/django-registration/
.. _`python-markdown`: http://www.freewisdom.org/projects/python-markdown/
.. _`Markdown`: http://daringfireball.net/projects/markdown/
.. _`postmarkup`: http://code.google.com/p/postmarkup/
.. _`BBCode`: http://en.wikipedia.org/wiki/BBCode


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

Post formatting modules must provide the following functions:

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

    <blockquote]T<br>
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
