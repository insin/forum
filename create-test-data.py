"""
Uses the ORM to create test data.
"""
import datetime
import os
import random

os.environ['DJANGO_SETTINGS_MODULE'] = 'forum.settings'

from django.contrib.auth.models import User
from django.db import transaction

from forum.models import Forum, ForumProfile, Post, Section, Topic

@transaction.commit_on_success
def create_test_data():
    # 3 Users
    admin = User.objects.create_user('admin', 'a@a.com', 'admin')
    admin.first_name = 'Admin'
    admin.last_name = 'User'
    admin.is_staff = True
    admin.is_superuser = True
    admin.save()
    ForumProfile.objects.create(user=admin, group=ForumProfile.ADMIN_GROUP)

    moderator = User.objects.create_user('moderator', 'm@m.com', 'moderator')
    moderator.first_name = 'Moderator'
    moderator.last_name = 'User'
    moderator.save()
    ForumProfile.objects.create(user=moderator, group=ForumProfile.MODERATOR_GROUP)

    user = User.objects.create_user('user', 'u@u.com', 'user')
    user.first_name = 'Test'
    user.last_name = 'User'
    user.save()
    ForumProfile.objects.create(user=user, group=ForumProfile.USER_GROUP)

    users = [admin, moderator, user]

    # 3 Sections
    sections = [Section.objects.create(name='Section %s' % i, order=i) \
                for i in xrange(1, 4)]

    # 3 Forums per Section
    forums = []
    for section in sections:
        forums += [section.forums.create(name='Forum %s' % i, order=i) \
                   for i in xrange(1, 4)]

    # 3 Topics per Forum
    topics = []
    for forum in forums:
        topics += [forum.topics.create(user=users[i-1], title='Topic %s' % i) \
                   for i in xrange(1, 4)]

    # 3 Posts per Topic
    for topic in topics:
        for i in xrange(1, 4):
            topic.posts.create(user=topic.user, body='Post %s' % i)

    # 3 Metaposts per Topic
    for topic in topics:
        for i in xrange(1, 4):
            topic.posts.create(user=topic.user, meta=True, body='Metapost %s' % i)

if __name__ == '__main__':
    create_test_data()
