from django.contrib.auth.models import User
from django.test import TestCase

from forum import moderation
from forum.models import Forum, ForumProfile, Post, Section, Topic

class ForumProfileTestCase(TestCase):
    fixtures = ['testdata.json']

    def test_auth_methods(self):
        """
        Verifies authorisation-related instance methods.
        """
        profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(profile.is_admin(), True)
        self.assertEquals(profile.is_moderator(), True)

        profile = ForumProfile.objects.get(pk=2)
        self.assertEquals(profile.is_admin(), False)
        self.assertEquals(profile.is_moderator(), True)

        profile = ForumProfile.objects.get(pk=3)
        self.assertEquals(profile.is_admin(), False)
        self.assertEquals(profile.is_moderator(), False)

class SectionTestCase(TestCase):
    """
    Tests for the Section model:

    - Delete a Section.
    """
    fixtures = ['testdata.json']

    def test_delete_section(self):
        """
        Verifies that deleting a Section has the appropriate effect on
        the ordering of existing Sections and User postcounts.
        """
        section = Section.objects.get(pk=1)
        section.delete()

        self.assertEquals(Section.objects.get(pk=2).order, 1)
        self.assertEquals(Section.objects.get(pk=3).order, 2)

        users = User.objects.filter(pk__in=[1,2,3])
        for user in users:
            forum_profile = ForumProfile.objects.get_for_user(user)
            self.assertEquals(user.posts.count(), 36)
            self.assertEquals(forum_profile.post_count, 36)

class ForumTestCase(TestCase):
    """
    Tests for the Forum model:

    - Delete a Forum.
    """
    fixtures = ['testdata.json']

    def test_delete_forum(self):
        """
        Verifies that deleting a Forum has the appropriate effect on
        the ordering of existing Forums and User postcounts.
        """
        forum = Forum.objects.get(pk=1)
        forum.delete()

        self.assertEquals(Forum.objects.get(pk=2).order, 1)
        self.assertEquals(Forum.objects.get(pk=3).order, 2)

        users = User.objects.filter(pk__in=[1,2,3])
        for user in users:
            forum_profile = ForumProfile.objects.get_for_user(user)
            self.assertEquals(user.posts.count(), 48)
            self.assertEquals(forum_profile.post_count, 48)

class TopicTestCase(TestCase):
    """
    Tests for the Topic model:

    - Add a Topic.
    - Edit a Topic.
    - Delete a Topic.

    The following tests are for appropriate changes to denormalised
    data:

    - Edit the last Topic in a Forum.
    - Delete the last Topic in a Forum.
    """
    fixtures = ['testdata.json']

    def test_add_topic(self):
        """
        Verifies that adding a Topic (and its opening Post) has the
        appropriate effect on denormalised data.
        """
        user = User.objects.get(pk=1)
        forum = Forum.objects.get(pk=1)
        topic = Topic.objects.create(forum=forum, user=user, title='Test Topic')

        post = Post.objects.create(topic=topic, user=user, body='Test Post.')
        self.assertEquals(post.num_in_topic, 1)
        self.assertNotEquals(post.posted_at, None)
        self.assertNotEquals(post.body_html, '')
        self.assertEquals(post.edited_at, None)

        topic = Topic.objects.get(pk=topic.id)
        self.assertEquals(topic.posts.count(), 1)
        self.assertEquals(topic.post_count, 1)
        self.assertEquals(topic.last_post_at, post.posted_at)
        self.assertEquals(topic.last_user_id, post.user_id)
        self.assertEquals(topic.last_username, post.user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 4)
        self.assertEquals(forum.topic_count, 4)
        self.assertEquals(forum.last_post_at, post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, post.user_id)
        self.assertEquals(forum.last_username, post.user.username)

        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 55)
        self.assertEquals(forum_profile.post_count, 55)

    def test_edit_topic(self):
        """
        Verifies that editing the title of a Topic which does *not*
        contain the last Post in its Forum does not affect anything but
        the Topic.
        """
        topic = Topic.objects.get(pk=1)
        topic.title = 'Updated Title'
        topic.save()

        last_post = Post.objects.get(pk=9)
        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 3)
        self.assertEquals(forum.topic_count, 3)
        self.assertEquals(forum.last_post_at, last_post.posted_at)
        self.assertEquals(forum.last_topic_id, last_post.topic.id)
        self.assertEquals(forum.last_topic_title, last_post.topic.title)
        self.assertEquals(forum.last_user_id, last_post.user.id)
        self.assertEquals(forum.last_username, last_post.user.username)

    def test_delete_topic(self):
        """
        Verifies that deleting a Topic has the appropriate effect on
        denormalised data.
        """
        Topic.objects.get(pk=1).delete()

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 2)
        self.assertEquals(forum.topic_count, 2)

        user = User.objects.get(pk=1)
        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 48)
        self.assertEquals(forum_profile.post_count, 48)

    def test_edit_last_topic(self):
        """
        Verifies that editing the title of the Topic which contains the
        last post in a Forum results in the Forum's denormalised data
        being updated appropriately.
        """
        topic = Topic.objects.get(pk=3)
        topic.title = 'Updated Title'
        topic.save()

        last_post = Post.objects.get(pk=9)
        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 3)
        self.assertEquals(forum.topic_count, 3)
        self.assertEquals(forum.last_post_at, last_post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, last_post.user.id)
        self.assertEquals(forum.last_username, last_post.user.username)

    def test_delete_last_post_topic(self):
        """
        Verifies that deleting the Topic which contains the last Post
        in a Forum results in the forum's denormalised last post data
        being updated appropriately.
        """
        topic = Topic.objects.get(pk=3)
        topic.delete()

        last_post = Post.objects.get(pk=6)
        last_topic = Topic.objects.get(pk=2)
        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 2)
        self.assertEquals(forum.topic_count, 2)
        self.assertEquals(forum.last_post_at, last_post.posted_at)
        self.assertEquals(forum.last_topic_id, last_topic.id)
        self.assertEquals(forum.last_topic_title, last_topic.title)
        self.assertEquals(forum.last_user_id, last_post.user.id)
        self.assertEquals(forum.last_username, last_post.user.username)

    def test_delete_last_topic(self):
        """
        Verifies that deleting the last Topic in a Forum results in the
        forum's denormalised last Post data being cleared.
        """
        topics = Topic.objects.filter(pk__in=[1,2,3])
        for topic in topics:
            topic.delete()

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 0)
        self.assertEquals(forum.topic_count, 0)
        self.assertEquals(forum.last_post_at, None)
        self.assertEquals(forum.last_topic_id, None)
        self.assertEquals(forum.last_topic_title, '')
        self.assertEquals(forum.last_user_id, None)
        self.assertEquals(forum.last_username, '')

        users = User.objects.filter(pk__in=[1,2,3])
        for user in users:
            forum_profile = ForumProfile.objects.get_for_user(user)
            self.assertEquals(user.posts.count(), 48)
            self.assertEquals(forum_profile.post_count, 48)

class PostTestCase(TestCase):
    """
    Tests for the Post model:

    - Add a Post.
    - Edit a Post.
    - Delete a Post.

    The following tests are for appropriate changes to denormalised
    data:

    - Delete the last Post in a Topic.
    - Delete the last Post in a Forum.
    """
    fixtures = ['testdata.json']

    def test_add_post(self):
        """
        Verifies that adding a Post to a Topic has the appropriate
        effect on denormalised data.
        """
        user = User.objects.get(pk=1)
        topic = Topic.objects.get(pk=1)

        post = Post.objects.create(topic=topic, user=user, body='Test Post.')
        self.assertEquals(post.num_in_topic, 4)
        self.assertNotEquals(post.posted_at, None)
        self.assertNotEquals(post.body_html, '')
        self.assertEquals(post.edited_at, None)

        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.posts.count(), 7)
        self.assertEquals(topic.post_count, 4)
        self.assertEquals(topic.metapost_count, 3)
        self.assertEquals(topic.last_post_at, post.posted_at)
        self.assertEquals(topic.last_user_id, post.user_id)
        self.assertEquals(topic.last_username, post.user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 3)
        self.assertEquals(forum.topic_count, 3)
        self.assertEquals(forum.last_post_at, post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, post.user_id)
        self.assertEquals(forum.last_username, post.user.username)

        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 55)
        self.assertEquals(forum_profile.post_count, 55)

    def test_edit_post(self):
        """
        Verifies that editing a Post results in appropriate Post fields
        being updated and doesn't have any effect on denormalised data.
        """
        post = Post.objects.get(pk=9)
        post.body = 'Test Post.'
        post.save()
        self.assertEquals(post.num_in_topic, 3)
        self.assertNotEquals(post.posted_at, None)
        self.assertNotEquals(post.edited_at, None)
        self.assertTrue(post.edited_at > post.posted_at)
        self.assertNotEquals(post.body_html, '')

        topic = Topic.objects.get(pk=3)
        self.assertEquals(topic.posts.count(), 6)
        self.assertEquals(topic.post_count, 3)
        self.assertEquals(topic.post_count, 3)
        self.assertEquals(topic.last_post_at, post.posted_at)
        self.assertEquals(topic.last_user_id, post.user_id)
        self.assertEquals(topic.last_username, post.user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 3)
        self.assertEquals(forum.topic_count, 3)
        self.assertEquals(forum.last_post_at, post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, post.user_id)
        self.assertEquals(forum.last_username, post.user.username)

        user = post.user
        forum_profile = ForumProfile.objects.get(pk=3)
        self.assertEquals(user.posts.count(), 54)
        self.assertEquals(forum_profile.post_count, 54)

    def test_delete_post(self):
        """
        Verifies that deleting a Post which is *not* the last Post in
        its topic results in following Posts' position counters being
        decremented appropriately, and that last Post denormalised data
        is unaffected.
        """
        post = Post.objects.get(pk=1)
        post.delete()

        self.assertEquals(Post.objects.get(pk=2).num_in_topic, 1)
        last_post = Post.objects.get(pk=3)
        self.assertEquals(last_post.num_in_topic, 2)

        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.posts.count(), 5)
        self.assertEquals(topic.post_count, 2)
        self.assertEquals(topic.metapost_count, 3)
        self.assertEquals(topic.last_post_at, last_post.posted_at)
        self.assertEquals(topic.last_user_id, last_post.user_id)
        self.assertEquals(topic.last_username, last_post.user.username)

        user = post.user
        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 53)
        self.assertEquals(forum_profile.post_count, 53)

    def test_delete_last_post_in_topic(self):
        """
        Verifies that deleting the last Post in a Topic has the
        appropriate effect on its denormalised data.
        """
        post = Post.objects.get(pk=3)
        post.delete()

        previous_post_in_topic = Post.objects.get(pk=2)
        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.posts.count(), 5)
        self.assertEquals(topic.post_count, 2)
        self.assertEquals(topic.metapost_count, 3)
        self.assertEquals(topic.last_post_at, previous_post_in_topic.posted_at)
        self.assertEquals(topic.last_user_id, previous_post_in_topic.user_id)
        self.assertEquals(topic.last_username, previous_post_in_topic.user.username)

        last_post_in_forum = Post.objects.get(pk=9)
        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 3)
        self.assertEquals(forum.topic_count, 3)
        self.assertEquals(forum.last_post_at, last_post_in_forum.posted_at)
        self.assertEquals(forum.last_topic_id, last_post_in_forum.topic.id)
        self.assertEquals(forum.last_topic_title, last_post_in_forum.topic.title)
        self.assertEquals(forum.last_user_id, last_post_in_forum.user_id)
        self.assertEquals(forum.last_username, last_post_in_forum.user.username)

        user = User.objects.get(pk=1)
        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 53)
        self.assertEquals(forum_profile.post_count, 53)

    def test_delete_last_post_in_forum(self):
        """
        Verifies that deleting the last Post in a Forum has the
        appropriate effect on denormalised data, including Forum and
        Topic last post data being reset appropriately.
        """
        post = Post.objects.get(pk=9)
        post.delete()

        previous_post = Post.objects.get(pk=8)

        topic = Topic.objects.get(pk=3)
        self.assertEquals(topic.posts.count(), 5)
        self.assertEquals(topic.post_count, 2)
        self.assertEquals(topic.metapost_count, 3)
        self.assertEquals(topic.last_post_at, previous_post.posted_at)
        self.assertEquals(topic.last_user_id, previous_post.user_id)
        self.assertEquals(topic.last_username, previous_post.user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 3)
        self.assertEquals(forum.topic_count, 3)
        self.assertEquals(forum.last_post_at, previous_post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, previous_post.user_id)
        self.assertEquals(forum.last_username, previous_post.user.username)

        user = User.objects.get(pk=3)
        forum_profile = ForumProfile.objects.get(pk=3)
        self.assertEquals(user.posts.count(), 53)
        self.assertEquals(forum_profile.post_count, 53)

class MetapostTestCase(TestCase):
    """
    Tests for the Post model when working with Posts flagged as "meta":

    - Add a Metapost.
    - Edit a Metapost.
    - Delete a Metapost.
    """
    fixtures = ['testdata.json']

    def test_add_metapost(self):
        """
        Verifies that adding a meta-Post to a Topic has the appropriate
        effect on denormalised data.
        """
        user = User.objects.get(pk=1)
        topic = Topic.objects.get(pk=1)

        post = Post.objects.create(topic=topic, user=user, meta=True, body='Test Metapost.')
        self.assertEquals(post.num_in_topic, 4)
        self.assertNotEquals(post.posted_at, None)
        self.assertNotEquals(post.body_html, '')
        self.assertEquals(post.edited_at, None)

        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.posts.count(), 7)
        self.assertEquals(topic.post_count, 3)
        self.assertEquals(topic.metapost_count, 4)

        # Verify that the Topic's last post details have not changed
        last_post = Post.objects.get(pk=3)
        self.assertEquals(topic.last_post_at, last_post.posted_at)
        self.assertEquals(topic.last_user_id, last_post.user_id)
        self.assertEquals(topic.last_username, last_post.user.username)

        # Verify that the Forum's last post details have not changed
        last_post = Post.objects.get(pk=9)
        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 3)
        self.assertEquals(forum.topic_count, 3)
        self.assertEquals(forum.last_post_at, last_post.posted_at)
        self.assertEquals(forum.last_topic_id, last_post.topic.id)
        self.assertEquals(forum.last_topic_title, last_post.topic.title)
        self.assertEquals(forum.last_user_id, last_post.user_id)
        self.assertEquals(forum.last_username, last_post.user.username)

        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 55)
        self.assertEquals(forum_profile.post_count, 55)

    def test_edit_metapost(self):
        """
        Verifies that editing a meta-Post results in appropriate Post fields
        being updated and doesn't have any effect on denormalised data.
        """
        post = Post.objects.get(pk=90)
        post.body = 'Test Metapost.'
        post.save()
        self.assertEquals(post.num_in_topic, 3)
        self.assertNotEquals(post.posted_at, None)
        self.assertNotEquals(post.edited_at, None)
        self.assertTrue(post.edited_at > post.posted_at)
        self.assertNotEquals(post.body_html, '')

        topic = Topic.objects.get(pk=3)
        self.assertEquals(topic.posts.count(), 6)
        self.assertEquals(topic.post_count, 3)
        self.assertEquals(topic.post_count, 3)
        last_post = Post.objects.get(pk=9)
        self.assertEquals(topic.last_post_at, last_post.posted_at)
        self.assertEquals(topic.last_user_id, last_post.user_id)
        self.assertEquals(topic.last_username, last_post.user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 3)
        self.assertEquals(forum.topic_count, 3)
        self.assertEquals(forum.last_post_at, last_post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, last_post.user_id)
        self.assertEquals(forum.last_username, last_post.user.username)

        user = post.user
        forum_profile = ForumProfile.objects.get(pk=3)
        self.assertEquals(user.posts.count(), 54)
        self.assertEquals(forum_profile.post_count, 54)

    def test_delete_metapost(self):
        """
        Verifies that deleting a meta-Post only results in the
        appropriate denormalised post count data being updated.
        """
        post = Post.objects.get(pk=82)
        post.delete()

        self.assertEquals(Post.objects.get(pk=1).num_in_topic, 1)
        self.assertEquals(Post.objects.get(pk=2).num_in_topic, 2)
        self.assertEquals(Post.objects.get(pk=3).num_in_topic, 3)
        self.assertEquals(Post.objects.get(pk=83).num_in_topic, 1)
        self.assertEquals(Post.objects.get(pk=84).num_in_topic, 2)

        last_post = Post.objects.get(pk=3)
        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.posts.count(), 5)
        self.assertEquals(topic.post_count, 3)
        self.assertEquals(topic.metapost_count, 2)
        self.assertEquals(topic.last_post_at, last_post.posted_at)
        self.assertEquals(topic.last_user_id, last_post.user_id)
        self.assertEquals(topic.last_username, last_post.user.username)

        user = post.user
        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 53)
        self.assertEquals(forum_profile.post_count, 53)

class ModerationTestCase(TestCase):
    """
    Tests for moderation functions, which can involve large-scale changes
    to data.

    - Make a post into a metapost.
    - Make the last post in a topic/forum into a metapost.
    - Make a metapost into a post.
    - Make a metapost into a post which will become the last post in a
      topic/forum.
    """
    fixtures = ['testdata.json']

    def test_post_to_metapost(self):
        post = Post.objects.get(pk=2)
        post.meta = True
        moderation.make_post_meta(post, post.topic, post.topic.forum)

        self.assertEquals(post.num_in_topic, 1)
        self.assertEquals(Post.objects.get(pk=82).num_in_topic, 2)
        self.assertEquals(Post.objects.get(pk=83).num_in_topic, 3)
        self.assertEquals(Post.objects.get(pk=84).num_in_topic, 4)
        self.assertEquals(Post.objects.get(pk=1).num_in_topic, 1)
        self.assertEquals(Post.objects.get(pk=3).num_in_topic, 2)

        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.post_count, 2)
        self.assertEquals(topic.metapost_count, 4)

    def test_last_post_to_metapost(self):
        post = Post.objects.get(pk=9)
        post.meta = True
        moderation.make_post_meta(post, post.topic, post.topic.forum)

        self.assertEquals(post.num_in_topic, 1)
        self.assertEquals(Post.objects.get(pk=88).num_in_topic, 2)
        self.assertEquals(Post.objects.get(pk=89).num_in_topic, 3)
        self.assertEquals(Post.objects.get(pk=90).num_in_topic, 4)

        topic = Topic.objects.get(pk=3)
        last_post = Post.objects.get(pk=8)
        self.assertEquals(topic.last_post_at, last_post.posted_at)
        self.assertEquals(topic.last_user_id, last_post.user_id)
        self.assertEquals(topic.last_username, last_post.user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.last_post_at, last_post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, last_post.user_id)
        self.assertEquals(forum.last_username, last_post.user.username)

    def test_metapost_to_post(self):
        post = Post.objects.get(pk=83)
        post.meta = False
        moderation.make_post_not_meta(post, post.topic, post.topic.forum)

        self.assertEquals(post.num_in_topic, 4)
        self.assertEquals(Post.objects.get(pk=82).num_in_topic, 1)
        self.assertEquals(Post.objects.get(pk=84).num_in_topic, 2)

        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.post_count, 4)
        self.assertEquals(topic.metapost_count, 2)

        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.last_post_at, post.posted_at)
        self.assertEquals(topic.last_user_id, post.user_id)
        self.assertEquals(topic.last_username, post.user.username)

    def test_metapost_to_last_post(self):
        post = Post.objects.get(pk=90)
        post.meta = False
        moderation.make_post_not_meta(post, post.topic, post.topic.forum)

        self.assertEquals(post.num_in_topic, 4)

        topic = Topic.objects.get(pk=3)
        self.assertEquals(topic.post_count, 4)
        self.assertEquals(topic.metapost_count, 2)
        self.assertEquals(topic.last_post_at, post.posted_at)
        self.assertEquals(topic.last_user_id, post.user_id)
        self.assertEquals(topic.last_username, post.user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.last_post_at, post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, post.user_id)
        self.assertEquals(forum.last_username, post.user.username)

class ManagerTestCase(TestCase):
    """
    Tests for custom Manager methods which add extra data to retrieved
    objects.
    """
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

    def test_post_manager_with_standalone_details(self):
        post = Post.objects.with_standalone_details().get(pk=1)
        forum_profile = ForumProfile.objects.get_for_user(post.user)
        topic = post.topic
        forum = topic.forum
        section = forum.section
        self.assertEquals(post.user_username, post.user.username)
        self.assertEquals(post.user_date_joined, post.user.date_joined)
        self.assertEquals(post.user_title, forum_profile.title)
        self.assertEquals(post.user_avatar, forum_profile.avatar)
        self.assertEquals(post.user_post_count, forum_profile.post_count)
        self.assertEquals(post.user_location, forum_profile.location)
        self.assertEquals(post.user_website, forum_profile.website)
        self.assertEquals(post.topic_title, topic.title)
        self.assertEquals(post.topic_post_count, topic.post_count)
        self.assertEquals(post.forum_id, forum.pk)
        self.assertEquals(post.forum_name, forum.name)
        self.assertEquals(post.section_id, section.pk)
        self.assertEquals(post.section_name, section.name)

    def test_topic_manager_with_user_details(self):
        topic = Topic.objects.with_user_details().get(pk=1)
        self.assertEquals(topic.user_username, topic.user.username)

    def test_topic_manager_with_forum_details(self):
        topic = Topic.objects.with_forum_details().get(pk=1)
        self.assertEquals(topic.forum_name, topic.forum.name)

    def test_topic_manager_with_forum_and_user_details(self):
        topic = Topic.objects.with_forum_and_user_details().get(pk=1)
        self.assertEquals(topic.user_username, topic.user.username)
        self.assertEquals(topic.forum_name, topic.forum.name)
