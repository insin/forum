from forum.models import ForumProfile

def user_can_edit_post(user, post):
    """
    Returns ``True`` if the given User can edit the given Post,
    ``False`` otherwise.
    """
    return user.id == post.user_id or \
           ForumProfile.objects.get_for_user(user).can_edit_any_post()
