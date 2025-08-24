from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app.blueprints.forums import forums_bp
from app.models.forums import Forum, Topic, Post
from app.models.users import User
from app.blueprints.forums.forms import CreateTopicForm, CreatePostForm
from app.blueprints.notifications.routes import add_notification # Import add_notification

TOPICS_PER_PAGE = 10
POSTS_PER_PAGE = 10

@forums_bp.route('/')
def forum_home():
    search_query = request.args.get('q', '')
    if search_query:
        # Search for forums where name or description contains the query
        forums = Forum.objects(Q(name__icontains=search_query) | Q(description__icontains=search_query)).order_by('name')
    else:
        forums = Forum.objects.order_by('name')
    return render_template('forums/home.html', forums=forums, title='Forums')

TOPICS_PER_PAGE = 10
POSTS_PER_PAGE = 10

@forums_bp.route('/forum/<string:forum_id>')
@forums_bp.route('/forum/<string:forum_id>/page/<int:page>')
def view_forum(forum_id, page=1):
    forum = Forum.objects.get_or_404(id=forum_id)
    search_query = request.args.get('q', '')
    if search_query:
        topics_pagination = Topic.objects(forum=forum, title__icontains=search_query).order_by('-last_post_at').paginate(page=page, per_page=TOPICS_PER_PAGE)
    else:
        topics_pagination = Topic.objects(forum=forum).order_by('-last_post_at').paginate(page=page, per_page=TOPICS_PER_PAGE)
    return render_template('forums/forum.html', forum=forum, topics_pagination=topics_pagination, title=forum.name)

@forums_bp.route('/topic/<string:topic_id>')
@forums_bp.route('/topic/<string:topic_id>/page/<int:page>')
def view_topic(topic_id, page=1):
    topic = Topic.objects.get_or_404(id=topic_id)
    posts_pagination = Post.objects(topic=topic).order_by('created_at').paginate(page=page, per_page=POSTS_PER_PAGE)
    topic.views += 1
    topic.save() # Increment view count
    form = CreatePostForm()
    is_subscribed = False
    if current_user.is_authenticated:
        is_subscribed = topic in current_user.subscribed_topics
    return render_template('forums/topic.html', topic=topic, posts_pagination=posts_pagination, form=form, title=topic.title, is_subscribed=is_subscribed)

@forums_bp.route('/forum/new_topic', methods=['GET', 'POST'])
@forums_bp.route('/forum/<string:forum_id>/new_topic', methods=['GET', 'POST'])
@login_required
def new_topic(forum_id=None):
    if forum_id is None:
        forums = Forum.objects.order_by('name')
        return render_template('forums/select_forum.html', forums=forums, title='Select a Forum')

    forum = Forum.objects.get_or_404(id=forum_id)
    form = CreateTopicForm()
    if form.validate_on_submit():
        topic = Topic(
            title=form.title.data,
            forum=forum,
            author=current_user._get_current_object()
        )
        topic.save()

        post = Post(
            content=form.content.data,
            topic=topic,
            author=current_user._get_current_object()
        )
        post.save()

        # Update forum and topic stats
        forum.topic_count += 1
        forum.post_count += 1
        forum.last_post_at = datetime.utcnow()
        forum.save()

        topic.post_count += 1
        topic.last_post_at = datetime.utcnow()
        topic.save()

        flash('Your topic has been created!', 'success')
        return redirect(url_for('forums.view_topic', topic_id=topic.id))
    return render_template('forums/new_topic.html', title='New Topic', form=form, forum=forum)

@forums_bp.route('/topic/<string:topic_id>/new_post', methods=['POST'])
@login_required
def new_post(topic_id):
    topic = Topic.objects.get_or_404(id=topic_id)
    form = CreatePostForm()
    if form.validate_on_submit():
        post = Post(
            content=form.content.data,
            topic=topic,
            author=current_user._get_current_object()
        )
        post.save()

        # Update forum and topic stats
        topic.post_count += 1
        topic.last_post_at = datetime.utcnow()
        topic.save()

        topic.forum.post_count += 1
        topic.forum.last_post_at = datetime.utcnow()
        topic.forum.save()

        flash('Your reply has been posted!', 'success')

        # Send notifications to subscribed users
        for user in topic.subscribed_topics: # Iterate through subscribed users
            # Ensure the user is not the current poster and has forum reply notifications enabled
            if user.id != current_user.id and user.notify_forum_reply:
                add_notification(
                    user_id=str(user.id),
                    message=f"New reply in topic '{topic.title}' by {current_user.username}",
                    notification_type='forum_reply',
                    payload={'topic_id': str(topic.id), 'post_id': str(post.id)}
                )

        return redirect(url_for('forums.view_topic', topic_id=topic.id))
    
    # If form validation fails, re-render the topic page with errors
    posts_pagination = Post.objects(topic=topic).order_by('created_at').paginate(page=1, per_page=POSTS_PER_PAGE)
    return render_template('forums/topic.html', topic=topic, posts_pagination=posts_pagination, form=form, title=topic.title)

@forums_bp.route('/topic/<string:topic_id>/subscribe', methods=['POST'])
@login_required
def subscribe_topic(topic_id):
    topic = Topic.objects.get_or_404(id=topic_id)
    if topic not in current_user.subscribed_topics:
        current_user.subscribed_topics.append(topic)
        current_user.save()
        flash('You have subscribed to this topic!', 'success')
    else:
        flash('You are already subscribed to this topic.', 'info')
    return redirect(url_for('forums.view_topic', topic_id=topic.id))

@forums_bp.route('/topic/<string:topic_id>/unsubscribe', methods=['POST'])
@login_required
def unsubscribe_topic(topic_id):
    topic = Topic.objects.get_or_404(id=topic_id)
    if topic in current_user.subscribed_topics:
        current_user.subscribed_topics.remove(topic)
        current_user.save()
        flash('You have unsubscribed from this topic.', 'success')
    else:
        flash('You are not subscribed to this topic.', 'info')
    return redirect(url_for('forums.view_topic', topic_id=topic.id))