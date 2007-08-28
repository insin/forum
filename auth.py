from forum.models import ForumProfile

def user_can_edit_post(user, post):
    """
    Returns ``True`` if the given User can edit the given Post,
    ``False`` otherwise.
    """
    return user.id == post.user_id or \
           ForumProfile.objects.get_for_user(user).is_moderator()

def user_can_edit_user_profile(user, user_to_edit):
    """
    Returns ``True`` if the given User can edit the given User's
    profile, ``False`` otherwise.
    """
    return user.id == user_to_edit.id or \
           ForumProfile.objects.get_for_user(user).is_moderator()
