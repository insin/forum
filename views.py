from django import newforms as forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import connection
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.encoding import smart_unicode
from django.views.generic.list_detail import object_list

from forum import app_settings
from forum import auth
from forum.formatters import post_formatter
from forum.forms import forum_profile_formfield_callback
from forum.models import Forum, ForumProfile, Post, Topic

qn = connection.ops.quote_name

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
    Displays a list of Forums.
    """
    return render_to_response('forum/forum_index.html', {
        'forum_list': Forum.objects.all(),
        'title': u'Forum index',
    }, context_instance=RequestContext(request))

def forum_detail(request, forum_id):
    """
    Displays a Forum's Topics.
    """
    forum = get_object_or_404(Forum, pk=forum_id)
    extra_context = {
        'forum': forum,
        'title': forum.name,
        'posts_per_page': get_posts_per_page(request.user),
    }
    if request.GET.get('page', 1) in (u'1', 1):
        extra_context['pinned_topics'] = \
            Topic.objects.with_user_details() \
                          .filter(forum=forum, pinned=True, hidden=False)
    return object_list(request,
        Topic.objects.with_user_details() \
                      .filter(forum=forum, pinned=False, hidden=False),
        paginate_by=get_topics_per_page(request.user), allow_empty=True,
        template_name='forum/forum_detail.html', extra_context=extra_context,
        template_object_name='topic')

@login_required
def new_posts(request):
    """
    Displays Topics containing new posts since the current User's last
    login.
    """
    queryset = Topic.objects.with_forum_and_user_details().filter(
        last_post_at__gte=request.user.last_login).order_by('-last_post_at')
    return object_list(request, queryset,
        paginate_by=get_topics_per_page(request.user), allow_empty=True,
        template_name='forum/new_posts.html',
        extra_context={
            'title': u'New posts',
            'posts_per_page': get_posts_per_page(request.user),
        }, template_object_name='topic')

@login_required
def add_topic(request, forum_id):
    """
    Adds a Topic to a Forum.
    """
    forum = get_object_or_404(Forum, pk=forum_id)
    AddTopicForm = forms.form_for_model(Topic, fields=('title', 'description'))
    TopicPostForm = forms.form_for_model(Post, fields=('body',))
    preview = None
    if request.method == 'POST':
        topic_form = AddTopicForm(request.POST)
        post_form = TopicPostForm(request.POST)
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
        topic_form = AddTopicForm()
        post_form = TopicPostForm()
    return render_to_response('forum/add_topic.html', {
        'topic_form': topic_form,
        'post_form': post_form,
        'forum': forum,
        'preview': preview,
        'title': u'Add topic',
    }, context_instance=RequestContext(request))

def topic_detail(request, topic_id):
    """
    Displays a Topic's Posts.
    """
    topic = get_object_or_404(Topic, pk=topic_id)
    topic.increment_view_count()
    return object_list(request,
        Post.objects.with_user_details().filter(topic=topic),
        paginate_by=get_posts_per_page(request.user), allow_empty=True,
        template_name='forum/topic_detail.html',
        extra_context={
            'topic': topic,
            'forum': topic.forum,
            'title': topic.title,
            'avatar_dimensions': get_avatar_dimensions(),
            'show_fast_reply': request.user.is_authenticated() and \
                ForumProfile.objects.get_for_user(request.user).auto_fast_reply \
                or False,
        }, template_object_name='post')

@login_required
def add_reply(request, topic_id, quote_post=None):
    """
    Adds a Post to a Topic.

    If ``quote_post`` is given, the form will be prepopulated with a
    quoted version of the post's body.
    """
    topic = get_object_or_404(Topic, pk=topic_id)
    AddReplyForm = forms.form_for_model(Post, fields=('body',))
    preview = None
    if request.method == 'POST':
        form = AddReplyForm(data=request.POST)
        if form.is_valid():
            if 'preview' in request.POST:
                preview = post_formatter.format_post_body(form.cleaned_data['body'])
            elif 'submit' in request.POST:
                post = form.save(commit=False)
                post.topic = topic
                post.user = request.user
                post.user_ip = request.META['REMOTE_ADDR']
                post.save()
                return redirect_to_post(request, post.id, post)
    else:
        initial = {}
        if quote_post is not None:
            initial['body'] = post_formatter.quote_post(quote_post)
        form = AddReplyForm(initial=initial)
    return render_to_response('forum/add_reply.html', {
        'form': form,
        'topic': topic,
        'forum': topic.forum,
        'preview': preview,
        'title': u'Add reply to %s' % topic.title,
    }, context_instance=RequestContext(request))

@login_required
def quote_post(request, post_id):
    """
    Adds a Post to a Topic, prepopulating the form with a quoted Post.
    """
    post = get_object_or_404(Post, pk=post_id)
    return add_reply(request, post.topic_id, post)

def redirect_to_post(request, post_id, post=None):
    """
    Redirects to the appropriate Topic page containing the given Post.

    If the Post itself is also given it will not be looked up, saving a
    database query.
    """
    if post is None:
        post = get_object_or_404(Post, pk=post_id)
    posts_per_page = get_posts_per_page(request.user)
    page, remainder = divmod(post.num_in_topic, posts_per_page)
    if post.num_in_topic < posts_per_page or remainder != 0:
        page += 1
    return HttpResponseRedirect('%s?page=%s#post%s' \
        % (reverse('forum_topic_detail', args=(smart_unicode(post.topic_id),)),
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
def edit_post(request, post_id):
    """
    Edits the given Post.
    """
    post = get_object_or_404(Post, pk=post_id)
    if not auth.user_can_edit_post(request.user, post):
        return HttpResponseForbidden()
    EditPostForm = forms.form_for_instance(post, fields=('body',))
    preview = None
    if request.method == 'POST':
        form = EditPostForm(data=request.POST)
        if form.is_valid():
            if 'preview' in request.POST:
                preview = post_formatter.format_post_body(form.cleaned_data['body'])
            elif 'submit' in request.POST:
                post = form.save(commit=True)
                return redirect_to_post(request, post.id, post)
    else:
        form = EditPostForm()
    topic = post.topic
    return render_to_response('forum/edit_post.html', {
        'form': form,
        'post': post,
        'topic': topic,
        'forum': topic.forum,
        'preview': preview,
        'title': u'Edit post',
    }, context_instance=RequestContext(request))

@login_required
def delete_post(request, post_id):
    """
    Deletes a Post after deletion is confirmed via POST.
    """
    post = get_object_or_404(Post.objects.with_user_details(), pk=post_id)
    if not auth.user_can_edit_post(request.user, post):
        return HttpResponseForbidden()
    topic = post.topic
    if request.method == 'POST':
        post.delete()
        return HttpResponseRedirect(topic.get_absolute_url())
    else:
        return render_to_response('forum/delete_post.html', {
            'post': post,
            'topic': topic,
            'forum': topic.forum,
            'title': u'Delete post',
            'avatar_dimensions': get_avatar_dimensions(),
        }, context_instance=RequestContext(request))

def user_profile(request, user_id):
    """
    Displays the Forum Profile for the user with the given id.
    """
    forum_user = get_object_or_404(User, pk=user_id)
    try:
        recent_topics = forum_user.topics.order_by('-started_at')[:5]
    except IndexError:
        recent_topics = []
    return render_to_response('forum/user_profile.html', {
        'forum_user': forum_user,
        'forum_profile': ForumProfile.objects.get_for_user(forum_user),
        'recent_topics': recent_topics,
        'title': u'User profile: %s' % forum_user,
        'avatar_dimensions': get_avatar_dimensions(),
    }, context_instance=RequestContext(request))

@login_required
def edit_user_profile(request, user_id):
    """
    Edits a given User's Forum Profile.
    """
    user = get_object_or_404(User, pk=user_id)
    if not auth.user_can_edit_user_profile(request.user, user):
        return HttpResponseForbidden()
    user_profile = ForumProfile.objects.get_for_user(user)
    editable_fields = ['location', 'avatar', 'website', 'timezone',
                       'topics_per_page', 'posts_per_page', 'auto_fast_reply']
    if ForumProfile.objects.get_for_user(request.user).is_moderator():
        editable_fields.insert(0, 'title')
    UserProfileForm = forms.form_for_instance(user_profile,
        formfield_callback=forum_profile_formfield_callback,
        fields=editable_fields)
    if request.method == 'POST':
        form = UserProfileForm(data=request.POST)
        if form.is_valid():
            form.save(commit=True)
            return HttpResponseRedirect(user_profile.get_absolute_url())
    else:
        form = UserProfileForm()
    return render_to_response('forum/edit_user_profile.html', {
        'forum_user': user,
        'forum_profile': user_profile,
        'form': form,
        'title': 'Edit user profile',
        'avatar_dimensions': get_avatar_dimensions(),
    }, context_instance=RequestContext(request))
