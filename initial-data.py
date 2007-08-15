import datetime
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'forum.settings'

from django.contrib.auth.models import User
from django.db import transaction

from forum.models import Forum, Metapost, Post, Topic, UserProfile

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
def create_initial_data():
    # Users
    admin = User.objects.create_user('admin', 'a@a.com', 'admin')
    admin.first_name = 'Admin'
    admin.last_name = 'User'
    admin.is_staff = True
    admin.is_superuser = True
    admin.save()
    UserProfile.objects.create(user=admin, avatar_url='http://www.jonathanbuchanan.plus.com/images/stipeav.png')

    testuser = User.objects.create_user('testuser', 'tu@tu.com', 'testuser')
    testuser.first_name = 'Test'
    testuser.last_name = 'User'
    testuser.save()
    UserProfile.objects.create(user=testuser)

    # Forums
    discussion = Forum.objects.create(name='Discussion', order=1, description='Blah-de-blah about this, that and the other.')
    off_topic = Forum.objects.create(name='Off Topic', order=2, description='Everything else goes here, or, like, die and stuff. (Will this do?)')

    # Topics + Posts
    re4_wii = Topic.objects.create(title='Resident Evil 4: Wii', description='Heads-a-poppin!', forum=discussion, user=testuser)
    re4_wii.posts.create(user=testuser, body=POST_TEXT)
    re4_wii.metaposts.create(user=testuser, body='I hate topics like this one.')

    sales = Topic.objects.create(title='Official Sales Figures', description='Snorefax.', forum=discussion, user=admin, pinned=True)
    sales.posts.create(user=admin, body=POST_TEXT)
    sales.metaposts.create(user=testuser, body='I hate topics like this one.')

    testing = Topic.objects.create(title='Testing', forum=off_topic, user=admin)
    testing.posts.create(user=admin, body=POST_TEXT)
    testing.metaposts.create(user=testuser, body='I hate topics like this one.')

if __name__ == '__main__':
    create_initial_data()
