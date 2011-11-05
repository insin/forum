from django.conf.urls.defaults import *
from django.conf import settings

from forum import app_settings

urlpatterns = patterns('forum.views',
    url(r'^$',                                           'forum_index',              name='forum_index'),
    url(r'^search/$',                                    'search',                   name='forum_search'),
    url(r'^search_results/(?P<search_id>\d+)/$',         'search_results',           name='forum_search_results'),
    url(r'^new_posts/$',                                 'new_posts',                name='forum_new_posts'),
    url(r'^stalk_users/$',                               'stalk_users',              name='forum_stalk_users'),
    url(r'^add_section/$',                               'add_section',              name='forum_add_section'),
    url(r'^section/(?P<section_id>\d+)/$',               'section_detail',           name='forum_section_detail'),
    url(r'^section/(?P<section_id>\d+)/edit/$',          'edit_section',             name='forum_edit_section'),
    url(r'^section/(?P<section_id>\d+)/delete/$',        'delete_section',           name='forum_delete_section'),
    url(r'^section/(?P<section_id>\d+)/add_forum/$',     'add_forum',                name='forum_add_forum'),
    url(r'^forum/(?P<forum_id>\d+)/$',                   'forum_detail',             name='forum_forum_detail'),
    url(r'^forum/(?P<forum_id>\d+)/edit/$',              'edit_forum',               name='forum_edit_forum'),
    url(r'^forum/(?P<forum_id>\d+)/delete/$',            'delete_forum',             name='forum_delete_forum'),
    url(r'^forum/(?P<forum_id>\d+)/add_topic/$',         'add_topic',                name='forum_add_topic'),
    url(r'^topic/(?P<topic_id>\d+)/$',                   'topic_detail',             {'meta': False}, name='forum_topic_detail'),
    url(r'^topic/(?P<topic_id>\d+)/edit/$',              'edit_topic',               name='forum_edit_topic'),
    url(r'^topic/(?P<topic_id>\d+)/reply/$',             'add_reply',                {'meta': False}, name='forum_add_reply'),
    url(r'^topic/(?P<topic_id>\d+)/last_post/$',         'redirect_to_last_post',    name='forum_redirect_to_last_post'),
    url(r'^topic/(?P<topic_id>\d+)/unread_post/$',       'redirect_to_unread_post',  name='forum_redirect_to_unread_post'),
    url(r'^topic/(?P<topic_id>\d+)/delete/$',            'delete_topic',             name='forum_delete_topic'),
    url(r'^topic/(?P<topic_id>\d+)/meta/$',              'topic_detail',             {'meta': True}, name='forum_topic_meta_detail'),
    url(r'^topic/(?P<topic_id>\d+)/meta/reply/$',        'add_reply',                {'meta': True}, name='forum_add_meta_reply'),
    url(r'^topic/(?P<topic_id>\d+)/summary/$',           'topic_post_summary',       name='forum_topic_post_summary'),
    url(r'^post/(?P<post_id>\d+)/$',                     'redirect_to_post',         name='forum_redirect_to_post'),
    url(r'^post/(?P<post_id>\d+)/edit/$',                'edit_post',                name='forum_edit_post'),
    url(r'^post/(?P<post_id>\d+)/quote/$',               'quote_post',               name='forum_quote_post'),
    url(r'^post/(?P<post_id>\d+)/delete/$',              'delete_post',              name='forum_delete_post'),
    url(r'^user/(?P<user_id>\d+)/$',                     'user_profile',             name='forum_user_profile'),
    url(r'^user/(?P<user_id>\d+)/topics/$',              'user_topics',              name='forum_user_topics'),
    url(r'^user/(?P<user_id>\d+)/edit_profile/$',        'edit_user_forum_profile',  name='forum_edit_user_forum_profile'),
    url(r'^user/edit_forum_settings/$',                  'edit_user_forum_settings', name='forum_edit_user_forum_settings'),
)

if app_settings.STANDALONE:
    from django.contrib import admin
    admin.autodiscover()
    urlpatterns += patterns('',
        (r'^accounts/', include('registration.backends.default.urls')),
        (r'^admin/', include(admin.site.urls)),
    )

