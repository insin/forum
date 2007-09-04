from django.contrib.auth.models import User
from django.test import TestCase

from forum.models import *

class ModelTestCase(TestCase):
    fixtures = ['testdata.json']

    def test_add_topic(self):
        user = User.objects.get(pk=1)
        forum = Forum.objects.get(pk=1)
        topic = Topic.objects.create(forum=forum, user=user, title='Test Topic 2')

        post = Post.objects.create(topic=topic, user=user, body='Test post.')
        self.assertEquals(post.num_in_topic, 1)
        self.assertNotEquals(post.posted_at, None)
        self.assertNotEquals(post.body_html, '')
        self.assertEquals(post.edited_at, None)

        topic = Topic.objects.get(pk=topic.id)
        self.assertEquals(topic.posts.count(), 1)
        self.assertEquals(topic.post_count, 1)
        self.assertEquals(topic.last_post_at, post.posted_at)
        self.assertEquals(topic.last_user_id, post.user.id)
        self.assertEquals(topic.last_username, post.user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 2)
        self.assertEquals(forum.topic_count, 2)
        self.assertEquals(forum.last_post_at, post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, post.user.id)
        self.assertEquals(forum.last_username, post.user.username)

        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 4)
        self.assertEquals(forum_profile.post_count, 4)

    def test_add_post(self):
        user = User.objects.get(pk=1)
        topic = Topic.objects.get(pk=1)

        post = Post.objects.create(topic=topic, user=user, body='Test post 4.')
        self.assertEquals(post.num_in_topic, 4)
        self.assertNotEquals(post.posted_at, None)
        self.assertNotEquals(post.body_html, '')
        self.assertEquals(post.edited_at, None)

        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.posts.count(), 4)
        self.assertEquals(topic.post_count, 4)
        self.assertEquals(topic.last_post_at, post.posted_at)
        self.assertEquals(topic.last_user_id, post.user.id)
        self.assertEquals(topic.last_username, post.user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 1)
        self.assertEquals(forum.topic_count, 1)
        self.assertEquals(forum.last_post_at, post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, post.user.id)
        self.assertEquals(forum.last_username, post.user.username)

        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 4)
        self.assertEquals(forum_profile.post_count, 4)

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

        last_post = Post.objects.get(pk=3)
        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.posts.count(), 3)
        self.assertEquals(topic.post_count, 3)
        self.assertEquals(topic.last_post_at, last_post.posted_at)
        self.assertEquals(topic.last_user_id, last_post.user.id)
        self.assertEquals(topic.last_username, last_post.user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 1)
        self.assertEquals(forum.topic_count, 1)
        self.assertEquals(forum.last_post_at, last_post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, last_post.user.id)
        self.assertEquals(forum.last_username, last_post.user.username)

        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 3)
        self.assertEquals(forum_profile.post_count, 3)

    def test_delete_last_post_in_topic(self):
        user = User.objects.get(pk=1)
        topic = Topic.objects.get(pk=1)
        post = Post.objects.get(pk=3)
        post.delete()
        previous_post = Post.objects.get(pk=2)

        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.posts.count(), 2)
        self.assertEquals(topic.post_count, 2)
        self.assertEquals(topic.last_post_at, previous_post.posted_at)
        self.assertEquals(topic.last_user_id, previous_post.user.id)
        self.assertEquals(topic.last_username, previous_post.user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 1)
        self.assertEquals(forum.topic_count, 1)
        self.assertEquals(forum.last_post_at, previous_post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, previous_post.user.id)
        self.assertEquals(forum.last_username, previous_post.user.username)

        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 2)
        self.assertEquals(forum_profile.post_count, 2)

    def test_delete_middle_post_in_topic(self):
        user = User.objects.get(pk=1)
        topic = Topic.objects.get(pk=1)
        post = Post.objects.get(pk=2)
        post.delete()
        new_last_post = Post.objects.get(pk=3)
        self.assertEquals(new_last_post.num_in_topic, 2)

        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.posts.count(), 2)
        self.assertEquals(topic.post_count, 2)
        self.assertEquals(topic.last_post_at, new_last_post.posted_at)
        self.assertEquals(topic.last_user_id, new_last_post.user.id)
        self.assertEquals(topic.last_username, new_last_post.user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 1)
        self.assertEquals(forum.topic_count, 1)
        self.assertEquals(forum.last_post_at, new_last_post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, new_last_post.user.id)
        self.assertEquals(forum.last_username, new_last_post.user.username)

        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 2)
        self.assertEquals(forum_profile.post_count, 2)

class ManagerTestCase(TestCase):
    fixtures = ['testdata.json']

    def test_post_manager_with_user_details(self):
        post = Post.objects.with_user_details().get(pk=1)
        forum_profile = ForumProfile.objects.get_for_user(post.user)
        self.assertEquals(post.user_username, post.user.username)
        self.assertEquals(post.user_date_joined, post.user.date_joined)
        self.assertEquals(post.user_title, forum_profile.title)
        self.assertEquals(post.user_avatar, forum_profile.avatar)
        self.assertEquals(post.user_post_count, forum_profile.post_count)
        self.assertEquals(post.user_location, forum_profile.location)
        self.assertEquals(post.user_website, forum_profile.website)

    def test_topic_manager_with_user_details(self):
        topic = Topic.objects.with_user_details().get(pk=1)
        self.assertEquals(topic.user_username, topic.user.username)

    def test_topic_manager_with_forum_and_user_details(self):
        topic = Topic.objects.with_forum_and_user_details().get(pk=1)
        self.assertEquals(topic.user_username, topic.user.username)
        self.assertEquals(topic.forum_name, topic.forum.name)
