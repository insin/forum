from django.contrib.auth.models import User
from django.test import TestCase

from forum import auth
from forum.models import Post, Topic

class AuthTestCase(TestCase):
    """
    Tests for the authorisation module.
    """
    fixtures = ['testdata.json']

    def setUp(self):
        """
        Retrieves a user from each user group for convenience.
        """
        self.admin = User.objects.get(pk=1)
        self.moderator = User.objects.get(pk=2)
        self.user = User.objects.get(pk=3)

    def test_is_admin(self):
        """
        Verifies the check for a user having Administrator privileges.
        """
        self.assertTrue(auth.is_admin(self.admin))
        self.assertFalse(auth.is_admin(self.moderator))
        self.assertFalse(auth.is_admin(self.user))

    def test_is_moderator(self):
        """
        Verifies the check for a user having Moderator privileges.
        """
        self.assertTrue(auth.is_moderator(self.admin))
        self.assertTrue(auth.is_moderator(self.moderator))
        self.assertFalse(auth.is_moderator(self.user))

    def test_user_can_edit_post(self):
        """
        Verifies the check for a given user being able to edit a given
        Post.

        Members of the User group may only edit their own Posts if they
        are not in unlocked Topics.
        """
        # Post by admin
        post = Post.objects.get(pk=1)
        topic = post.topic
        self.assertTrue(auth.user_can_edit_post(self.admin, post))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post))
        self.assertFalse(auth.user_can_edit_post(self.user, post))
        self.assertTrue(auth.user_can_edit_post(self.admin, post, topic))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post, topic))
        self.assertFalse(auth.user_can_edit_post(self.user, post, topic))
        topic.locked = True
        self.assertTrue(auth.user_can_edit_post(self.admin, post, topic))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post, topic))
        self.assertFalse(auth.user_can_edit_post(self.user, post, topic))

        # Post by moderator
        post = Post.objects.get(pk=4)
        topic = post.topic
        self.assertTrue(auth.user_can_edit_post(self.admin, post))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post))
        self.assertFalse(auth.user_can_edit_post(self.user, post))
        self.assertTrue(auth.user_can_edit_post(self.admin, post, topic))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post, topic))
        self.assertFalse(auth.user_can_edit_post(self.user, post, topic))
        topic.locked = True
        self.assertTrue(auth.user_can_edit_post(self.admin, post, topic))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post, topic))
        self.assertFalse(auth.user_can_edit_post(self.user, post, topic))

        # Post by user
        post = Post.objects.get(pk=7)
        topic = post.topic
        self.assertTrue(auth.user_can_edit_post(self.admin, post))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post))
        self.assertTrue(auth.user_can_edit_post(self.user, post))
        self.assertTrue(auth.user_can_edit_post(self.admin, post, topic))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post, topic))
        self.assertTrue(auth.user_can_edit_post(self.user, post, topic))
        topic.locked = True
        self.assertTrue(auth.user_can_edit_post(self.admin, post, topic))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post, topic))
        self.assertFalse(auth.user_can_edit_post(self.user, post, topic))

    def test_user_can_edit_topic(self):
        """
        Verifies the check for a given user being able to edit a given
        Topic.

        Members of the User group may only edit their own Topics if they
        are not locked.
        """
        # Topic creeated by admin
        topic = Topic.objects.get(pk=1)
        self.assertTrue(auth.user_can_edit_topic(self.admin, topic))
        self.assertTrue(auth.user_can_edit_topic(self.moderator, topic))
        self.assertFalse(auth.user_can_edit_topic(self.user, topic))
        topic.locked = True
        self.assertTrue(auth.user_can_edit_topic(self.admin, topic))
        self.assertTrue(auth.user_can_edit_topic(self.moderator, topic))
        self.assertFalse(auth.user_can_edit_topic(self.user, topic))

        # Topic created by moderator
        topic = Topic.objects.get(pk=2)
        self.assertTrue(auth.user_can_edit_topic(self.admin, topic))
        self.assertTrue(auth.user_can_edit_topic(self.moderator, topic))
        self.assertFalse(auth.user_can_edit_topic(self.user, topic))
        topic.locked = True
        self.assertTrue(auth.user_can_edit_topic(self.admin, topic))
        self.assertTrue(auth.user_can_edit_topic(self.moderator, topic))
        self.assertFalse(auth.user_can_edit_topic(self.user, topic))

        # Topic created by user
        topic = Topic.objects.get(pk=3)
        self.assertTrue(auth.user_can_edit_topic(self.admin, topic))
        self.assertTrue(auth.user_can_edit_topic(self.moderator, topic))
        self.assertTrue(auth.user_can_edit_topic(self.user, topic))
        topic.locked = True
        self.assertTrue(auth.user_can_edit_topic(self.admin, topic))
        self.assertTrue(auth.user_can_edit_topic(self.moderator, topic))
        self.assertFalse(auth.user_can_edit_topic(self.user, topic))

    def test_user_can_edit_user_profile(self):
        """
        Verifies the check for a given user being able to edit another
        given user's public ForumProfile.

        Members of the User group may only edit their own ForumProfile.
        """
        self.assertTrue(auth.user_can_edit_user_profile(self.admin, self.admin))
        self.assertTrue(auth.user_can_edit_user_profile(self.moderator, self.admin))
        self.assertFalse(auth.user_can_edit_user_profile(self.user, self.admin))

        self.assertTrue(auth.user_can_edit_user_profile(self.admin, self.moderator))
        self.assertTrue(auth.user_can_edit_user_profile(self.moderator, self.moderator))
        self.assertFalse(auth.user_can_edit_user_profile(self.user, self.moderator))

        self.assertTrue(auth.user_can_edit_user_profile(self.admin, self.user))
        self.assertTrue(auth.user_can_edit_user_profile(self.moderator, self.user))
        self.assertTrue(auth.user_can_edit_user_profile(self.user, self.user))