import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, InvalidPage
from django.core.urlresolvers import reverse
from django.db import connection, transaction
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import loader, RequestContext
from django.utils import simplejson
from django.utils.encoding import smart_unicode
from django.utils.text import capfirst
from django.views.generic.list_detail import object_list

from forum import app_settings
from forum import auth
from forum import forms
from forum import moderation
from forum.formatters import post_formatter
from forum.models import Forum, ForumProfile, Post, Search, Section, Topic

if app_settings.USE_REDIS:
    from forum import redis_connection as redis

qn = connection.ops.quote_name

class TopicURLs(object):
    """
    Handles display of different URLs based on whether or not a topic
    is being viewed in meta mode.
    """
    def __init__(self, topic, meta):
        self.topic = topic
        self.meta = meta

    def topic_detail(self):
        if self.meta:
            return self.topic.get_meta_url()
        else:
            return self.topic.get_absolute_url()

    def add_reply(self):
        url_name = self.meta and 'forum_add_meta_reply' or 'forum_add_reply'
        return reverse(url_name, args=(smart_unicode(self.topic.pk),))

def get_topics_per_page(user):
    """
    Gets the number of Topics which should be displayed per page, based
    on the given User.
    """
    if user.is_authenticated():
        forum_profile = ForumProfile.objects.get_for_user(user)
        return forum_profile.topics_per_page or \
               app_settings.DEFAULT_TOPICS_PER_PAGE
    else:
        return app_settings.DEFAULT_TOPICS_PER_PAGE

def get_posts_per_page(user):
    """
    Gets the number of Posts which should be displayed per page, based
    on the given User.
    """
    if user.is_authenticated():
        forum_profile = ForumProfile.objects.get_for_user(user)
        return forum_profile.posts_per_page or \
               app_settings.DEFAULT_POSTS_PER_PAGE
    else:
        return app_settings.DEFAULT_POSTS_PER_PAGE

def get_avatar_dimensions():
    """
    Creates a string specifying dimensons for User forum avatars. This
    will be the empty string unless the application is configured to
    force avatars to display with particular dimensions.
    """
    if app_settings.MAX_AVATAR_DIMENSIONS is not None and \
       app_settings.FORCE_AVATAR_DIMENSIONS:
        return ' width="%s" height="%s"' % app_settings.MAX_AVATAR_DIMENSIONS
    else:
        return ''

def get_page_or_404(request, paginator, page_param='page'):
    """
    Uses the page specified in the query string of the given request
    (assuming the first page if none is specified) to retrieve a page
    from the given paginator, returning the current page or raising
    ``Http404`` if an invalid page was specified.
    """
    try:
        return paginator.page(int(request.GET.get(page_param, 1)))
    except (ValueError, InvalidPage):
        raise Http404

def permission_denied(request, title='Permission denied',
    message='You do not have permission to perform the requested action.'):
    """
    Returns an HttpResponseForbidden with a permission denied error
    screen.
    """
    return HttpResponseForbidden(loader.render_to_string(
        'forum/permission_denied.html', {
            'title': title,
            'message': message,
        }))

def render(request, template, context, *args, **kwargs):
    """
    Wrapper for ``render_to_response`` which which patches forum context
    variables into template contexts, in lieu of being able to detect
    ``current_app`` in context processors, and always uses
    ``RequestContext``.
    """
    context['redis'] = app_settings.USE_REDIS
    context['nodejs'] = app_settings.USE_NODEJS
    return render_to_response(template, context,
                              context_instance=RequestContext(request))

def forum_index(request):
    """
    Displays a list of Sections and their Forums.
    """
    active_users = None
    if app_settings.USE_REDIS:
        if request.user.is_authenticated():
            redis.seen_user(request.user, 'Viewing forum index')
        active_users = list(redis.get_active_users())
    return render(request, 'forum/forum_index.html', {
        'section_list': list(Section.objects.get_forums_by_section()),
        'title': 'Forum Index',
        'active_users': active_users,
    })

@login_required
def search(request):
    """
    Searches Topics or Posts based on given criteria.
    """
    if request.method == 'POST':
        form = forms.SearchForm(request.POST)
        if form.is_valid():
            results = form.get_queryset().values('id')[:1000]
            search = Search.objects.create(type=form.cleaned_data['search_type'],
                user=request.user,
                criteria_json=simplejson.dumps(form.cleaned_data),
                result_ids=','.join([smart_unicode(result['id']) \
                                      for result in results]))
            return HttpResponseRedirect(search.get_absolute_url())
    else:
        form = forms.SearchForm()
    if app_settings.USE_REDIS:
        redis.seen_user(request.user, 'Searching...')
    return render(request, 'forum/search.html', {
        'form': form,
        'title': 'Search',
    })

@login_required
def search_results(request, search_id):
    """
    Displays Search results.
    """
    search = get_object_or_404(Search, pk=search_id)
    if not auth.user_can_view_search_results(request.user, search):
        return permission_denied(request,
            message='You may only view your own search results.')
    if search.type == Search.POST_SEARCH:
        items_per_page = get_posts_per_page(request.user)
    else:
        items_per_page = get_topics_per_page(request.user)
    search_result_ids = []
    if search.result_ids:
        search_result_ids = search.result_ids.split(',')
    paginator = Paginator(search_result_ids, items_per_page)
    page = get_page_or_404(request, paginator)
    model = search.get_result_model()
    model_name = capfirst(model._meta.verbose_name)
    context = {
        'title': '%s Search Results' % model_name,
        'search': search,
        'object_list': model.objects.with_standalone_details() \
                             .filter(pk__in=page.object_list).order_by('id'),
        'object_name': model_name,
        'is_paginated': paginator.num_pages > 1,
        'has_next': page.has_next(),
        'has_previous': page.has_previous(),
        'page': page.number,
        'next': page.next_page_number(),
        'previous': page.previous_page_number(),
        'pages': paginator.num_pages,
        'hits' : paginator.count,
    }
    if search.type == Search.TOPIC_SEARCH:
        context['posts_per_page'] = get_posts_per_page(request.user)
    if app_settings.USE_REDIS:
        redis.seen_user(request.user, 'Viewing search results')
    return render(request, 'forum/search_results.html', context)

@login_required
@transaction.commit_on_success
def add_section(request):
    """
    Adds a Section.
    """
    if not auth.is_admin(request.user):
        return permission_denied(request)
    sections = list(Section.objects.all())
    if app_settings.USE_REDIS:
        redis.seen_user(request.user, 'Adding a new section')
    if request.method == 'POST':
        form = forms.AddSectionForm(sections, request.POST)
        if form.is_valid():
            if not form.cleaned_data['section']:
                # Add to the end
                order = len(sections) + 1
            else:
                # Insert before an existing Section
                order = Section.objects.get(pk=form.cleaned_data['section']).order
                Section.objects.increment_orders(order)
            section = Section.objects.create(name=form.cleaned_data['name'],
                                             order=order)
            return HttpResponseRedirect(section.get_absolute_url())
    else:
        form = forms.AddSectionForm(sections)
    return render(request, 'forum/add_section.html', {
        'form': form,
        'title': 'Add Section',
    })

def section_detail(request, section_id):
    """
    Displays a particular Section's Forums.
    """
    section = get_object_or_404(Section, pk=section_id)
    if app_settings.USE_REDIS and request.user.is_authenticated():
        redis.seen_user(request.user, 'Viewing:', section)
    return render(request, 'forum/section_detail.html', {
        'section': section,
        'forum_list': section.forums.all(),
        'title': section.name,
    })

@login_required
@transaction.commit_on_success
def edit_section(request, section_id):
    """
    Edits a Section.
    """
    if not auth.is_admin(request.user):
        return permission_denied(request)
    section = get_object_or_404(Section, pk=section_id)
    if app_settings.USE_REDIS:
        redis.seen_user(request.user, 'Editing a section')
    if request.method == 'POST':
        form = forms.EditSectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save(commit=True)
            return HttpResponseRedirect(section.get_absolute_url())
    else:
        form = forms.EditSectionForm(instance=section)
    return render(request, 'forum/edit_section.html', {
        'form': form,
        'section': section,
        'title': 'Edit Section',
    })

@login_required
@transaction.commit_on_success
def delete_section(request, section_id):
    """
    Deletes a Section after confirmation is made via POST.
    """
    if not auth.is_admin(request.user):
        return permission_denied(request)
    section = get_object_or_404(Section, pk=section_id)
    if app_settings.USE_REDIS:
        redis.seen_user(request.user, 'Deleting a section')
    if request.method == 'POST':
        section.delete()
        return HttpResponseRedirect(reverse('forum_index'))
    else:
        return render(request, 'forum/delete_section.html', {
            'section': section,
            'forum_list': section.forums.all(),
            'title': 'Delete Section',
        })

@login_required
@transaction.commit_on_success
def add_forum(request, section_id):
    """
    Adds a Forum to a Section.
    """
    if not auth.is_admin(request.user):
        return permission_denied(request)
    section = get_object_or_404(Section, pk=section_id)
    forums = list(section.forums.all())
    if app_settings.USE_REDIS:
        redis.seen_user(request.user, 'Adding a new forum')
    if request.method == 'POST':
        form = forms.AddForumForm(forums, request.POST)
        if form.is_valid():
            if not form.cleaned_data['forum']:
                # Add to the end
                order = len(forums) + 1
            else:
                # Insert before an existing Forum
                order = Forum.objects.get(pk=form.cleaned_data['forum']).order
                Forum.objects.increment_orders(section.id, order)
            forum = Forum.objects.create(name=form.cleaned_data['name'],
                section=section, order=order,
                description=form.cleaned_data['description'])
            return HttpResponseRedirect(forum.get_absolute_url())
    else:
        form = forms.AddForumForm(forums)
    return render(request, 'forum/add_forum.html', {
        'form': form,
        'section': section,
        'title': 'Add Forum to %s' % section.name,
    })

@login_required
@transaction.commit_on_success
def edit_forum(request, forum_id):
    """
    Edits a Forum.
    """
    if not auth.is_admin(request.user):
        return permission_denied(request)
    forum = get_object_or_404(Forum.objects.select_related(), pk=forum_id)
    if app_settings.USE_REDIS:
        redis.seen_user(request.user, 'Editing a forum')
    if request.method == 'POST':
        form = forms.EditForumForm(request.POST, instance=forum)
        if form.is_valid():
            form.save(commit=True)
            return HttpResponseRedirect(forum.get_absolute_url())
    else:
        form = forms.EditForumForm(instance=forum)
    return render(request, 'forum/edit_forum.html', {
        'form': form,
        'forum': forum,
        'section': forum.section,
        'title': 'Edit Forum',
    })

def forum_detail(request, forum_id):
    """
    Displays a Forum's Topics.
    """
    forum = get_object_or_404(Forum.objects.select_related(), pk=forum_id)
    topic_filters = {
        'forum': forum,
        'pinned': False,
    }
    if not request.user.is_authenticated() or \
       not auth.is_moderator(request.user):
        topic_filters['hidden'] = False
    # Get a page of topics
    topics_per_page = get_topics_per_page(request.user)
    paginator = Paginator(
        Topic.objects.with_user_details().filter(**topic_filters),
        topics_per_page)
    page = get_page_or_404(request, paginator)
    topics = list(page.object_list)
    context = {
        'section': forum.section,
        'forum': forum,
        'topic_list': topics,
        'title': forum.name,
        'posts_per_page': get_posts_per_page(request.user),
        'is_paginated': paginator.num_pages > 1,
        'has_next': page.has_next(),
        'has_previous': page.has_previous(),
        'page': page.number,
        'next': page.next_page_number(),
        'previous': page.previous_page_number(),
        'pages': paginator.num_pages,
        'hits' : paginator.count,
    }
    # Get pinned topics too if we're on the first page and add the
    # current user's last read details to all topics.
    if page.number == 1:
        topic_filters['pinned'] = True
        pinned_topics = list(Topic.objects.with_user_details() \
                                           .filter(**topic_filters) \
                                            .order_by('-started_at'))
        context['pinned_topics'] = pinned_topics
        if app_settings.USE_REDIS:
            Topic.objects.add_last_read_times(topics + pinned_topics, request.user)
            Topic.objects.add_view_counts(topics + pinned_topics)
    elif app_settings.USE_REDIS:
        Topic.objects.add_last_read_times(topics, request.user)
        Topic.objects.add_view_counts(topics)
    if app_settings.USE_REDIS and request.user.is_authenticated():
        redis.seen_user(request.user, 'Viewing:', forum)
    return render(request, 'forum/forum_detail.html', context)

@login_required
@transaction.commit_on_success
def delete_forum(request, forum_id):
    """
    Deletes a Forum after confirmation is made via POST.
    """
    if not auth.is_admin(request.user):
        return permission_denied(request)
    forum = get_object_or_404(Forum.objects.select_related(), pk=forum_id)
    section = forum.section
    if app_settings.USE_REDIS:
        redis.seen_user(request.user, 'Deleting a forum')
    if request.method == 'POST':
        forum.delete()
        return HttpResponseRedirect(section.get_absolute_url())
    else:
        return render(request, 'forum/delete_forum.html', {
            'section': section,
            'forum': forum,
            'topic_count': forum.topics.count(),
            'title': 'Delete Forum',
        })

@login_required
def new_posts(request):
    """
    Displays all Topics which have had new posts in the last fortnight,
    those with newest Posts first.
    """
    filters = {'last_post_at__gte': \
               datetime.date.today() - datetime.timedelta(days=14)}
    if not auth.is_moderator(request.user):
        filters['hidden'] = False
    queryset = Topic.objects.with_forum_and_user_details().filter(
        **filters).order_by('-last_post_at')
    if app_settings.USE_REDIS:
        redis.seen_user(request.user,
                        'Viewing: <a href="%s">New Posts</a>' % reverse('forum_new_posts'))
    return object_list(request, queryset,
        paginate_by=get_topics_per_page(request.user), allow_empty=True,
        template_name='forum/new_posts.html',
        extra_context={
            'title': 'New Posts',
            'posts_per_page': get_posts_per_page(request.user),
        }, template_object_name='topic')

@login_required
@transaction.commit_on_success
def add_topic(request, forum_id):
    """
    Adds a Topic to a Forum.
    """
    forum = get_object_or_404(Forum.objects.select_related(), pk=forum_id)
    preview = None
    if app_settings.USE_REDIS:
        redis.seen_user(request.user, 'Adding a new topic')
    if request.method == 'POST':
        topic_form = forms.AddTopicForm(request.POST)
        post_form = forms.TopicPostForm(request.POST)
        if topic_form.is_valid() and post_form.is_valid():
            if 'preview' in request.POST:
                preview = post_formatter.format_post(
                    post_form.cleaned_data['body'],
                    post_form.cleaned_data['emoticons'])
            elif 'submit' in request.POST:
                topic = topic_form.save(commit=False)
                topic.user = request.user
                topic.forum = forum
                topic.save()
                post = post_form.save(commit=False)
                post.topic = topic
                post.user = request.user
                post.user_ip = request.META['REMOTE_ADDR']
                post.save()
                return HttpResponseRedirect(topic.get_absolute_url())
    else:
        topic_form = forms.AddTopicForm()
        post_form = forms.TopicPostForm()
    return render(request, 'forum/add_topic.html', {
        'topic_form': topic_form,
        'post_form': post_form,
        'section': forum.section,
        'forum': forum,
        'preview': preview,
        'title': 'Add Topic in %s' % forum.name,
        'quick_help_template': post_formatter.QUICK_HELP_TEMPLATE,
    })

def topic_detail(request, topic_id, meta=False):
    """
    Displays a Topic's Posts.
    """
    filters = {'pk': topic_id}
    if not request.user.is_authenticated() or \
       not auth.is_moderator(request.user):
        filters['hidden'] = False
    topic = get_object_or_404(Topic.objects.with_display_details(), **filters)
    if app_settings.USE_REDIS:
        redis.increment_view_count(topic)
        if request.user.is_authenticated():
            redis.update_last_read_time(request.user, topic)
            redis.seen_user(request.user, 'Viewing Topic:', topic)
    return object_list(request,
        Post.objects.with_user_details().filter(topic=topic, meta=meta) \
                                         .order_by('posted_at', 'num_in_topic'),
        paginate_by=get_posts_per_page(request.user), allow_empty=True,
        template_name='forum/topic_detail.html',
        extra_context={
            'topic': topic,
            'title': topic.title,
            'avatar_dimensions': get_avatar_dimensions(),
            'meta': meta,
            'urls': TopicURLs(topic, meta),
            'show_fast_reply': request.user.is_authenticated() and \
                ForumProfile.objects.get_for_user(request.user).auto_fast_reply \
                or False,
        }, template_object_name='post')

@login_required
@transaction.commit_on_success
def edit_topic(request, topic_id):
    """
    Edits the given Topic.

    To avoid regular Users from being shown non-working links, the
    Topic's Forum's denormalised last Post data is also updated when
    necessary after the moderator has made a change to the Topic's
    ``hidden`` status. Post counts and Topic counts will not be
    affected by hiding a Topic - it is assumed this is a temporary
    measure which will either lead to a Topic being cleaned up or
    removed altogether.
    """
    filters = {'pk': topic_id}
    if not auth.is_moderator(request.user):
        filters['hidden'] = False
    topic = get_object_or_404(Topic, **filters)
    forum = Forum.objects.select_related().get(pk=topic.forum_id)
    if not auth.user_can_edit_topic(request.user, topic):
        return permission_denied(request,
            message='You do not have permission to edit this topic.')
    editable_fields = ['title', 'description']
    moderator = auth.is_moderator(request.user)
    if moderator:
        was_hidden = topic.hidden
    if app_settings.USE_REDIS:
        redis.seen_user(request.user, 'Editing Topic:', topic)
    if request.method == 'POST':
        form = forms.EditTopicForm(moderator, request.POST, instance=topic)
        if form.is_valid():
            topic = form.save(commit=True)
            if auth.is_moderator(request.user):
                if topic.hidden and not was_hidden:
                     if forum.last_topic_id == topic.id:
                         # Set the forum's last post to the latest non-hidden
                         # post.
                         forum.set_last_post()
                elif not topic.hidden and was_hidden:
                    # Just in case this topic still holds the last post
                    forum.set_last_post()
            return HttpResponseRedirect(topic.get_absolute_url())
    else:
        form = forms.EditTopicForm(moderator, instance=topic)
    return render(request, 'forum/edit_topic.html', {
        'topic': topic,
        'form': form,
        'section': forum.section,
        'forum': forum,
        'title': 'Edit Topic',
        'quick_help_template': post_formatter.QUICK_HELP_TEMPLATE,
    })

@login_required
@transaction.commit_on_success
def delete_topic(request, topic_id):
    """
    Deletes a Topic after confirmation is made via POST.
    """
    filters = {'pk': topic_id}
    if not auth.is_moderator(request.user):
        filters['hidden'] = False
    topic = get_object_or_404(Topic, **filters)
    post = Post.objects.with_user_details().get(topic=topic, meta=False,
                                                num_in_topic=1)
    if not auth.user_can_edit_topic(request.user, topic):
        return permission_denied(request,
            message='You do not have permission to delete this topic.')
    forum = Forum.objects.select_related().get(pk=topic.forum_id)
    if app_settings.USE_REDIS:
        redis.seen_user(request.user, 'Deleting a Topic')
    if request.method == 'POST':
        topic.delete()
        return HttpResponseRedirect(forum.get_absolute_url())
    else:
        return render(request, 'forum/delete_topic.html', {
            'post': post,
            'topic': topic,
            'forum': forum,
            'section': forum.section,
            'title': 'Delete Topic',
            'avatar_dimensions': get_avatar_dimensions(),
        })

def topic_post_summary(request, topic_id):
    """
    Displays a summary of Users who have posted in the given Topic and
    the number of Posts they have made.
    """
    filters = {'pk': topic_id}
    if not request.user.is_authenticated() or \
       not auth.is_moderator(request.user):
        filters['hidden'] = False
    topic = get_object_or_404(Topic.objects.with_display_details(), **filters)

    post_opts = Post._meta
    post_table = qn(post_opts.db_table)
    meta = qn(post_opts.get_field('meta').column)
    topic_fk = qn(post_opts.get_field('topic').column)
    user_fk = qn(post_opts.get_field('user').column)

    user_opts = User._meta
    user_table = qn(user_opts.db_table)
    user_pk = qn(user_opts.pk.column)

    users = User.objects.extra(
        select={'post_count': """SELECT COUNT(%(post_pk)s)
            FROM %(post)s
            WHERE %(topic_fk)s=%%s
              AND %(user_fk)s=%(user)s.%(user_pk)s
              AND %(meta)s=%%s""" % {
                'post_pk':  qn(post_opts.pk.column),
                'post':     post_table,
                'topic_fk': topic_fk,
                'user_fk':  user_fk,
                'user':     user_table,
                'user_pk':  user_pk,
                'meta':     meta,
            }},
        select_params=[topic.pk, False],
        where=["""%(user)s.%(user_pk)s IN (
            SELECT DISTINCT %(user_fk)s
            FROM %(post)s
            WHERE %(topic_fk)s=%%s
            AND %(meta)s=%%s)""" % {
                'user':     user_table,
                'user_pk':  user_pk,
                'user_fk':  user_fk,
                'post':     post_table,
                'topic_fk': topic_fk,
                'meta':     meta,
            }],
        params=[topic.pk, False],
    ).order_by('-post_count')

    if app_settings.USE_REDIS and request.user.is_authenticated():
        redis.seen_user(request.user, 'Viewing Post Summary for:', topic)
    return render(request, 'forum/topic_post_summary.html', {
        'topic': topic,
        'users': users,
        'title': 'Users who posted in %s' % topic.title,
    })

@login_required
@transaction.commit_on_success
def add_reply(request, topic_id, meta=False, quote_post=None):
    """
    Adds a Post to a Topic.

    If ``quote_post`` is given, the form will be prepopulated with a
    quoted version of the Post's body.
    """
    filters = {'pk': topic_id}
    if not auth.is_moderator(request.user):
        filters['hidden'] = False
    topic = get_object_or_404(Topic, **filters)
    if topic.locked and \
       not auth.is_moderator(request.user):
        return permission_denied(request,
            message='You do not have permission to post in this topic.')
    forum = Forum.objects.select_related().get(pk=topic.forum_id)
    preview = None
    if app_settings.USE_REDIS:
        redis.seen_user(request.user, 'Posting in topic:', topic)
    if request.method == 'POST':
        form = forms.ReplyForm(not meta, request.POST)
        if form.is_valid():
            if 'preview' in request.POST:
                preview = post_formatter.format_post(
                    form.cleaned_data['body'], form.cleaned_data['emoticons'])
            elif 'submit' in request.POST:
                post = form.save(commit=False)
                post.topic = topic
                post.user = request.user
                # Only force the meta attribute if posting in meta mode,
                # as otherwise the user can choose to create a meta post.
                if meta:
                    post.meta = True
                post.user_ip = request.META['REMOTE_ADDR']
                post.save()
                return redirect_to_post(request, post.id, post)
    else:
        initial = {}
        if quote_post is not None:
            initial['body'] = post_formatter.quote_post(quote_post)
        form = forms.ReplyForm(not meta, initial=initial)
    return render(request, 'forum/add_reply.html', {
        'form': form,
        'topic': topic,
        'section': forum.section,
        'forum': forum,
        'topic': topic,
        'preview': preview,
        'meta': meta,
        'urls': TopicURLs(topic, meta),
        'title': 'Add Reply to %s' % topic.title,
        'quick_help_template': post_formatter.QUICK_HELP_TEMPLATE,
    })

@login_required
def quote_post(request, post_id):
    """
    Adds a Post to a Topic, prepopulating the form with a quoted Post.
    """
    post = get_object_or_404(Post, pk=post_id)
    return add_reply(request, post.topic_id, meta=post.meta, quote_post=post)

def redirect_to_post(request, post_id, post=None):
    """
    Redirects to the appropriate Topic page containing the given Post.

    If the Post itself is also given it will not be looked up, saving a
    database query.
    """
    if post is None:
        filters = {'pk': post_id}
        if not request.user.is_authenticated() or \
           not auth.is_moderator(request.user):
            filters['topic__hidden'] = False
        post = get_object_or_404(Post, **filters)
    posts_per_page = get_posts_per_page(request.user)
    page, remainder = divmod(post.num_in_topic, posts_per_page)
    if post.num_in_topic < posts_per_page or remainder != 0:
        page += 1
    url_name = post.meta and 'forum_topic_meta_detail' or 'forum_topic_detail'
    return HttpResponseRedirect('%s?page=%s&#post%s' \
        % (reverse(url_name, args=(smart_unicode(post.topic_id),)),
           page, post_id))

def redirect_to_last_post(request, topic_id):
    """
    Redirects to the last Post in the Topic with the given id.
    """
    try:
        post = Post.objects.filter(topic=topic_id, meta=False) \
                            .order_by('-posted_at', '-id')[0]
    except Post.DoesNotExist:
        raise Http404
    return redirect_to_post(request, post.id, post)

@login_required
def redirect_to_unread_post(request, topic_id):
    """
    Redirects to the first Post in the given Topic since the logged-in
    User last viewed it.

    If the User in question has never viewed the given Topic, redirects
    to the Topic's first page.

    If an unread Post can't be found for whatever reason (if it was
    deleted in the interim period, for example), redirects to the Topic's
    last post instead.
    """
    last_read = None
    if app_settings.USE_REDIS:
        last_read = redis.get_last_read_time(request.user, topic_id)
    if not last_read:
        return topic_detail(request, topic_id)

    try:
        unread_post = \
            Post.objects.filter(topic=topic_id, meta=False,
                                posted_at__gt=last_read) \
                         .order_by('posted_at', 'id')[0]
        return redirect_to_post(request, unread_post.pk, unread_post)
    except IndexError:
        return redirect_to_last_post(request, topic_id)

@login_required
@transaction.commit_on_success
def edit_post(request, post_id):
    """
    Edits the given Post.
    """
    filters = {'pk': post_id}
    if not auth.is_moderator(request.user):
        filters['topic__hidden'] = False
    post = get_object_or_404(Post, **filters)
    topic = post.topic
    if not auth.user_can_edit_post(request.user, post, topic):
        return permission_denied(request,
            message='You do not have permission to edit this post.')
    forum = Forum.objects.select_related().get(pk=topic.forum_id)
    meta_editable = auth.is_moderator(request.user)
    if meta_editable:
        was_meta = post.meta
    preview = None
    if app_settings.USE_REDIS:
        redis.seen_user(request.user, 'Editing a post in:', topic)
    if request.method == 'POST':
        form = forms.ReplyForm(meta_editable, request.POST, instance=post)
        if form.is_valid():
            if 'preview' in request.POST:
                preview = post_formatter.format_post(
                    form.cleaned_data['body'], form.cleaned_data['emoticons'])
            elif 'submit' in request.POST:
                post = form.save(commit=False)
                if auth.is_moderator(request.user):
                    if post.meta and not was_meta:
                        moderation.make_post_meta(post, topic, forum)
                    elif not post.meta and was_meta:
                        moderation.make_post_not_meta(post, topic, forum)
                    else:
                        post.save()
                else:
                    post.save()
                return redirect_to_post(request, post.id, post)
    else:
        form = forms.ReplyForm(meta_editable, instance=post)
    return render(request, 'forum/edit_post.html', {
        'form': form,
        'post': post,
        'topic': topic,
        'forum': forum,
        'section': forum.section,
        'preview': preview,
        'title': 'Edit Post',
        'quick_help_template': post_formatter.QUICK_HELP_TEMPLATE,
    })

@login_required
@transaction.commit_on_success
def delete_post(request, post_id):
    """
    Deletes a Post after deletion is confirmed via POST.

    A request to delete the first post in a Topic is interpreted
    as a request to delete the Topic itself.
    """
    filters = {'pk': post_id}
    if not request.user.is_authenticated() or \
       not auth.is_moderator(request.user):
        filters['topic__hidden'] = False
    post = get_object_or_404(Post.objects.with_user_details(), **filters)
    topic = post.topic
    if not auth.user_can_edit_post(request.user, post, topic):
        return permission_denied(request,
            message='You do not have permission to delete this post.')
    if post.num_in_topic == 1 and not post.meta:
        return delete_topic(request, post.topic_id)
    if app_settings.USE_REDIS:
        redis.seen_user(request.user, 'Deleting a post in:', topic)
    if request.method == 'POST':
        post.delete()
        url = post.meta and topic.get_meta_url() or topic.get_absolute_url()
        return HttpResponseRedirect(url)
    else:
        forum = Forum.objects.select_related().get(pk=topic.forum_id)
        return render(request, 'forum/delete_post.html', {
            'post': post,
            'topic': topic,
            'forum': forum,
            'section': forum.section,
            'title': 'Delete Post',
            'avatar_dimensions': get_avatar_dimensions(),
        })

def user_profile(request, user_id):
    """
    Displays the ForumProfile for the user with the given id.
    """
    forum_user = get_object_or_404(User, pk=user_id)
    try:
        filters = {'user': forum_user}
        if not request.user.is_authenticated() or \
           not auth.is_moderator(request.user):
            filters['hidden'] = False
        recent_topics = Topic.objects.with_forum_details().filter(
            **filters).order_by('-started_at')[:5]
    except IndexError:
        recent_topics = []
    context = {
        'forum_user': forum_user,
        'forum_profile': ForumProfile.objects.get_for_user(forum_user),
        'recent_topics': Topic.objects.add_view_counts(recent_topics),
        'title': 'Forum Profile for %s' % forum_user,
        'avatar_dimensions': get_avatar_dimensions(),
    }
    if app_settings.USE_REDIS:
        last_seen, doing = redis.get_last_seen(forum_user)
        context['last_seen'] = last_seen
        context['doing'] = doing
        if request.user.is_authenticated():
            redis.seen_user(request.user, 'Viewing user profile:', forum_user)
    return render(request, 'forum/user_profile.html', context)

def user_topics(request, user_id):
    """
    Displays Topics created by a given User.
    """
    forum_user = get_object_or_404(User, pk=user_id)
    filters = {'user': forum_user}
    if not request.user.is_authenticated() or \
       not auth.is_moderator(request.user):
        filters['hidden'] = False
    queryset = Topic.objects.with_forum_details().filter(
        **filters).order_by('-started_at')
    if app_settings.USE_REDIS and request.user.is_authenticated():
        redis.seen_user(request.user, 'Viewing topics by:', forum_user)
    return object_list(request, queryset,
        paginate_by=get_topics_per_page(request.user), allow_empty=True,
        template_name='forum/user_topics.html',
        extra_context={
            'forum_user': forum_user,
            'title': 'Topics Started by %s' % forum_user.username,
            'posts_per_page': get_posts_per_page(request.user),
        }, template_object_name='topic')

@login_required
def edit_user_forum_profile(request, user_id):
    """
    Edits public information in a given User's ForumProfile.

    Only moderators may edit a User's title.
    """
    user = get_object_or_404(User, pk=user_id)
    if not auth.user_can_edit_user_profile(request.user, user):
        return permission_denied(request,
            message='You do not have permission to edit this user\'s forum profile.')
    user_profile = ForumProfile.objects.get_for_user(user)
    can_edit_title = auth.is_moderator(request.user)
    if app_settings.USE_REDIS:
        redis.seen_user(request.user, 'Editing User Profile')
    if request.method == 'POST':
        form = forms.UserProfileForm(can_edit_title, request.POST, instance=user_profile)
        if form.is_valid():
            form.save(commit=True)
            return HttpResponseRedirect(user_profile.get_absolute_url())
    else:
        form = forms.UserProfileForm(can_edit_title, instance=user_profile)
    return render(request, 'forum/edit_user_forum_profile.html', {
        'forum_user': user,
        'forum_profile': user_profile,
        'form': form,
        'title': 'Edit Forum Profile',
        'avatar_dimensions': get_avatar_dimensions(),
    })

@login_required
def edit_user_forum_settings(request):
    """
    Edits forum settings in the logged-in User's ForumProfile.
    """
    user_profile = ForumProfile.objects.get_for_user(request.user)
    if app_settings.USE_REDIS:
        redis.seen_user(request.user, 'Editing Forum Settings')
    if request.method == 'POST':
        form = forms.ForumSettingsForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save(commit=True)
            return HttpResponseRedirect(user_profile.get_absolute_url())
    else:
        form = forms.ForumSettingsForm(instance=user_profile)
    return render(request, 'forum/edit_user_forum_settings.html', {
        'user': request.user,
        'forum_profile': user_profile,
        'form': form,
        'title': 'Edit Forum Settings',
    })

def stalk_users(request):
    """
    Realtime monitoring of user activity via Redis and Node.js.
    """
    if app_settings.USE_REDIS and request.user.is_authenticated():
        redis.seen_user(request.user, 'Stalking Users')
    return render(request, 'forum/stalk_users.html', {
        'title': 'Stalk Users',
    })
