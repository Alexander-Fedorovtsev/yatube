"""Модуль с описанием view-функций приложения posts.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()


def _all_posts(request, post_list):
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return {
        'page': page,
        'page_number': page_number,
    }


@require_GET
def index(request):
    """View-функция для главной страницы проекта.
    """
    post_list = Post.objects.all()
    return render(
        request,
        'posts/index.html',
        _all_posts(request, post_list)
    )


@require_GET
def group_posts(request, slug: str):
    """View-функция для страницы сообщества.
    """
    group = get_object_or_404(Group, slug=slug)
    paginator = Paginator(group.posts.all(), 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/group.html', {'group': group, 'page': page})


def _get_author_info(username):
    """Функция для получения информации об авторе поста по username.
    """
    author = get_object_or_404(User, username=username)
    posts_count = author.posts.count()
    subscribers = author.following.count()
    signed = author.follower.count()
    return {
        'author': author,
        'posts_count': posts_count,
        'username': username,
        'subscribers': subscribers,
        'signed': signed,
    }


@require_GET
def profile(request, username):
    """View-функция для страницы профайла пользователя.
    """
    author_info = _get_author_info(username)
    post_list = Paginator(author_info['author'].posts.all(), 10)
    page_number = request.GET.get('page')
    page = post_list.get_page(page_number)
    if not request.user.is_authenticated:
        context = {
            **author_info,
            'page': page,
        }
    else:
        if (author_info['author'].following.filter(user=request.user).count()
                != 0):
            following = True
        else:
            following = False
        context = {
            **author_info,
            'page': page,
            'following': following,
        }
    return render(
        request,
        'posts/profile.html',
        context,
    )


@require_http_methods(["GET", "POST"])
def post_view(request, username, post_id):
    """View-функция для страницы поста.
    """
    author_info = _get_author_info(username)
    post = get_object_or_404(author_info['author'].posts, id=post_id)
    author_info['post'] = post
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        **author_info,
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(
        request,
        'posts/post.html',
        context,
    )


@require_http_methods(["GET", "POST"])
@login_required
def new_post(request):
    """View-функция для создания нового поста. Видна только авторизованным
    пользователям.
    """
    form = PostForm(request.POST or None)
    if not form.is_valid():
        return render(request, 'posts/new_post.html', {'form': form, })
    new_post = form.save(commit=False)
    new_post.author = request.user
    new_post.save()
    return redirect('index')


@require_http_methods(["GET", "POST"])
@login_required
def post_edit(request, username, post_id):
    """View-функция для редактирования поста. Доступна только автору поста.
    """
    author = get_object_or_404(User, username=username)
    edit_post = get_object_or_404(Post, pk=post_id)
    path_post = redirect('post', username=username, post_id=post_id)
    if request.user != author:
        return path_post
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=edit_post,
    )
    if form.is_valid():
        edit_post.save()
        return path_post

    return render(
        request,
        'posts/edit_post.html',
        {
            'form': form,
            'post': edit_post,
        }
    )


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем

    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@require_http_methods(["GET", "POST"])
@login_required
def add_comment(request, username, post_id):
    """View-функция для добавления нового комментария. Видна только
    авторизованным пользователям.
    """
    get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid() and request.user.is_authenticated:
        new_comment = form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = post
        new_comment.save()
    return redirect('post', username=username, post_id=post_id)


@require_GET
@login_required
def follow_index(request):
    """View-функция страницы, куда будут выведены посты авторов, на
    которых подписан текущий пользователь. Видна только авторизованным
    пользователям.
    """
    post_list = Post.objects.filter(author__following__user=request.user)
    return render(
        request,
        'posts/follow.html',
        _all_posts(request, post_list)
    )


def _redirect_follow(request, username, action):
    get_object_or_404(User.objects, username=username)
    author_follow = get_object_or_404(User, username=username)
    user_follower = get_object_or_404(User, username=request.user.username)
    path_to_follow = redirect('profile', username=username)
    if author_follow == user_follower:
        return path_to_follow
    check_following = author_follow.following.filter(user=user_follower)
    if not check_following and action == 'add':
        Follow.objects.create(
            author=author_follow,
            user=user_follower,
        )
        return path_to_follow
    elif check_following and action == 'del':
        Follow.objects.get(
            user=user_follower,
            author=author_follow,
        ).delete()
        return path_to_follow
    return path_to_follow


@login_required
def profile_follow(request, username):
    """View-функция для добавления подписки на автора. Видна только
    авторизованным пользователям.
    """
    return _redirect_follow(request, username, 'add')


@login_required
def profile_unfollow(request, username):
    """View-функция для удаления подписки на автора. Видна только
    авторизованным пользователям.
    """
    return _redirect_follow(request, username, 'del')
