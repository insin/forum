"""
Functions which perform moderation tasks - this can involve making
multiple, complex changes to the items being moderated.
"""
from forum.models import Post

def make_post_meta(post, topic, forum):
    """
    Performs changes required to turn an existing post into a metapost.
    """
    Post.objects.update_num_in_topic(topic, post.num_in_topic, increment=False,
                                     meta=False)
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
    try:
        # Find the first earlier meta post by post time
        previous_meta_post = \
            topic.posts.filter(meta=True, posted_at__lte=post.posted_at) \
                        .order_by('-posted_at')[0]
        post.num_in_topic = previous_meta_post.num_in_topic + 1
        increment_from = previous_meta_post.num_in_topic
    except IndexError:
        # There is no existing, earlier meta post - make this the first
        post.num_in_topic = 1
        increment_from = 0
    # Increment num_in_topic for existing meta posts
    Post.objects.update_num_in_topic(topic, increment_from, increment=True,
                                     meta=True)
    # Save the post to update its meta and num_in_topic attributes
    post.save()
    # Make any changes required to the topic and forum
    if was_last_in_topic:
        topic.set_last_post()
    else:
        topic.update_post_count(meta=False)
    topic.update_post_count(meta=True)
    if was_last_in_forum:
        forum.set_last_post()

def make_post_not_meta(post, topic, forum):
    """
    Performs changes required to turn an existing metapost into a post.
    """
    Post.objects.update_num_in_topic(topic, post.num_in_topic, increment=False,
                                     meta=True)
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
    try:
        # Find the first earlier post by post time
        previous_post = \
            topic.posts.filter(meta=False, posted_at__lte=post.posted_at) \
                        .order_by('-posted_at')[0]
        post.num_in_topic = previous_post.num_in_topic + 1
        increment_from = previous_post.num_in_topic
    except IndexError:
        # There is no existing, earlier post - make this the first
        post.num_in_topic = 1
        increment_from = 0
    # Increment num_in_topic for existing posts
    Post.objects.update_num_in_topic(topic, increment_from, increment=True,
                                     meta=False)
    # Save the post to update its meta and num_in_topic attributes
    post.save()
    # Make any changes required to the topic and forum
    if is_last_in_topic:
        topic.set_last_post(post)
    else:
        topic.update_post_count(meta=False)
    topic.update_post_count(meta=True)
    if is_last_in_forum:
        forum.set_last_post(post)
