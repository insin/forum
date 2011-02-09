from django.contrib import admin

from forum.models import ForumProfile, Section, Forum, Topic, Post, Search

DENORMALISED_DATA_NOTICE = 'You shouldn\'t need to edit this data manually.'

class ForumProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'title', 'location',
                    'post_count')
    list_filter = ('group',)
    fieldsets = (
        (None, {
            'fields': ('user', 'group', 'title', 'location', 'avatar',
                       'website'),
        }),
        ('Board settings', {
            'fields': ('timezone', 'topics_per_page', 'posts_per_page',
                       'auto_fast_reply'),
        }),
        ('Denormalised data', {
            'classes': ('collapse',),
            'description': DENORMALISED_DATA_NOTICE,
            'fields': ('post_count',),
        }),
    )

class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')

class ForumAdmin(admin.ModelAdmin):
    list_display = ('name', 'section', 'description', 'order',
                    'topic_count', 'locked', 'hidden')
    list_filter = ('section',)
    fieldsets = (
        (None, {
            'fields': ('name', 'section', 'description', 'order'),
        }),
        ('Administration', {
            'fields': ('locked', 'hidden'),
        }),
        ('Denormalised data', {
            'classes': ('collapse',),
            'description': DENORMALISED_DATA_NOTICE,
            'fields': ('topic_count', 'last_post_at', 'last_topic_id',
                       'last_topic_title','last_user_id', 'last_username'),
        }),
    )
    search_fields = ('name',)

class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'forum', 'user', 'started_at', 'post_count',
                    'metapost_count', 'last_post_at', 'locked', 'pinned',
                    'hidden')
    list_filter = ('forum', 'locked', 'pinned', 'hidden')
    fieldsets = (
        (None, {
            'fields': ('title', 'forum', 'user', 'description'),
        }),
        ('Administration', {
            'fields': ('pinned', 'locked', 'hidden'),
        }),
        ('Denormalised data', {
            'classes': ('collapse',),
            'description': DENORMALISED_DATA_NOTICE,
            'fields': ('post_count', 'metapost_count', 'last_post_at',
                       'last_user_id', 'last_username'),
        }),
    )
    search_fields = ('title',)

class PostAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'user', 'topic', 'meta', 'posted_at',
                    'edited_at', 'user_ip')
    list_filter = ('meta',)
    fieldsets = (
        (None, {
            'fields': ('user', 'topic', 'body', 'meta', 'emoticons'),
        }),
        ('Denormalised data', {
            'classes': ('collapse',),
            'description': DENORMALISED_DATA_NOTICE,
            'fields': ('num_in_topic',),
        }),
    )
    search_fields = ('body',)

class SearchAdmin(admin.ModelAdmin):
    list_display = ('type', 'user', 'searched_at')
    list_filter = ('type',)

admin.site.register(ForumProfile, ForumProfileAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Forum, ForumAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Search, SearchAdmin)
