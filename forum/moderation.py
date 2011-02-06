"""
Functions which perform moderation tasks - this can involve making
multiple, complex changes to the items being moderated.
"""
from forum.models import Post

def _update_num_in_topic(post, topic):
    """
    Updates the ``num_in_topic`` field for Posts in the given Topic
    affected by the given Post having its ``meta`` flag changed.
    """
    # Decrement num_in_topic for the post's current meta type
    Post.objects.update_num_in_topic(topic, post.num_in_topic, increment=False,
                                     meta=not post.meta)
    try:
        # Find the first prior post of the new meta type by post time -
        # fall back on id if times are equal.
        previous_post = \
            (topic.posts.filter(meta=post.meta, posted_at__lt=post.posted_at) | \
             topic.posts.filter(meta=post.meta, posted_at=post.posted_at, pk__lt=post.pk)) \
             .order_by('-posted_at', '-id')[0]
        post.num_in_topic = previous_post.num_in_topic + 1
        increment_from = previous_post.num_in_topic
    except IndexError:
        # There is no existing, earlier post - make this the first
        post.num_in_topic = 1
        increment_from = 0
    # Increment num_in_topic for the post's new meta type
    Post.objects.update_num_in_topic(topic, increment_from, increment=True,
                                     meta=post.meta)
    # Save the post to update its meta and num_in_topic attributes
    post.save()

def make_post_not_meta(post, topic, forum):
    """
    Performs changes required to turn a metapost into a regular post.
    """
    # If this becomes the new last post in its topic, the topic will need
    # its last post details updated.
    is_last_in_topic = False
    if post.posted_at > topic.last_post_at:
        is_last_in_topic = True
    # If this becomes the new last post in its forum, the forum will need
    # its last post details updated.
    is_last_in_forum = False
    if post.posted_at > forum.last_post_at:
        is_last_in_forum = True
    # Update num_in_topic for all affected posts
    _update_num_in_topic(post, topic)
    # Make any changes required to the topic and forum
    if is_last_in_topic:
        topic.set_last_post(post)
    else:
        topic.update_post_count(meta=False)
    topic.update_post_count(meta=True)
    if is_last_in_forum:
        forum.set_last_post(post)

def make_post_meta(post, topic, forum):
    """
    Performs changes required to turn a regular post into a metapost.
    """
    # If this was the last post in its topic, the topic will need its
    # last post details updated.
    was_last_in_topic = False
    if topic.last_post_at == post.posted_at and \
       topic.last_user_id == post.user_id:
        was_last_in_topic = True
    # If this was the last post in its forum, the forum will need its
    # latest post details updated.
    was_last_in_forum = False
    if forum.last_topic_id == topic.pk and \
       forum.last_post_at == post.posted_at and \
       forum.last_user_id == post.user_id:
        was_last_in_forum = True
    # Update num_in_topic for all affected posts
    _update_num_in_topic(post, topic)
    # Make any changes required to the topic and forum
    if was_last_in_topic:
        topic.set_last_post()
    else:
        topic.update_post_count(meta=False)
    topic.update_post_count(meta=True)
    if was_last_in_forum:
        forum.set_last_post()
