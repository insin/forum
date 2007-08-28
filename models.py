import datetime

from django.contrib.auth.models import User
from django.db import connection, models
from django.utils.encoding import smart_unicode
from django.utils.text import truncate_words

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

USER_GROUP_CHOICES = (
    ('U', 'Users'),
    ('M', 'Moderators'),
    ('A', 'Admins'),
)

class ForumProfile(models.Model):
    """
    A user's forum profile.
    """
    user     = models.OneToOneField(User, related_name='forum_profile')
    group    = models.CharField(max_length=1, choices=USER_GROUP_CHOICES, default='U')
    title    = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    avatar   = models.URLField(verify_exists=False, blank=True)
    website  = models.URLField(verify_exists=False, blank=True)

    # Denormalised data
    post_count = models.PositiveIntegerField(default=0)

    objects = ForumProfileManager()

    def __unicode__(self):
        return u'Forum Profile for %s' % self.user

    class Admin:
        list_display = ('user', 'group', 'title', 'location', 'post_count')
        list_filter = ('group',)
        fields = (
            (None, {
                'fields': ('user', 'group', 'title', 'location', 'avatar',
                           'website'),
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
    metapost_count = models.PositiveIntegerField(default=0)
    view_count     = models.PositiveIntegerField(default=0)
    last_post_at   = models.DateTimeField(null=True, blank=True)
    last_user_id   = models.PositiveIntegerField(null=True, blank=True)
    last_username  = models.CharField(max_length=30, blank=True)

    objects = TopicManager()

    def __unicode__(self):
        return self.title

    def save(self, **kwargs):
        is_new = False
        if not self.id:
            self.started_at = datetime.datetime.now()
            is_new = True
        super(Topic, self).save(**kwargs)
        if is_new:
            self.forum.topic_count = self.forum.topics.count()
            self.forum.save()

    class Meta:
        ordering = ('-last_post_at', '-started_at')

    class Admin:
        list_display = ('title', 'forum', 'user', 'started_at', 'post_count',
                        'metapost_count', 'view_count', 'last_post_at',
                        'locked', 'pinned')
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

    objects = PostManager()

    def __unicode__(self):
        return truncate_words(self.body, 25)

    def save(self, **kwargs):
        self.body = self.body.strip()
        self.body_html = post_formatter.format_post_body(self.body)
        is_new = False
        if not self.id:
            self.posted_at = datetime.datetime.now()
            is_new = True
        else:
            self.edited_at = datetime.datetime.now()
        super(Post, self).save(**kwargs)
        if is_new:
            self.topic.post_count = self.topic.posts.count()
            self.topic.last_post_at = self.posted_at
            self.topic.last_user_id = self.user.id
            self.topic.last_username = self.user.username
            self.topic.save()
            forum = self.topic.forum
            forum.last_post_at = self.posted_at
            forum.last_topic_id = self.topic.id
            forum.last_topic_title = self.topic.title
            forum.last_user_id = self.user.id
            forum.last_username = self.user.username
            forum.save()
            forum_profile = ForumProfile.objects.get_for_user(self.user)
            forum_profile.post_count = self.user.posts.count()
            forum_profile.save()

    def delete(self):
        topic = self.topic
        user = self.user
        forum_profile = ForumProfile.objects.get_for_user(self.user)
        super(Post, self).delete()
        topic.post_count = topic.posts.count()
        topic.save()
        forum_profile.post_count = user.posts.count()
        forum_profile.save()

    class Admin:
        list_display = ('__unicode__', 'user', 'topic', 'posted_at',
                        'edited_at')
        search_fields = ('body',)

    @models.permalink
    def get_absolute_url(self):
        return ('forum_redirect_to_post', (smart_unicode(self.id),))

class Metapost(models.Model):
    """
    A post which forms part of a discussion *about* a discussion.

    For example, posts which are about how a discussion is going could
    be considered metaposts.
    """
    user      = models.ForeignKey(User, related_name='metaposts')
    topic     = models.ForeignKey(Topic, related_name='metaposts')
    body      = models.TextField()
    body_html = models.TextField(editable=False)
    posted_at = models.DateTimeField(editable=False)
    edited_at = models.DateTimeField(editable=False, null=True, blank=True)

    objects = PostManager()

    def __unicode__(self):
        return truncate_words(self.body, 25)

    def save(self, **kwargs):
        self.body = self.body.strip()
        self.body_html = post_formatter.format_post_body(self.body)
        is_new = False
        if not self.id:
            self.posted_at = datetime.datetime.now()
            is_new = True
        else:
            self.edited_at = datetime.datetime.now()
        super(Metapost, self).save(**kwargs)
        if is_new:
            self.topic.metapost_count = self.topic.metaposts.count()
            self.topic.save()

    def delete(self):
        topic = self.topic
        super(Metapost, self).delete()
        topic.metapost_count = topic.metaposts.count()
        topic.save()

    class Admin:
        list_display = ('__unicode__', 'user', 'topic', 'posted_at',
                        'edited_at')
        search_fields = ('body',)
