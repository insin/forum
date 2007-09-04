from django.contrib.auth.models import User
from django.test import TestCase

from forum.models import *

class ModelTestCase(TestCase):
    fixtures = ['testdata.json']

    def test_add_topic(self):
        user = User.objects.get(pk=1)
        forum = Forum.objects.get(pk=1)
        topic = Topic.objects.create(forum=forum, user=user, title='Test Topic 2')

        post = Post.objects.create(topic=topic, user=user, body='Test post 3.')
        self.assertEquals(post.num_in_topic, 1)
        self.assertNotEquals(post.posted_at, None)
        self.assertNotEquals(post.body_html, '')
        self.assertEquals(post.edited_at, None)

        topic = Topic.objects.get(pk=topic.id)
        self.assertEquals(topic.posts.count(), 1)
        self.assertEquals(topic.post_count, 1)
        self.assertEquals(topic.last_post_at, post.posted_at)
        self.assertEquals(topic.last_user_id, user.id)
        self.assertEquals(topic.last_username, user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 2)
        self.assertEquals(forum.topic_count, 2)
        self.assertEquals(forum.last_post_at, post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, user.id)
        self.assertEquals(forum.last_username, user.username)

        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 3)
        self.assertEquals(forum_profile.post_count, 3)

    def test_add_post(self):
        user = User.objects.get(pk=1)
        topic = Topic.objects.get(pk=1)

        post = Post.objects.create(topic=topic, user=user, body='Test post 3.')
        self.assertEquals(post.num_in_topic, 3)
        self.assertNotEquals(post.posted_at, None)
        self.assertNotEquals(post.body_html, '')
        self.assertEquals(post.edited_at, None)

        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.posts.count(), 3)
        self.assertEquals(topic.post_count, 3)
        self.assertEquals(topic.last_post_at, post.posted_at)
        self.assertEquals(topic.last_user_id, user.id)
        self.assertEquals(topic.last_username, user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 1)
        self.assertEquals(forum.topic_count, 1)
        self.assertEquals(forum.last_post_at, post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, user.id)
        self.assertEquals(forum.last_username, user.username)

        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 3)
        self.assertEquals(forum_profile.post_count, 3)

    def test_edit_post(self):
        user = User.objects.get(pk=1)
        topic = Topic.objects.get(pk=1)

        post = Post.objects.get(pk=2)
        post.body = 'Test editing post 2.'
        post.save()
        self.assertEquals(post.num_in_topic, 2)
        self.assertNotEquals(post.posted_at, None)
        self.assertNotEquals(post.edited_at, None)
        self.assertTrue(post.edited_at > post.posted_at)
        self.assertNotEquals(post.body_html, '')

        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.posts.count(), 2)
        self.assertEquals(topic.post_count, 2)
        self.assertEquals(topic.last_post_at, post.posted_at)
        self.assertEquals(topic.last_user_id, user.id)
        self.assertEquals(topic.last_username, user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 1)
        self.assertEquals(forum.topic_count, 1)
        self.assertEquals(forum.last_post_at, post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, user.id)
        self.assertEquals(forum.last_username, user.username)

        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 2)
        self.assertEquals(forum_profile.post_count, 2)

    def test_delete_post(self):
        user = User.objects.get(pk=1)
        topic = Topic.objects.get(pk=1)
        post = Post.objects.get(pk=2)
        post.delete()
        previous_post = Post.objects.get(pk=1)

        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.posts.count(), 1)
        self.assertEquals(topic.post_count, 1)
        self.assertEquals(topic.last_post_at, previous_post.posted_at)
        self.assertEquals(topic.last_user_id, user.id)
        self.assertEquals(topic.last_username, user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 1)
        self.assertEquals(forum.topic_count, 1)
        self.assertEquals(forum.last_post_at, previous_post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, user.id)
        self.assertEquals(forum.last_username, user.username)

        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 1)
        self.assertEquals(forum_profile.post_count, 1)
