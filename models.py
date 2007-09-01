import datetime

from django.contrib.auth.models import User
from django.db import connection, models, transaction
from django.utils.encoding import smart_unicode
from django.utils.text import truncate_words
from pytz import common_timezones

from forum.formatters import post_formatter

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

TIMEZONE_CHOICES = tuple([(tz, tz) for tz in common_timezones])

USER_GROUP_CHOICES = (
    ('U', 'Users'),
    ('M', 'Moderators'),
    ('A', 'Admins'),
)

TOPICS_PER_PAGE_CHOICES = (
    (10,   '10'),
    (20,   '20'),
    (30,   '30'),
    (40,   '40'),
)

POSTS_PER_PAGE_CHOICES = (
    (10,   '10'),
    (20,   '20'),
    (30,   '30'),
    (40,   '40'),
)

class ForumProfile(models.Model):
    """
    A user's forum profile.
    """
    user     = models.ForeignKey(User, unique=True, related_name='forum_profile')
    group    = models.CharField(max_length=1, choices=USER_GROUP_CHOICES, default='U')
    title    = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    avatar   = models.URLField(verify_exists=False, blank=True)
    website  = models.URLField(verify_exists=False, blank=True)

    # Board settings
    timezone        = models.CharField(max_length=25, choices=TIMEZONE_CHOICES, blank=True)
    topics_per_page = models.PositiveIntegerField(choices=TOPICS_PER_PAGE_CHOICES, null=True, blank=True)
    posts_per_page  = models.PositiveIntegerField(choices=POSTS_PER_PAGE_CHOICES, null=True, blank=True)

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
                'fields': ('timezone', 'topics_per_page', 'posts_per_page'),
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
        return self.group in ('M', 'A')

    def is_admin(self):
        """
        Returns ``True`` if the User represented by this profile has
        administrative privileges, ``False`` otherwise.
        """
        return self.group == 'A'

    def update_post_count(self):
        """
        Executes a simple SQL ``UPDATE`` to update this profile's
        ``post_count``.
        """
        opts = self._meta
        cursor = connection.cursor()
        cursor.execute('UPDATE %s SET %s=%%s WHERE %s=%%s' % (
            qn(opts.db_table), qn(opts.get_field('post_count').column),
            qn(opts.pk.column)), [self.user.posts.count(), self._get_pk_val()])

    update_post_count.alters_data = True

class Forum(models.Model):
    """
    Provides categorisation for discussion topics.
    """
    name        = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order       = models.PositiveIntegerField(unique=True)

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

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('order',)

    class Admin:
        list_display = ('name', 'description', 'order', 'topic_count',
                        'locked', 'hidden')
        fields = (
            (None, {
                'fields': ('name', 'description', 'order'),
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
        return ('forum_detail', (smart_unicode(self.id),))

    def update_topic_count(self):
        """
        Executes a simple SQL ``UPDATE`` to increment this forum's
        ``topic_count``.
        """
        opts = self._meta
        cursor = connection.cursor()
        cursor.execute('UPDATE %s SET %s=%%s WHERE %s=%%s' % (
            qn(opts.db_table), qn(opts.get_field('topic_count').column),
            qn(opts.pk.column)), [self.topics.count(), self._get_pk_val()])

    update_topic_count.alters_data = True

    def set_last_post(self, post=None):
        """
        Executes a simple SQL ``UPDATE`` to set details about this
        forum's last post.

        If the last post is not given, it will be looked up.
        """
        if post is None:
            post = Post.objects.filter(topic__forum=self) \
                                .order_by('-posted_at', '-id')[0]
        opts = self._meta
        cursor = connection.cursor()
        cursor.execute('UPDATE %s SET %s=%%s, %s=%%s, %s=%%s, %s=%%s, %s=%%s WHERE %s=%%s' % (
            qn(opts.db_table), qn(opts.get_field('last_post_at').column),
            qn(opts.get_field('last_topic_id').column),
            qn(opts.get_field('last_topic_title').column),
            qn(opts.get_field('last_user_id').column),
            qn(opts.get_field('last_username').column),
            qn(opts.pk.column)), [post.posted_at, post.topic._get_pk_val(),
                                  post.topic.title, post.user._get_pk_val(),
                                  post.user.username, self._get_pk_val()])

    set_last_post.alters_data = True

class TopicManager(models.Manager):
    def with_user_details(self):
        """
        Creates a ``QuerySet`` containing Topics which have
        additional information about the User who created them.
        """
        opts = self.model._meta
        user_opts = User._meta
        user_table = qn(user_opts.db_table)
        return super(TopicManager, self).get_query_set().extra(
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

    def with_forum_and_user_details(self):
        """
        Creates a ``QuerySet`` containing Topics which have
        additional information about the User who created them and the
        Forum they belong to.
        """
        opts = self.model._meta
        forum_opts = Forum._meta
        forum_table = qn(forum_opts.db_table)
        return self.with_user_details().extra(
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
        """
        is_new = False
        if not self.id:
            self.started_at = datetime.datetime.now()
            is_new = True
        super(Topic, self).save(**kwargs)
        if is_new:
            self.forum.update_topic_count()
            transaction.commit_unless_managed()

    def delete(self):
        """
        This method is overridden to update denormalised data in the
        related ``Forum`` object after a topic has been deleted.
        """
        super(Topic, self).delete()
        self.forum.update_topic_count()
        transaction.commit_unless_managed()

    class Meta:
        ordering = ('-last_post_at', '-started_at')

    class Admin:
        list_display = ('title', 'forum', 'user', 'started_at', 'post_count',
                        'view_count', 'last_post_at', 'locked', 'pinned')
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
                'fields': ('post_count', 'view_count',
                           'last_post_at', 'last_user_id', 'last_username'),
            }),
        )
        search_fields = ('title',)

    @models.permalink
    def get_absolute_url(self):
        return ('forum_topic_detail', (smart_unicode(self.id),))

    def update_post_count(self):
        """
        Executes a simple SQL ``UPDATE`` to update this topic's
        ``post_count``.
        """
        opts = self._meta
        cursor = connection.cursor()
        cursor.execute('UPDATE %s SET %s=%%s WHERE %s=%%s' % (
            qn(opts.db_table), qn(opts.get_field('post_count').column),
            qn(opts.pk.column)), [self.posts.count(), self._get_pk_val()])

    update_post_count.alters_data = True

    def set_last_post(self, post=None):
        """
        Executes a simple SQL ``UPDATE`` to set details about this
        topic's last post and update its ``post_count``.

        If the last post is not given, it will be looked up.
        """
        if post is None:
            post = self.posts.order_by('-posted_at')[0]
        opts = self._meta
        cursor = connection.cursor()
        cursor.execute('UPDATE %s SET %s=%%s, %s=%%s, %s=%%s, %s=%%s WHERE %s=%%s' % (
            qn(opts.db_table), qn(opts.get_field('post_count').column),
            qn(opts.get_field('last_post_at').column),
            qn(opts.get_field('last_user_id').column),
            qn(opts.get_field('last_username').column),
            qn(opts.pk.column)), [self.posts.count(), post.posted_at,
                                  post.user._get_pk_val(), post.user.username,
                                  self._get_pk_val()])

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
            qn(opts.pk.column)), [self.view_count, self._get_pk_val()])
        transaction.commit_unless_managed()

    increment_view_count.alters_data = True

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
                    qn(forum_profile_opts.pk.column),
                    user_table,
                    qn(user_opts.pk.column),
                ),
            ]
        )

    def decrement_num_in_topic(self, topic, start_at):
        """
        Decrements ``num_in_topic`` for all posts in the given topic
        which have a ``num_in_topic`` greater than ``start_at``.
        """
        opts = self.model._meta
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE %(post_table)s
            SET %(num_in_topic)s=%(num_in_topic)s-1
            WHERE %(topic_fk)s=%%s
              AND %(num_in_topic)s>%%s""" % {
                'post_table': qn(opts.db_table),
                'num_in_topic': qn(opts.get_field('num_in_topic').column),
                'topic_fk': qn(opts.get_field('topic').column),
            }, [topic.id, start_at])

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
        self.body_html = post_formatter.format_post_body(self.body)
        is_new = False
        if not self.id:
            self.posted_at = datetime.datetime.now()
            self.num_in_topic = self.topic.post_count + 1
            is_new = True
        else:
            self.edited_at = datetime.datetime.now()
        super(Post, self).save(**kwargs)
        if is_new:
            self.topic.set_last_post(self)
            self.topic.forum.set_last_post(self)
            ForumProfile.objects.get_for_user(self.user).update_post_count()
            transaction.commit_unless_managed()

    def delete(self):
        """
        This method is overridden to update denormalised data in related
        ``Topic``, ``Forum``, ``ForumProfile`` and other ``Post``
        objects after the post has been deleted.

        In the case where the post being deleted is the latest post in
        its topic or forum, it is necessary to replace the denormalised
        data these objects hold about the post with details of the
        next-newest post.
        """
        topic = self.topic
        forum = topic.forum
        forum_profile = ForumProfile.objects.get_for_user(self.user)
        super(Post, self).delete()
        forum_profile.update_post_count()
        if self.posted_at == topic.last_post_at:
            topic.set_last_post()
        if self.posted_at == forum.last_post_at:
            forum.set_last_post()
        self._default_manager.decrement_num_in_topic(topic, self.num_in_topic)
        transaction.commit_unless_managed()

    class Admin:
        list_display = ('__unicode__', 'user', 'topic', 'posted_at',
                        'edited_at', 'user_ip')
        fields = (
            (None, {
                'fields': ('user', 'topic', 'body'),
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
