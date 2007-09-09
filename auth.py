"""
Utility functions related to forum user permissions.
"""
from forum.models import ForumProfile

def user_can_edit_post(user, post, topic=None):
    """
    Returns ``True`` if the given User can edit the given Post,
    ``False`` otherwise.

    If the Post's Topic is also given, its ``locked`` status will be
    taken into account when determining permissions.
    """
    if topic and topic.locked:
        return ForumProfile.objects.get_for_user(user).is_moderator()
    else:
        return user.id == post.user_id or \
            ForumProfile.objects.get_for_user(user).is_moderator()

def user_can_edit_topic(user, topic):
    """
    Returns ``True`` if the given User can edit the given Topic,
    ``False`` otherwise.
    """
    if topic.locked:
        return ForumProfile.objects.get_for_user(user).is_moderator()
    else:
        return user.id == topic.user_id or \
            ForumProfile.objects.get_for_user(user).is_moderator()

def user_can_edit_user_profile(user, user_to_edit):
    """
    Returns ``True`` if the given User can edit the given User's
    profile, ``False`` otherwise.
    """
    return user.id == user_to_edit.id or \
           ForumProfile.objects.get_for_user(user).is_moderator()

def is_moderator(user):
    """
    Shortcut so we don't have to paste this incantation everywhere.
    """
    return ForumProfile.objects.get_for_user(user).is_moderator()
