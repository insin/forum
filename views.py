import datetime

from django import newforms as forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import ObjectPaginator, InvalidPage
from django.core.urlresolvers import reverse
from django.db import connection, transaction
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.encoding import smart_unicode
from django.views.generic.list_detail import object_list

from forum import app_settings
from forum import auth
from forum import moderation
from forum.formatters import post_formatter
from forum.forms import (EditSectionBaseForm, ForumForm, SectionForm,
    forum_profile_formfield_callback, post_formfield_callback,
    topic_formfield_callback)
from forum.models import Forum, ForumProfile, Post, Section, Topic, TopicTracker

qn = connection.ops.quote_name

###################
# Utility Classes #
###################

class TopicURLs:
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

#####################
# Utility Functions #
#####################

def get_topics_per_page(user):
    """
    Gets the number of Topics which should be displayed per page, based
    on the given user.
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
    on the given user.
    """
    if user.is_authenticated():
        forum_profile = ForumProfile.objects.get_for_user(user)
        return forum_profile.posts_per_page or \
               app_settings.DEFAULT_POSTS_PER_PAGE
    else:
        return app_settings.DEFAULT_POSTS_PER_PAGE

def get_avatar_dimensions():
    """
    Creates a string specifying dimensons for user avatars. This will be
    the empty string unless the forum is configured to force avatars to
    display with particular dimensions.
    """
    if app_settings.MAX_AVATAR_DIMENSIONS is not None and \
       app_settings.FORCE_AVATAR_DIMENSIONS:
        return u' width="%s" height="%s"' % app_settings.MAX_AVATAR_DIMENSIONS
    else:
        return u''

##################
# View Functions #
##################

def forum_index(request):
    """
    Displays a list of Sections and their Forums.
    """
    return render_to_response('forum/forum_index.html', {
        'section_list': list(Section.objects.get_forums_by_section()),
        'title': u'Forum Index',
    }, context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success
def add_section(request):
    """
    Adds a Section.
    """
    if not auth.is_admin(request.user):
        return HttpResponseForbidden()
    sections = list(Section.objects.all())
    if request.method == 'POST':
        form = SectionForm(sections, data=request.POST)
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
        form = SectionForm(sections)
    return render_to_response('forum/add_section.html', {
        'form': form,
        'title': u'Add Section',
    }, context_instance=RequestContext(request))

def section_detail(request, section_id):
    """
    Displays a particular Section's Forums.
    """
    section = get_object_or_404(Section, pk=section_id)
    return render_to_response('forum/section_detail.html', {
        'section': section,
        'forum_list': section.forums.all(),
        'title': section.name,
    }, context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success
def edit_section(request, section_id):
    """
    Edits a Section.
    """
    if not auth.is_admin(request.user):
        return HttpResponseForbidden()
    section = get_object_or_404(Section, pk=section_id)
    SectionForm = forms.form_for_instance(section, fields=('name',),
        form=EditSectionBaseForm)
    if request.method == 'POST':
        form = SectionForm(data=request.POST)
        if form.is_valid():
            form.save(commit=True)
            return HttpResponseRedirect(section.get_absolute_url())
    else:
        form = SectionForm()
    return render_to_response('forum/edit_section.html', {
        'form': form,
        'section': section,
        'title': u'Edit Section',
    }, context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success
def delete_section(request, section_id):
    """
    Deletes a Section after confirmation is made via POST.
    """
    if not auth.is_admin(request.user):
        return HttpResponseForbidden()
    section = get_object_or_404(Section, pk=section_id)
    if request.method == 'POST':
        section.delete()
        return HttpResponseRedirect(reverse('forum_index'))
    else:
        return render_to_response('forum/delete_section.html', {
            'section': section,
            'forum_list': section.forums.all(),
            'title': u'Delete Topic',
        }, context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success
def add_forum(request, section_id):
    """
    Adds a Forum to a Section.
    """
    if not auth.is_admin(request.user):
        return HttpResponseForbidden()
    section = get_object_or_404(Section, pk=section_id)
    forums = list(section.forums.all())
    if request.method == 'POST':
        form = ForumForm(forums, data=request.POST)
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
        form = ForumForm(forums)
    return render_to_response('forum/add_forum.html', {
        'form': form,
        'section': section,
        'title': u'Add Forum to %s' % section.name,
    }, context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success
def edit_forum(request, forum_id):
    """
    Edits a Forum.
    """
    if not auth.is_admin(request.user):
        return HttpResponseForbidden()
    forum = get_object_or_404(Forum.objects.select_related(), pk=forum_id)
    ForumForm = forms.form_for_instance(forum, fields=('name', 'description'))
    if request.method == 'POST':
        form = ForumForm(data=request.POST)
        if form.is_valid():
            form.save(commit=True)
            return HttpResponseRedirect(forum.get_absolute_url())
    else:
        form = ForumForm()
    return render_to_response('forum/edit_forum.html', {
        'form': form,
        'forum': forum,
        'section': forum.section,
        'title': u'Edit Forum',
    }, context_instance=RequestContext(request))

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
    paginator = ObjectPaginator(
        Topic.objects.with_user_details().filter(**topic_filters),
        topics_per_page)
    page = request.GET.get('page', 1)
    try:
        page_number = int(page)
    except ValueError:
        raise Http404
    try:
        topics = list(paginator.get_page(page_number - 1))
    except InvalidPage:
        if page_number == 1:
            topics = []
        else:
            raise Http404
    context = {
        'section': forum.section,
        'forum': forum,
        'topic_list': topics,
        'title': forum.name,
        'posts_per_page': get_posts_per_page(request.user),
        'is_paginated': paginator.pages > 1,
        'results_per_page': topics_per_page,
        'has_next': paginator.has_next_page(page_number - 1),
        'has_previous': paginator.has_previous_page(page_number - 1),
        'page': page_number,
        'next': page_number + 1,
        'previous': page_number - 1,
        'last_on_page': paginator.last_on_page(page_number - 1),
        'first_on_page': paginator.first_on_page(page_number - 1),
        'pages': paginator.pages,
        'hits' : paginator.hits,
    }
    # Get pinned topics too if we're on the first page
    if page_number == 1:
        topic_filters['pinned'] = True
        pinned_topics = list(Topic.objects.with_user_details() \
                                           .filter(**topic_filters) \
                                            .order_by('-started_at'))
        context['pinned_topics'] = pinned_topics
    # Add the current user's last read details to topics
    if page_number == 1:
        TopicTracker.objects.add_last_read_to_topics(topics + pinned_topics,
                                                     request.user)
    else:
        TopicTracker.objects.add_last_read_to_topics(topics, request.user)
    return render_to_response('forum/forum_detail.html', context,
        context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success
def delete_forum(request, forum_id):
    """
    Deletes a Forum after confirmation is made via POST.
    """
    if not auth.is_admin(request.user):
        return HttpResponseForbidden()
    forum = get_object_or_404(Forum.objects.select_related(), pk=forum_id)
    section = forum.section
    if request.method == 'POST':
        forum.delete()
        return HttpResponseRedirect(section.get_absolute_url())
    else:
        return render_to_response('forum/delete_forum.html', {
            'section': section,
            'forum': forum,
            'topic_count': forum.topics.count(),
            'title': u'Delete Forum',
        }, context_instance=RequestContext(request))


@login_required
def new_posts(request):
    """
    Displays Topics containing new posts since the current User's last
    login.
    """
    filters = {'last_post_at__gte': request.user.last_login}
    if not auth.is_moderator(request.user):
        filters['hidden'] = False
    queryset = Topic.objects.with_forum_and_user_details().filter(
        **filters).order_by('-last_post_at')
    return object_list(request, queryset,
        paginate_by=get_topics_per_page(request.user), allow_empty=True,
        template_name='forum/new_posts.html',
        extra_context={
            'title': u'New Posts',
            'posts_per_page': get_posts_per_page(request.user),
        }, template_object_name='topic')

@login_required
@transaction.commit_on_success
def add_topic(request, forum_id):
    """
    Adds a Topic to a Forum.
    """
    forum = get_object_or_404(Forum.objects.select_related(), pk=forum_id)
    TopicForm = forms.form_for_model(Topic, fields=('title', 'description'),
        formfield_callback=topic_formfield_callback)
    PostForm = forms.form_for_model(Post, fields=('body',),
        formfield_callback=post_formfield_callback)
    preview = None
    if request.method == 'POST':
        topic_form = TopicForm(data=request.POST)
        post_form = PostForm(data=request.POST)
        if topic_form.is_valid() and post_form.is_valid():
            if 'preview' in request.POST:
                preview = post_formatter.format_post_body(post_form.cleaned_data['body'])
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
        topic_form = TopicForm()
        post_form = PostForm()
    return render_to_response('forum/add_topic.html', {
        'topic_form': topic_form,
        'post_form': post_form,
        'section': forum.section,
        'forum': forum,
        'preview': preview,
        'title': u'Add Topic in %s' % forum.name,
        'quick_help_template': post_formatter.QUICK_HELP_TEMPLATE,
    }, context_instance=RequestContext(request))

@transaction.commit_manually
def topic_detail(request, topic_id, meta=False):
    """
    Displays a Topic's Posts.
    """
    filters = {'pk': topic_id}
    if not request.user.is_authenticated() or \
       not auth.is_moderator(request.user):
        filters['hidden'] = False
    topic = get_object_or_404(Topic.objects.with_display_details(), **filters)
    topic.increment_view_count()
    if request.user.is_authenticated():
        last_read = datetime.datetime.now()
        tracker, created = \
            TopicTracker.objects.get_or_create(user=request.user, topic=topic,
                                               defaults={'last_read': last_read})
        if not created:
            tracker.update_last_read(last_read)
    transaction.commit()
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

    To avoid regular users from being shown non-working links, the
    Topic's Forum's denormalised last post data is also updated when
    necessary after the moderator has made a change to the Topic's
    ``hidden`` status. Post counts and topic counts will not be
    affected by hiding a Topic - it is assumed that this is a temporary
    measure which will either lead to a Topic being cleaned up or
    removed altogether.
    """
    filters = {'pk': topic_id}
    if not auth.is_moderator(request.user):
        filters['hidden'] = False
    topic = get_object_or_404(Topic, **filters)
    forum = Forum.objects.select_related().get(pk=topic.forum_id)
    if not auth.user_can_edit_topic(request.user, topic):
        return HttpResponseForbidden()
    editable_fields = ['title', 'description']
    if auth.is_moderator(request.user):
        editable_fields += ['pinned', 'locked', 'hidden']
        was_hidden = topic.hidden
    TopicForm = forms.form_for_instance(topic, fields=editable_fields,
        formfield_callback=topic_formfield_callback)
    if request.method == 'POST':
        form = TopicForm(data=request.POST)
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
        form = TopicForm()
    return render_to_response('forum/edit_topic.html', {
        'topic': topic,
        'form': form,
        'section': forum.section,
        'forum': forum,
        'title': u'Edit Topic',
        'quick_help_template': post_formatter.QUICK_HELP_TEMPLATE,
    }, context_instance=RequestContext(request))

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
    post = Post.objects.with_user_details().get(topic=topic, num_in_topic=1)
    if not auth.user_can_edit_topic(request.user, topic):
        return HttpResponseForbidden()
    forum = Forum.objects.select_related().get(pk=topic.forum_id)
    if request.method == 'POST':
        topic.delete()
        return HttpResponseRedirect(forum.get_absolute_url())
    else:
        return render_to_response('forum/delete_topic.html', {
            'post': post,
            'topic': topic,
            'forum': forum,
            'section': forum.section,
            'title': u'Delete Topic',
            'avatar_dimensions': get_avatar_dimensions(),
        }, context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success
def add_reply(request, topic_id, meta=False, quote_post=None):
    """
    Adds a Post to a Topic.

    If ``quote_post`` is given, the form will be prepopulated with a
    quoted version of the post's body.
    """
    filters = {'pk': topic_id}
    if not auth.is_moderator(request.user):
        filters['hidden'] = False
    topic = get_object_or_404(Topic, **filters)
    if topic.locked and \
       not auth.is_moderator(request.user):
        return HttpResponseForbidden()
    forum = Forum.objects.select_related().get(pk=topic.forum_id)
    editable_fields = ['body']
    if not meta:
        editable_fields += ['meta']
    PostForm = forms.form_for_model(Post, fields=editable_fields,
        formfield_callback=post_formfield_callback)
    preview = None
    if request.method == 'POST':
        form = PostForm(data=request.POST)
        if form.is_valid():
            if 'preview' in request.POST:
                preview = post_formatter.format_post_body(form.cleaned_data['body'])
            elif 'submit' in request.POST:
                post = form.save(commit=False)
                post.topic = topic
                post.user = request.user
                if meta:
                    post.meta = True
                post.user_ip = request.META['REMOTE_ADDR']
                post.save()
                return redirect_to_post(request, post.id, post)
    else:
        initial = {}
        if quote_post is not None:
            initial['body'] = post_formatter.quote_post(quote_post)
        form = PostForm(initial=initial)
    return render_to_response('forum/add_reply.html', {
        'form': form,
        'topic': topic,
        'section': forum.section,
        'forum': forum,
        'topic': topic,
        'preview': preview,
        'meta': meta,
        'urls': TopicURLs(topic, meta),
        'title': u'Add Reply to %s' % topic.title,
        'quick_help_template': post_formatter.QUICK_HELP_TEMPLATE,
    }, context_instance=RequestContext(request))

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
        post = Post.objects.filter(topic=topic_id).order_by('-posted_at')[0]
    except Post.DoesNotExist:
        raise Http404
    return redirect_to_post(request, post.id, post)

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
        return HttpResponseForbidden()
    forum = Forum.objects.select_related().get(pk=topic.forum_id)
    editable_fields = ['body']
    if auth.is_moderator(request.user):
        editable_fields += ['meta']
        was_meta = post.meta
    PostForm = forms.form_for_instance(post, fields=editable_fields,
        formfield_callback=post_formfield_callback)
    preview = None
    if request.method == 'POST':
        form = PostForm(data=request.POST)
        if form.is_valid():
            if 'preview' in request.POST:
                preview = post_formatter.format_post_body(form.cleaned_data['body'])
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
        form = PostForm()
    return render_to_response('forum/edit_post.html', {
        'form': form,
        'post': post,
        'topic': topic,
        'forum': forum,
        'section': forum.section,
        'preview': preview,
        'title': u'Edit Post',
        'quick_help_template': post_formatter.QUICK_HELP_TEMPLATE,
    }, context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success
def delete_post(request, post_id):
    """
    Deletes a Post after deletion is confirmed via POST.

    A request to delete the first post in a Topic is interpreted
    as a request to delete the topic itself.
    """
    filters = {'pk': post_id}
    if not request.user.is_authenticated() or \
       not auth.is_moderator(request.user):
        filters['topic__hidden'] = False
    post = get_object_or_404(Post.objects.with_user_details(), **filters)
    topic = post.topic
    if not auth.user_can_edit_post(request.user, post, topic):
        return HttpResponseForbidden()
    if post.num_in_topic == 1:
        return delete_topic(request, post.topic_id)
    if request.method == 'POST':
        post.delete()
        url = post.meta and topic.get_meta_url() or topic.get_absolute_url()
        return HttpResponseRedirect(url)
    else:
        forum = Forum.objects.select_related().get(pk=topic.forum_id)
        return render_to_response('forum/delete_post.html', {
            'post': post,
            'topic': topic,
            'forum': forum,
            'section': forum.section,
            'title': u'Delete Post',
            'avatar_dimensions': get_avatar_dimensions(),
        }, context_instance=RequestContext(request))

def user_profile(request, user_id):
    """
    Displays the Forum Profile for the user with the given id.
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
    return render_to_response('forum/user_profile.html', {
        'forum_user': forum_user,
        'forum_profile': ForumProfile.objects.get_for_user(forum_user),
        'recent_topics': recent_topics,
        'title': u'Forum Profile for %s' % forum_user,
        'avatar_dimensions': get_avatar_dimensions(),
    }, context_instance=RequestContext(request))

def user_topics(request, user_id):
    """
    Displays topics created by a given User.
    """
    forum_user = get_object_or_404(User, pk=user_id)
    filters = {'user': forum_user}
    if not request.user.is_authenticated() or \
       not auth.is_moderator(request.user):
        filters['hidden'] = False
    queryset = Topic.objects.with_forum_details().filter(
        **filters).order_by('-started_at')
    return object_list(request, queryset,
        paginate_by=get_topics_per_page(request.user), allow_empty=True,
        template_name='forum/user_topics.html',
        extra_context={
            'forum_user': forum_user,
            'title': u'Topics Started by %s' % forum_user.username,
            'posts_per_page': get_posts_per_page(request.user),
        }, template_object_name='topic')

@login_required
def edit_user_forum_profile(request, user_id):
    """
    Edits public information in a given User's Forum Profile.

    Only moderators may edit a User's title.
    """
    user = get_object_or_404(User, pk=user_id)
    if not auth.user_can_edit_user_profile(request.user, user):
        return HttpResponseForbidden()
    user_profile = ForumProfile.objects.get_for_user(user)
    editable_fields = ['location', 'avatar', 'website']
    if auth.is_moderator(request.user):
        editable_fields.insert(0, 'title')
    ForumProfileForm = forms.form_for_instance(user_profile,
        formfield_callback=forum_profile_formfield_callback,
        fields=editable_fields)
    if request.method == 'POST':
        form = ForumProfileForm(data=request.POST)
        if form.is_valid():
            form.save(commit=True)
            return HttpResponseRedirect(user_profile.get_absolute_url())
    else:
        form = ForumProfileForm()
    return render_to_response('forum/edit_user_forum_profile.html', {
        'forum_user': user,
        'forum_profile': user_profile,
        'form': form,
        'title': 'Edit Forum Profile',
        'avatar_dimensions': get_avatar_dimensions(),
    }, context_instance=RequestContext(request))

@login_required
def edit_user_forum_settings(request, user_id):
    """
    Edits private forum settings in a given User's Forum Profile.
    """
    user = get_object_or_404(User, pk=user_id)
    if request.user.id != user.id:
        return HttpResponseForbidden()
    user_profile = ForumProfile.objects.get_for_user(user)
    ForumSettingsForm = forms.form_for_instance(user_profile,
        fields=['timezone', 'topics_per_page', 'posts_per_page',
                'auto_fast_reply'])
    if request.method == 'POST':
        form = ForumSettingsForm(data=request.POST)
        if form.is_valid():
            form.save(commit=True)
            return HttpResponseRedirect(user_profile.get_absolute_url())
    else:
        form = ForumSettingsForm()
    return render_to_response('forum/edit_user_forum_settings.html', {
        'forum_user': user,
        'forum_profile': user_profile,
        'form': form,
        'title': 'Edit Forum Settings',
    }, context_instance=RequestContext(request))
