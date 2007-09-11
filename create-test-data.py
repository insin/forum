"""
Uses the Django ORM to create test data for the forum, giving custom
save methods a workout as it does so.
"""
import datetime
import os
import random

os.environ['DJANGO_SETTINGS_MODULE'] = 'forum.settings'

from django.contrib.auth.models import User
from django.db import transaction

from forum.models import Forum, ForumProfile, Post, Section, Topic

POST_TEXT = """
Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Integer facilisis
ligula ac nisl. Phasellus justo justo, ullamcorper id, laoreet eget, pharetra
sit amet, purus. Nullam elementum purus. Quisque convallis vehicula ante.
Nullam varius hendrerit erat. Sed tempor purus eu leo. Cras vitae justo nec est
hendrerit sollicitudin. Duis auctor metus at lectus. Aenean sit amet tortor ac
velit ullamcorper lacinia. Praesent congue viverra lectus. In sit amet nisi at
odio laoreet dignissim. Quisque volutpat odio id felis. Sed hendrerit nunc eget
ipsum. Aenean vel nunc suscipit tellus auctor tincidunt. In hendrerit egestas
dui. Nulla tempus vehicula leo.

Nullam ligula. Phasellus lectus. Pellentesque est lacus, porta id, dictum eu,
egestas id, lorem. Vestibulum nulla mauris, viverra nec, dignissim eu, mollis
faucibus, odio. Suspendisse potenti. Quisque condimentum, tortor ultricies
elementum varius, augue diam commodo neque, sed porttitor elit dui sed nunc.
Pellentesque dignissim elementum urna. Sed eleifend rhoncus dolor. Mauris a
nibh sed ante adipiscing eleifend. Nulla facilisi. Vivamus nec lacus vitae
lacus facilisis gravida. Donec consequat ullamcorper nisl. Nunc suscipit massa
eu libero. Quisque imperdiet. Sed ullamcorper quam in tortor. Etiam venenatis
pede ut erat commodo molestie. Ut metus arcu, facilisis vel, eleifend nec,
hendrerit quis, mauris. Quisque rhoncus rutrum magna.

Nullam euismod orci nec urna. Curabitur luctus lacus a mi. Nullam tellus odio,
ullamcorper ac, interdum id, ullamcorper id, tortor. Integer sollicitudin purus
ac est. Ut nonummy, felis et lacinia iaculis, ipsum enim ornare dolor, eu
feugiat justo arcu non libero. Morbi mollis vestibulum nibh. Nulla sit amet
justo. Donec sollicitudin ante at dolor. Morbi ac mi sit amet sapien vulputate
mollis. Aenean tempor massa et dui.

Curabitur ullamcorper, arcu id nonummy porttitor, turpis justo suscipit diam,
id malesuada augue risus nec augue. Sed molestie. Phasellus tortor magna,
sodales sed, rutrum in, cursus vitae, justo. Ut lacus elit, euismod at,
scelerisque in, fermentum nec, lacus. Donec erat quam, facilisis lobortis,
aliquet mollis, gravida id, turpis. Fusce accumsan, purus ut feugiat ornare,
diam sapien pulvinar enim, vitae rhoncus felis neque sit amet enim. Phasellus
ultrices vulputate nisi. Quisque pellentesque pellentesque enim. Etiam purus
nulla, iaculis vitae, sollicitudin id, gravida in, libero. Vivamus quis nisi
gravida quam sodales iaculis. Suspendisse justo ante, varius vel, fermentum id,
commodo sed, elit. Aenean sed tellus a diam mollis congue. Etiam luctus
faucibus erat.

Sed ut eros. Proin vel elit. Praesent aliquam enim a neque. In ac lorem. Aenean
magna ligula, imperdiet sit amet, scelerisque volutpat, sollicitudin at, augue.
Cras vestibulum velit quis sapien. Aenean magna felis, adipiscing a, dapibus
at, tincidunt eget, leo. Integer fringilla dignissim diam. Duis porttitor
libero nec mauris. Integer nec erat at dolor consectetuer ornare. Nulla
consequat tortor venenatis est. Phasellus auctor mi in arcu.
"""

@transaction.commit_on_success
def create_test_data():
    # Users
    admin = User.objects.create_user('admin', 'a@a.com', 'admin')
    admin.first_name = 'Admin'
    admin.last_name = 'User'
    admin.is_staff = True
    admin.is_superuser = True
    admin.save()
    ForumProfile.objects.create(user=admin, group='A', avatar='http://www.jonathanbuchanan.plus.com/images/stipeav.png')

    moderator = User.objects.create_user('moderator', 'm@m.com', 'moderator')
    moderator.first_name = 'Moderator'
    moderator.last_name = 'User'
    moderator.save()
    ForumProfile.objects.create(user=moderator, group='M', avatar='http://insin.woaf.net/images/dsav.png')

    user = User.objects.create_user('user', 'u@u.com', 'user')
    user.first_name = 'Test'
    user.last_name = 'User'
    user.save()
    ForumProfile.objects.create(user=user, group='U', avatar='http://insin.woaf.net/images/widget.gif')

    users = [admin, moderator, user]

    # Sections
    news = Section.objects.create(name='News', order=1)
    community = Section.objects.create(name='Community', order=2)
    testing = Section.objects.create(name='Testing', order=3)

    # Forums
    announcements = Forum.objects.create(name='Announcements & Feedback', section=news, order=1, description='Forum news and feedback.')
    discussion = Forum.objects.create(name='Gaming Discussion', section=community, order=1)
    off_topic = Forum.objects.create(name='Off Topic', section=community, order=2, description='Everything else goes here.')
    test_pagination = Forum.objects.create(name='Test Pagination', section=testing, order=1, description='Contain lots of Topics and Posts.')
    ideas = Forum.objects.create(name='Forum Feature Ideas', section=testing, order=2, description='Suggest and discuss ideas for lesser-spotted forum features.')

    # Topics + Posts
    for i in xrange(1, 401):
        poster = random.choice(users)
        topic = Topic.objects.create(user=poster, title='Test Topic %s' % i,
                                     description='Test Description %s' % i,
                                     forum=test_pagination)
        topic.posts.create(user=poster, body='Test Topic %s' % i)
    poster = random.choice(users)
    topic = Topic.objects.create(user=poster, title='Test Post Pagination',
                                 description='Contains 400 Posts',
                                 forum=test_pagination)
    topic.posts.create(user=poster, body='Post 1')
    for i in xrange(2, 401):
        topic.posts.create(user=random.choice(users), body='Post %s' % i)

    open_testing = Topic.objects.create(title='Open for testing', forum=announcements, user=admin)
    open_testing.posts.create(user=admin, body=POST_TEXT)

    re4_wii = Topic.objects.create(title='Resident Evil 4: Wii', description='Heads-a-poppin!', forum=discussion, user=user)
    re4_wii.posts.create(user=user, body=POST_TEXT)

    sales = Topic.objects.create(title='Official Sales Figures', description='Snorefax.', forum=discussion, user=admin, pinned=True)
    sales.posts.create(user=admin, body=POST_TEXT)

    testing = Topic.objects.create(title='Test Topic', forum=off_topic, user=admin)
    testing.posts.create(user=admin, body=POST_TEXT)

    idea_data = (
        ('Up/Down Voting on Content', 'Like Reddit gone mad!', "Up/down voting *everywhere*, specifically on users, topics and posts.\n\nFor each type of content voted on, have a configurable lower boundary score in user Forum Settings.\n\nScores under the boundary would result in individual topics and posts, or even *everything* from a specific user being hidden.\n\nLet consensus be your ignore list, if you're crazy enough."),
        ('Forum Types', '', "Each forum could have a \"type\" field, which could affect how everything in that particular forum works.\n\nA \"Discussion Forum\" type would be the default and would be what we're using right now.\n\n**Example:**\n\nA \"Help Forum\" type could have the initial post in each topic displayed on every page, with some kind of kudos points system in place. Each topic would start with `settings.FORUM_INITIAL_TOPIC_KUDOS_POINTS` and the topic starter could award these points to specific posts, and thus to users, within the topic for giving useful answers.\n\nIdeas for uses of kudos points:\n\n1. Total points earned could be displayed in place of post counts in user profiles when viewing a Help Forum, and they would actually *mean* something.\n2. An option to view only the starting post and posts which got kudos points if you just want to see what the useful answers were.\n3. If some people can be convinced to *post* more simply by `post_count += 1`, perhaps they could be convinced to *help* more by `kudos += 10` ;)"),
    )
    for title, description, body in idea_data:
        topic = Topic.objects.create(title=title, description=description, forum=ideas, user=admin)
        topic.posts.create(user=admin, body=body)

if __name__ == '__main__':
    create_test_data()
