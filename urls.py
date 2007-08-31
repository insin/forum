from django.conf.urls.defaults import *

from forum import app_settings

urlpatterns = patterns('forum.views',
    url(r'^$',                                  'forum_index',           name='forum_index'),
    url(r'^newposts/$',                         'new_posts',             name='forum_new_posts'),
    url(r'^forum/(?P<forum_id>\d+)/$',          'forum_detail',          name='forum_detail'),
    url(r'^forum/(?P<forum_id>\d+)/newtopic/$', 'add_topic',             name='forum_add_topic'),
    url(r'^topic/(?P<topic_id>\d+)/$',          'topic_detail',          name='forum_topic_detail'),
    url(r'^topic/(?P<topic_id>\d+)/reply/$',    'add_reply',             name='forum_add_reply'),
    url(r'^topic/(?P<topic_id>\d+)/lastpost/$', 'redirect_to_last_post', name='forum_redirect_to_last_post'),
    url(r'^post/(?P<post_id>\d+)/$',            'redirect_to_post',      name='forum_redirect_to_post'),
    url(r'^post/(?P<post_id>\d+)/edit/$',       'edit_post',             name='forum_edit_post'),
    url(r'^post/(?P<post_id>\d+)/quote/$',      'quote_post',            name='forum_quote_post'),
    url(r'^post/(?P<post_id>\d+)/delete/$',     'delete_post',           name='forum_delete_post'),
    url(r'^user/(?P<user_id>\d+)/$',            'user_profile',          name='forum_user_profile'),
    url(r'^user/(?P<user_id>\d+)/edit/$',       'edit_user_profile',     name='forum_edit_user_profile'),
)

if app_settings.STANDALONE:
    urlpatterns += patterns('',
        (r'accounts/', include('registration.urls')),
        (r'admin/', include('django.contrib.admin.urls')),
    )
