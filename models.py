import datetime

from django.contrib.auth.models import User
from django.db import connection, models, transaction
from django.utils.encoding import smart_unicode
from django.utils.text import truncate_words

from forum.formatters import post_formatter
from pytz import common_timezones

__all__ = ['ForumProfile', 'Section', 'Forum', 'Topic', 'Post']

DENORMALISED_DATA_NOTICE = u'You shouldn\'t need to edit this data manually.'

qn = connection.ops.quote_name

class ForumProfileManager(models.Manager):
    def get_for_user(self, user):
        """
        Returns the Forum Profile for this user, creating it first if
        necessary and caching it the first time it is looked up.
        """
        if not hasattr(user, '_forum_profile_cache'):
            profile, created = self.get_or_create(user=user)
            user._forum_profile_cache = profile
        return user._forum_profile_cache

    def update_post_counts_in_bulk(self, user_ids):
        """
        Updates the post counts of all given users.
        """
        opts = self.model._meta
        post_opts = Post._meta
        query = """
        UPDATE %(forum_profile)s
        SET %(post_count)s = (
            SELECT COUNT(*)
            FROM %(post)s
            WHERE %(post)s.%(post_user_fk)s = %(forum_profile)s.%(user_fk)s
        )
        WHERE %(user_fk)s IN (%(user_pks)s)""" % {
            'forum_profile': qn(opts.db_table),
            'post_count': qn(opts.get_field('post_count').column),
            'post': qn(post_opts.db_table),
            'post_user_fk': qn(post_opts.get_field('user').column),
            'user_fk': qn(opts.get_field('user').column),
            'user_pks': ','.join(['%s'] * len(user_ids)),
        }
        cursor = connection.cursor()
        cursor.execute(query, user_ids)

TIMEZONE_CHOICES = tuple([(tz, tz) for tz in common_timezones])

TOPICS_PER_PAGE_CHOICES = (
    (10, '10'),
    (20, '20'),
    (30, '30'),
    (40, '40'),
)

POSTS_PER_PAGE_CHOICES = (
    (10, '10'),
    (20, '20'),
    (30, '30'),
    (40, '40'),
)

class ForumProfile(models.Model):
    """
    A user's forum profile.
    """
    USER_GROUP      = 'U'
    MODERATOR_GROUP = 'M'
    ADMIN_GROUP     = 'A'

    GROUP_CHOICES = (
        (USER_GROUP, 'Users'),
        (MODERATOR_GROUP, 'Moderators'),
        (ADMIN_GROUP, 'Admins'),
    )

    user     = models.ForeignKey(User, unique=True, related_name='forum_profile')
    group    = models.CharField(max_length=1, choices=GROUP_CHOICES, default=USER_GROUP)
    title    = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    avatar   = models.URLField(max_length=200, verify_exists=False, blank=True)
    website  = models.URLField(max_length=200, verify_exists=False, blank=True)

    # Board settings
    timezone        = models.CharField(max_length=25, choices=TIMEZONE_CHOICES, blank=True)
    topics_per_page = models.PositiveIntegerField(choices=TOPICS_PER_PAGE_CHOICES, null=True, blank=True)
    posts_per_page  = models.PositiveIntegerField(choices=POSTS_PER_PAGE_CHOICES, null=True, blank=True)
    auto_fast_reply = models.BooleanField(default=False)

    # Denormalised data
    post_count = models.PositiveIntegerField(default=0)

    objects = ForumProfileManager()

    def __unicode__(self):
        return u'Forum Profile for %s' % self.user

    class Admin:
        list_display = ('user', 'group', 'title', 'location',
                        'post_count')
        list_filter = ('group',)
        fields = (
            (None, {
                'fields': ('user', 'group', 'title', 'location', 'avatar',
                           'website'),
            }),
            (u'Board settings', {
                'fields': ('timezone', 'topics_per_page', 'posts_per_page',
                           'auto_fast_reply'),
            }),
            (u'Denormalised data', {
                'classes': 'collapse',
                'description': DENORMALISED_DATA_NOTICE,
                'fields': ('post_count',),
            }),
        )

    @models.permalink
    def get_absolute_url(self):
        return ('forum_user_profile', (smart_unicode(self.user_id),))

    def is_moderator(self):
        """
        Returns ``True`` if the User represented by this profile has
        moderation privileges, ``False`` otherwise.
        """
        return self.group in (self.MODERATOR_GROUP, self.ADMIN_GROUP)

    def is_admin(self):
        """
        Returns ``True`` if the User represented by this profile has
        administrative privileges, ``False`` otherwise.
        """
        return self.group == self.ADMIN_GROUP

    def update_post_count(self):
        """
        Executes a simple SQL ``UPDATE`` to update this profile's
        ``post_count``.
        """
        opts = self._meta
        cursor = connection.cursor()
        cursor.execute('UPDATE %s SET %s=%%s WHERE %s=%%s' % (
            qn(opts.db_table), qn(opts.get_field('post_count').column),
            qn(opts.pk.column)), [self.user.posts.count(), self.pk])

    update_post_count.alters_data = True

class SectionManager(models.Manager):
    def get_forums_by_section(self):
        """
        Yields ordered two-tuples of (section, forums).
        """
        section_forums = {}
        for forum in Forum.objects.all():
            section_forums.setdefault(forum.section_id, []).append(forum)
        for section in super(SectionManager, self).get_query_set():
            yield section, section_forums.get(section.id, [])

    def increment_orders(self, start_at):
        """
        Increments ``order`` for all sections which have an ``order``
        greater than or equal to ``start_at``.
        """
        self._change_orders(start_at, '+1')

    def decrement_orders(self, start_at):
        """
        Increments ``order`` for all sections which have an ``order``
        greater than or equal to ``start_at``.
        """
        self._change_orders(start_at, '-1')

    def _change_orders(self, start_at, change):
        opts = self.model._meta
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE %(section_table)s
            SET %(order)s=%(order)s%(change)s
            WHERE %(order)s>=%%s""" % {
                'section_table': qn(opts.db_table),
                'order': qn(opts.get_field('order').column),
                'change': change,
            }, [start_at])

class Section(models.Model):
    """
    Provides categorisation for forums.
    """
    name  = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField()

    objects = SectionManager()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('order',)

    class Admin:
        list_display = ('name', 'order')

    @models.permalink
    def get_absolute_url(self):
        return ('forum_section_detail', (smart_unicode(self.id),))

    def delete(self):
        """
        This method is overridden to maintain consecutive ordering and
        to update the post counts of any users who had posts in the
        Forums in this Section.
        """
        affected_user_ids = [user['id'] for user in \
            User.objects.filter(posts__topic__forum__section=self) \
                         .distinct()\
                          .values('id')]
        super(Section, self).delete()
        Section.objects.decrement_orders(self.order)
        if len(affected_user_ids) > 0:
            ForumProfile.objects.update_post_counts_in_bulk(affected_user_ids)
        transaction.commit_unless_managed()

class ForumManager(models.Manager):
    def increment_orders(self, section_id, start_at):
        """
        Increments ``order`` for all forums in the given section which
        have an ``order`` greater than or equal to ``start_at``.
        """
        self._change_orders(section_id, start_at, '+1')

    def decrement_orders(self, section_id, start_at):
        """
        Decrements ``order`` for all forums in the given section which
        have an ``order`` greater than or equal to ``start_at``.
        """
        self._change_orders(section_id, start_at, '-1')

    def _change_orders(self, section_id, start_at, change):
        opts = self.model._meta
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE %(forum_table)s
            SET %(order)s=%(order)s%(change)s
            WHERE %(section_fk)s=%%s
              AND %(order)s>=%%s""" % {
                'forum_table': qn(opts.db_table),
                'order': qn(opts.get_field('order').column),
                'change': change,
                'section_fk': qn(opts.get_field('section').column),
            }, [section_id, start_at])

class Forum(models.Model):
    """
    Provides categorisation for discussion topics.
    """
    name        = models.CharField(max_length=100)
    section     = models.ForeignKey(Section, related_name='forums')
    description = models.TextField(blank=True)
    order       = models.PositiveIntegerField()

    # Administration
    locked = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)

    # Denormalised data
    topic_count      = models.PositiveIntegerField(default=0)
    last_post_at     = models.DateTimeField(null=True, blank=True)
    last_topic_id    = models.PositiveIntegerField(null=True, blank=True)
    last_topic_title = models.CharField(max_length=100, blank=True)
    last_user_id     = models.PositiveIntegerField(null=True, blank=True)
    last_username    = models.CharField(max_length=30, blank=True)

    objects = ForumManager()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('order',)

    class Admin:
        list_display = ('name', 'section', 'description', 'order', 'topic_count',
                        'locked', 'hidden')
        list_filter = ('section',)
        fields = (
            (None, {
                'fields': ('name', 'section', 'description', 'order'),
            }),
            (u'Administration', {
                'fields': ('locked', 'hidden'),
            }),
            (u'Denormalised data', {
                'classes': 'collapse',
                'description': DENORMALISED_DATA_NOTICE,
                'fields': ('topic_count', 'last_post_at', 'last_topic_id',
                           'last_topic_title','last_user_id', 'last_username'),
            }),
        )

    @models.permalink
    def get_absolute_url(self):
        return ('forum_forum_detail', (smart_unicode(self.id),))

    def delete(self):
        """
        This method is overridden to maintain consecutive ordering and
        to update the post counts of any users who had posts in this
        forum.
        """
        affected_user_ids = [user['id'] for user in \
            User.objects.filter(posts__topic__forum=self) \
                         .distinct() \
                          .values('id')]
        super(Forum, self).delete()
        Forum.objects.decrement_orders(self.section_id, self.order)
        if len(affected_user_ids) > 0:
            ForumProfile.objects.update_post_counts_in_bulk(affected_user_ids)
        transaction.commit_unless_managed()

    def update_topic_count(self):
        """
        Executes a simple SQL ``UPDATE`` to update this forum's
        ``topic_count``.
        """
        opts = self._meta
        cursor = connection.cursor()
        cursor.execute('UPDATE %s SET %s=%%s WHERE %s=%%s' % (
            qn(opts.db_table), qn(opts.get_field('topic_count').column),
            qn(opts.pk.column)), [self.topics.count(), self.pk])

    update_topic_count.alters_data = True

    def set_last_post(self, post=None):
        """
        Executes a simple SQL ``UPDATE`` to set details about this
        forum's last post.

        It is assumed that any post given is not a metapost and is not in
        a hidden topic.

        If the last post is not given, the last non-meta, non-hidden post
        will be looked up. This method should never set the details of a
        post in a hidden topic as the last post, as this would result in
        the display of latest post links which do not work for regular and
        anonymous users.
        """
        try:
            if post is None:
                post = Post.objects.filter(meta=False,
                                           topic__forum=self,
                                           topic__hidden=False) \
                                    .order_by('-posted_at', '-id')[0]
            params = [post.posted_at, post.topic.pk, post.topic.title,
                      post.user.pk, post.user.username, self.pk]
        except IndexError:
            # No post was given and there was no latest, non-hidden
            # Post, so there must not be any eligible Topics in the
            # Forum at the moment.
            params = [None, None, '', None, '', self.pk]
        opts = self._meta
        cursor = connection.cursor()
        cursor.execute('UPDATE %s SET %s=%%s, %s=%%s, %s=%%s, %s=%%s, %s=%%s WHERE %s=%%s' % (
            qn(opts.db_table), qn(opts.get_field('last_post_at').column),
            qn(opts.get_field('last_topic_id').column),
            qn(opts.get_field('last_topic_title').column),
            qn(opts.get_field('last_user_id').column),
            qn(opts.get_field('last_username').column),
            qn(opts.pk.column)), params)

    set_last_post.alters_data = True

class TopicManager(models.Manager):
    def _add_user_details(self, queryset):
        """
        Uses ``extra`` to add User details to a Topic queryset.
        """
        opts = self.model._meta
        user_opts = User._meta
        user_table = qn(user_opts.db_table)
        return queryset.extra(
            select={
                'user_username': '%s.%s' % (user_table, qn(user_opts.get_field('username').column)),
            },
            tables=[user_table],
            where=[
                '%s.%s=%s.%s' % (
                    qn(opts.db_table),
                    qn(opts.get_field('user').column),
                    user_table,
                    qn(user_opts.pk.column),
                ),
            ]
        )

    def _add_forum_details(self, queryset):
        """
        Uses ``extra`` to add Forum details to a Topic queryset.
        """
        opts = self.model._meta
        forum_opts = Forum._meta
        forum_table = qn(forum_opts.db_table)
        return queryset.extra(
            select={
                'forum_name': '%s.%s' % (forum_table, qn(forum_opts.get_field('name').column)),
            },
            tables=[forum_table],
            where=[
                '%s.%s=%s.%s' % (
                    qn(opts.db_table),
                    qn(opts.get_field('forum').column),
                    forum_table,
                    qn(forum_opts.pk.column),
                ),
            ]
        )

    def with_user_details(self):
        """
        Creates a ``QuerySet`` containing Topics which have
        additional information about the User who created them.
        """
        return self._add_user_details(super(TopicManager, self).get_query_set())

    def with_forum_details(self):
        """
        Creates a ``QuerySet`` containing Topics which have
        additional information about the Forum they belong to.
        """
        return self._add_forum_details(super(TopicManager, self).get_query_set())

    def with_forum_and_user_details(self):
        """
        Creates a ``QuerySet`` containing Topics which have
        additional information about the User who created them and the
        Forum they belong to.
        """
        return self._add_forum_details(
            self._add_user_details(
                super(TopicManager, self).get_query_set()))

    def with_display_details(self):
        """
        Creates a ``QuerySet`` which adds additional information required
        to display a Topic's detail page without having to perform extra
        queries.
        """
        opts = self.model._meta
        forum_opts = Forum._meta
        forum_table = qn(forum_opts.db_table)
        section_opts = Section._meta
        section_table = qn(section_opts.db_table)
        return super(TopicManager, self).get_query_set().extra(
            select={
                'forum_name': '%s.%s' % (forum_table, qn(forum_opts.get_field('name').column)),
                'section_id': '%s.%s' % (forum_table, qn(forum_opts.get_field('section').column)),
                'section_name': '%s.%s' % (section_table, qn(section_opts.get_field('name').column)),
            },
            tables=[forum_table, section_table],
            where=[
                '%s.%s=%s.%s' % (
                    qn(opts.db_table),
                    qn(opts.get_field('forum').column),
                    forum_table,
                    qn(forum_opts.pk.column),
                ),
                '%s.%s=%s.%s' % (
                    qn(forum_table),
                    qn(forum_opts.get_field('section').column),
                    section_table,
                    qn(section_opts.pk.column),
                ),
            ]
        )

    def with_standalone_details(self):
        """
        Creates a ``QuerySet`` comtaining Topics which have additional
        information about their User, Forum and Section.
        """
        opts = self.model._meta
        user_opts = User._meta
        user_table = qn(user_opts.db_table)
        return self.with_display_details().extra(
            select={
                'user_username': '%s.%s' % (user_table, qn(user_opts.get_field('username').column)),
            },
            tables=[user_table],
            where=[
                '%s.%s=%s.%s' % (
                    qn(opts.db_table),
                    qn(opts.get_field('user').column),
                    user_table,
                    qn(user_opts.pk.column),
                ),
            ]
        )

class Topic(models.Model):
    """
    A discussion topic.
    """
    title       = models.CharField(max_length=100)
    forum       = models.ForeignKey(Forum, related_name='topics')
    user        = models.ForeignKey(User, related_name='topics')
    description = models.CharField(max_length=100, blank=True)
    started_at  = models.DateTimeField(editable=False)

    # Administration
    pinned = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)

    # Denormalised data
    post_count     = models.PositiveIntegerField(default=0)
    metapost_count = models.PositiveIntegerField(default=0)
    view_count     = models.PositiveIntegerField(default=0)
    last_post_at   = models.DateTimeField(null=True, blank=True)
    last_user_id   = models.PositiveIntegerField(null=True, blank=True)
    last_username  = models.CharField(max_length=30, blank=True)

    objects = TopicManager()

    def __unicode__(self):
        return self.title

    def save(self, **kwargs):
        """
        This method is overridden to implement the following:

        - Populating the non-editable ``started_at`` field.
        - Updating denormalised data in the related ``Forum`` object
          when creating a new topic.
        - If ``title`` has been updated and this Topic was set in its
          Forum's last post details, it needs to be updated in the
          Forum as well.
        """
        is_new = False
        if not self.id:
            self.started_at = datetime.datetime.now()
            is_new = True
        super(Topic, self).save(**kwargs)
        if is_new:
            self.forum.update_topic_count()
            transaction.commit_unless_managed()
        elif self.id == self.forum.last_topic_id and \
             self.title != self.forum.last_topic_title and \
             not self.hidden:
            self.forum.set_last_post()
            transaction.commit_unless_managed()

    def delete(self):
        """
        This method is overridden to update denormalised data in
        related ``Forum`` and ``ForumProfile`` objects after a topic
        has been deleted:

        - The forum's topic count always has to be updated.
        - The post counts of profiles of any users who posted in the
          topic always have to be updated.
        - If it was set as the topic in the forum's last post details,
          these need to be updated.
        """
        forum = self.forum
        was_last_topic = self.id == forum.last_topic_id
        affected_user_ids = [user['id'] for user in \
            User.objects.filter(posts__topic=self).distinct().values('id')]
        super(Topic, self).delete()
        forum.update_topic_count()
        if was_last_topic:
            forum.set_last_post()
        if len(affected_user_ids) > 0:
            ForumProfile.objects.update_post_counts_in_bulk(affected_user_ids)
        transaction.commit_unless_managed()

    class Meta:
        ordering = ('-last_post_at', '-started_at')

    class Admin:
        list_display = ('title', 'forum', 'user', 'started_at', 'post_count',
                        'metapost_count', 'view_count', 'last_post_at', 'locked',
                        'pinned', 'hidden')
        list_filter = ('forum', 'locked', 'pinned', 'hidden')
        fields = (
            (None, {
                'fields': ('title', 'forum', 'user', 'description'),
            }),
            (u'Administration', {
                'fields': ('pinned', 'locked', 'hidden'),
            }),
            (u'Denormalised data', {
                'classes': 'collapse',
                'description': DENORMALISED_DATA_NOTICE,
                'fields': ('post_count', 'metapost_count', 'view_count',
                           'last_post_at', 'last_user_id', 'last_username'),
            }),
        )
        search_fields = ('title',)

    @models.permalink
    def get_absolute_url(self):
        return ('forum_topic_detail', (smart_unicode(self.id),))

    @models.permalink
    def get_meta_url(self):
        return ('forum_topic_meta_detail', (smart_unicode(self.id),))

    def get_first_post(self):
        """
        Gets the first Post in this Topic.
        """
        return self.posts.order_by('num_in_topic')[0]

    def update_post_count(self, meta=False):
        """
        Executes a simple SQL ``UPDATE`` to update one of this topic's
        denormalised post counts, based on ``meta``.
        """
        opts = self._meta
        cursor = connection.cursor()
        cursor.execute('UPDATE %s SET %s=%%s WHERE %s=%%s' % (
            qn(opts.db_table), qn(opts.get_field('%spost_count' % (meta and 'meta' or '',)).column),
            qn(opts.pk.column)), [self.posts.filter(meta=meta).count(), self.pk])

    update_post_count.alters_data = True

    def set_last_post(self, post=None):
        """
        Executes a simple SQL ``UPDATE`` to set details about this
        topic's last post and update its denormalised ``post_count``.

        If the last post is not given, it will be looked up.
        """
        if post is None:
            post = self.posts.filter(meta=False).order_by('-posted_at')[0]
        opts = self._meta
        cursor = connection.cursor()
        cursor.execute('UPDATE %s SET %s=%%s, %s=%%s, %s=%%s, %s=%%s WHERE %s=%%s' % (
            qn(opts.db_table), qn(opts.get_field('post_count').column),
            qn(opts.get_field('last_post_at').column),
            qn(opts.get_field('last_user_id').column),
            qn(opts.get_field('last_username').column),
            qn(opts.pk.column)), [self.posts.filter(meta=False).count(),
                                  post.posted_at, post.user.pk,
                                  post.user.username, self.pk])

    set_last_post.alters_data = True

    def increment_view_count(self):
        """
        Executes a simple SQL ``UPDATE`` to increment this Topic's
        ``view_count``.
        """
        self.view_count += 1
        opts = self._meta
        cursor = connection.cursor()
        cursor.execute('UPDATE %s SET %s=%%s WHERE %s=%%s' % (
            qn(opts.db_table), qn(opts.get_field('view_count').column),
            qn(opts.pk.column)), [self.view_count, self.pk])

    increment_view_count.alters_data = True

class TopicTrackerManager(models.Manager):
    def add_last_read_to_topics(self, topics, user):
        """
        If the given User is authenticated, adds a ``last_read``
        attribute to the given Topics based on their TopicTrackers. This
        will be ``None`` if there is no TopicTrackers for a Topic.
        """
        if user.is_authenticated():
            queryset = super(TopicTrackerManager, self).get_query_set().filter(
                user=user, topic__in=topics)
            last_read_dict = dict([(tracker.topic_id, tracker.last_read) \
                                   for tracker in queryset])
            for topic in topics:
                topic.last_read = last_read_dict.get(topic.pk, None)

class TopicTracker(models.Model):
    """
    Tracks the last time a user read a particular topic.
    """
    user      = models.ForeignKey(User, related_name='topic_trackers')
    topic     = models.ForeignKey(Topic, related_name='trackers')
    last_read = models.DateTimeField()

    objects = TopicTrackerManager()

    def __unicode__(self):
        return u'%s read %s at %s' % (self.user, self.topic, self.last_read)

    class Meta:
        unique_together = (('user', 'topic'),)

    class Admin:
        pass

    def update_last_read(self, last_read):
        """
        Executes a simple SQL ``UPDATE`` to update this tracker's
        ``last_read``.

        This avoids the extra query which would be performed to determine
        existance if calling save() on the instance instead.
        """
        opts = self._meta
        cursor = connection.cursor()
        cursor.execute('UPDATE %s SET %s=%%s WHERE %s=%%s' % (
            qn(opts.db_table), qn(opts.get_field('last_read').column),
            qn(opts.pk.column)), [last_read, self.pk])

    update_last_read.alters_data = True

class PostManager(models.Manager):
    def with_user_details(self):
        """
        Creates a ``QuerySet`` containing Posts which have
        additional information about the User who created them.
        """
        opts = self.model._meta
        user_opts = User._meta
        forum_profile_opts = ForumProfile._meta
        user_table = qn(user_opts.db_table)
        forum_profile_table = qn(forum_profile_opts.db_table)
        return super(PostManager, self).get_query_set().extra(
            select={
                'user_username': '%s.%s' % (user_table, qn(user_opts.get_field('username').column)),
                'user_date_joined': '%s.%s' % (user_table, qn(user_opts.get_field('date_joined').column)),
                'user_title': '%s.%s' % (forum_profile_table, qn(forum_profile_opts.get_field('title').column)),
                'user_avatar': '%s.%s' % (forum_profile_table, qn(forum_profile_opts.get_field('avatar').column)),
                'user_post_count': '%s.%s' % (forum_profile_table, qn(forum_profile_opts.get_field('post_count').column)),
                'user_location': '%s.%s' % (forum_profile_table, qn(forum_profile_opts.get_field('location').column)),
                'user_website': '%s.%s' % (forum_profile_table, qn(forum_profile_opts.get_field('website').column)),
            },
            tables=[user_table, forum_profile_table],
            where=[
                '%s.%s=%s.%s' % (
                    qn(opts.db_table),
                    qn(opts.get_field('user').column),
                    user_table,
                    qn(user_opts.pk.column),
                ),
                '%s.%s=%s.%s' % (
                    forum_profile_table,
                    qn(forum_profile_opts.get_field('user').column),
                    user_table,
                    qn(user_opts.pk.column),
                ),
            ]
        )

    def with_standalone_details(self):
        """
        Creates a ``QuerySet`` containing Posts which have
        additional information about the User who created them and their
        Topic, Forum and Section.
        """
        opts = self.model._meta
        topic_opts = Topic._meta
        forum_opts = Forum._meta
        section_opts = Section._meta
        topic_table = qn(topic_opts.db_table)
        forum_table = qn(forum_opts.db_table)
        section_table = qn(section_opts.db_table)
        return self.with_user_details().extra(
            select={
                'topic_title': '%s.%s' % (topic_table, qn(topic_opts.get_field('title').column)),
                'topic_post_count': '%s.%s' % (topic_table, qn(topic_opts.get_field('post_count').column)),
                'topic_view_count': '%s.%s' % (topic_table, qn(topic_opts.get_field('view_count').column)),
                'forum_id': '%s.%s' % (topic_table, qn(topic_opts.get_field('forum').column)),
                'forum_name': '%s.%s' % (forum_table, qn(forum_opts.get_field('name').column)),
                'section_id': '%s.%s' % (forum_table, qn(forum_opts.get_field('section').column)),
                'section_name': '%s.%s' % (section_table, qn(section_opts.get_field('name').column)),
            },
            tables=[topic_table, forum_table, section_table],
            where=[
                '%s.%s=%s.%s' % (
                    qn(opts.db_table),
                    qn(opts.get_field('topic').column),
                    topic_table,
                    qn(topic_opts.pk.column),
                ),
                '%s.%s=%s.%s' % (
                    qn(topic_opts.db_table),
                    qn(topic_opts.get_field('forum').column),
                    forum_table,
                    qn(forum_opts.pk.column),
                ),
                '%s.%s=%s.%s' % (
                    forum_table,
                    qn(forum_opts.get_field('section').column),
                    section_table,
                    qn(section_opts.pk.column),
                ),
            ]
        )

    def update_num_in_topic(self, topic, start_at, increment=False, meta=False):
        """
        Updates ``num_in_topic`` for all posts in the given topic
        which have a ``num_in_topic`` greater than ``start_at``.

        Values will be incremented or decremented based on ``increment``.
        """
        opts = self.model._meta
        cursor = connection.cursor()
        operator = {True: '+', False: '-'}[increment]
        cursor.execute("""
            UPDATE %(post_table)s
            SET %(num_in_topic)s=%(num_in_topic)s%(operator)s1
            WHERE %(topic_fk)s=%%s
              AND %(meta)s=%%s
              AND %(num_in_topic)s>%%s""" % {
                'post_table': qn(opts.db_table),
                'meta': qn(opts.get_field('meta').column),
                'num_in_topic': qn(opts.get_field('num_in_topic').column),
                'operator': operator,
                'topic_fk': qn(opts.get_field('topic').column),
            }, [topic.id, meta, start_at])

class Post(models.Model):
    """
    A post which forms part of a discussion.
    """
    user      = models.ForeignKey(User, related_name='posts')
    topic     = models.ForeignKey(Topic, related_name='posts')
    body      = models.TextField()
    body_html = models.TextField(editable=False)
    posted_at = models.DateTimeField(editable=False)
    edited_at = models.DateTimeField(editable=False, null=True, blank=True)
    user_ip   = models.IPAddressField(editable=False, null=True, blank=True)
    meta      = models.BooleanField(default=False)
    emoticons = models.BooleanField(default=True)

    # Denormalised data
    num_in_topic = models.PositiveIntegerField(default=0)

    objects = PostManager()

    def __unicode__(self):
        return truncate_words(self.body, 25)

    def save(self, **kwargs):
        """
        This method is overridden to implement the following:

        - Formatting and escaping the raw post body as HTML at save
          time.
        - Populating or updating non-editable post time fields.
        - Populating denormalised data in related ``Topic``, ``Forum``
          and ``ForumProfile`` objects when creating a new post.
        """
        self.body = self.body.strip()
        self.body_html = post_formatter.format_post(self.body, self.emoticons)
        is_new = False
        if not self.id:
            self.posted_at = datetime.datetime.now()
            self.num_in_topic = getattr(self.topic, '%spost_count' % \
                                        (self.meta and 'meta' or '',)) + 1
            is_new = True
        else:
            self.edited_at = datetime.datetime.now()
        super(Post, self).save(**kwargs)
        if is_new:
            if not self.meta:
                # Includes a non-metapost post count update
                self.topic.set_last_post(self)
            else:
                self.topic.update_post_count(meta=True)

            # Don't update the forum's last post if the topic is hidden
            # - this allows moderators to add posts to hidden topics
            # without them becoming visible on forum listing pages.
            if not self.meta and not self.topic.hidden:
                self.topic.forum.set_last_post(self)
            ForumProfile.objects.get_for_user(self.user).update_post_count()
            transaction.commit_unless_managed()

    def delete(self):
        """
        This method is overridden to update denormalised data in related
        ``Topic``, ``Forum``, ``ForumProfile`` and other ``Post``
        objects after the post has been deleted:

        - The ``post_count`` of the ForumProfile for the User who made
          the post always needs to be updated.
        - The ``post_count`` or ``metapost_count`` of the post's Topic
          always needs to be updated.
        - If this is not a metapost and was the last post in its Topic,
          the Topic's last post details need to be updated.
        - If this is not a metapost was the last post in its Topic's
          Forum, the Forum's last post details need to be updated to the
          new last post.
        - If this was not the last post in its Topic, the
          ``num_in_topic`` of all later posts need to be decremented.
        """
        topic = self.topic
        forum = topic.forum
        forum_profile = ForumProfile.objects.get_for_user(self.user)
        super(Post, self).delete()
        forum_profile.update_post_count()
        if not self.meta and self.posted_at == topic.last_post_at:
            # Includes a non-metapost post count update
            topic.set_last_post()
        else:
            topic.update_post_count(meta=self.meta)
        if not self.meta and self.posted_at == forum.last_post_at:
            forum.set_last_post()
        Post.objects.update_num_in_topic(topic, self.num_in_topic,
                                         increment=False, meta=self.meta)
        transaction.commit_unless_managed()

    class Admin:
        list_display = ('__unicode__', 'user', 'topic', 'meta', 'posted_at',
                        'edited_at', 'user_ip')
        list_filter = ('meta',)
        fields = (
            (None, {
                'fields': ('user', 'topic', 'body', 'meta', 'emoticons'),
            }),
            (u'Denormalised data', {
                'classes': 'collapse',
                'description': DENORMALISED_DATA_NOTICE,
                'fields': ('num_in_topic',),
            }),
        )
        search_fields = ('body',)

    @models.permalink
    def get_absolute_url(self):
        return ('forum_redirect_to_post', (smart_unicode(self.id),))

class Search(models.Model):
    """
    Caches search criteria and a limited number of results to avoid
    repitition of expensive searches when paginating results.
    """
    POST_SEARCH  = 'P'
    TOPIC_SEARCH = 'T'
    TYPE_CHOICES = (
        (POST_SEARCH, 'Posts'),
        (TOPIC_SEARCH, 'Topics'),
    )

    type          = models.CharField(max_length=1, choices=TYPE_CHOICES)
    user          = models.ForeignKey(User, related_name='searches')
    searched_at   = models.DateTimeField(editable=False)
    criteria_json = models.TextField()
    result_ids    = models.TextField()

    def save(self, **kwargs):
        if not self.id:
            self.searched_at = datetime.datetime.now()
        super(Search, self).save(**kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('forum_search_results', (smart_unicode(self.id),))

    def get_result_model(self):
        """
        Returns the model class this search holds results for.
        """
        return {self.POST_SEARCH: Post, self.TOPIC_SEARCH: Topic}[self.type]

    def is_post_search(self):
        """
        Returns ``True`` if this is a Post search, ``False`` otherwise.
        """
        return self.type == self.POST_SEARCH

    def is_topic_search(self):
        """
        Returns ``True`` if this is a Topic search, ``False`` otherwise.
        """
        return self.type == self.TOPIC_SEARCH
