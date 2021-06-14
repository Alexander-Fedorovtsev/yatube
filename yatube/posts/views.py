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
    """Функция для получения страницы с постами.
    """
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return {
        'page': page,
    }


@require_GET
def index(request):
    """View-функция для главной страницы проекта.
    """
    post_list = Post.objects.all()
    page_number = request.GET.get('page')
    return render(
        request,
        'posts/index.html',
        {
            **_all_posts(request, post_list),
            'page_number': page_number,
        },
    )


@require_GET
def group_posts(request, slug: str):
    """View-функция для страницы сообщества.
    """
    group = get_object_or_404(Group, slug=slug)
    return render(
        request,
        'posts/group.html',
        {
            **_all_posts(request, group.posts.all()),
            'group': group,
        },
    )


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


@login_required
def _check_follow(request, user_author):
    """Функция для проверки подписки на автора.
    """
    if user_author.following.filter(user=request.user).exists():
        return True
    else:
        return False


@require_GET
def profile(request, username):
    """View-функция для страницы профайла пользователя.
    """
    author_info = _get_author_info(username)
    post_list = author_info['author'].posts.all()
    context = {
        **author_info,
        **_all_posts(request, post_list),
    }

    if not request.user.is_authenticated:
        return render(
            request,
            'posts/profile.html',
            context,
        )
    return render(
        request,
        'posts/profile.html',
        {
            **context,
            'following': _check_follow(request, author_info['author']),
        },
    )


@require_http_methods(["GET", "POST"])
def post_view(request, username, post_id):
    """View-функция для страницы поста.
    """
    author_info = _get_author_info(username)
    post = get_object_or_404(Post, id=post_id)
    author_info['post'] = post
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        **author_info,
        'post': post,
        'form': form,
        'comments': comments,
    }
    if request.user.is_authenticated:
        return render(
            request,
            'posts/post.html',
            {
                **context,
                'following': _check_follow(request, author_info['author']),
            },
        )
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
    form = PostForm(request.POST or None, request.FILES or None)
    if not form.is_valid():
        return render(
            request,
            'posts/new_post.html',
            {
                'form': form,
            },
        )
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
    path_post = redirect(
        'post',
        username=username,
        post_id=post_id
    )
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
        },
    )


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {
            'path': request.path
        },
        status=404,
    )


def server_error(request):
    return render(
        request,
        'misc/500.html',
        status=500,
    )


@require_http_methods(["GET", "POST"])
@login_required
def add_comment(request, username, post_id):
    """View-функция для добавления нового комментария. Видна только
    авторизованным пользователям.
    """
    get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = post
        new_comment.save()
    return redirect(
        'post',
        username=username,
        post_id=post_id,
    )


@require_GET
@login_required
def follow_index(request):
    """View-функция страницы, куда будут выведены посты авторов, на
    которых подписан текущий пользователь. Видна только авторизованным
    пользователям.
    """
    post_list = Post.objects.prefetch_related('author').filter(
        author__following__user=request.user)
    return render(
        request,
        'posts/follow.html',
        _all_posts(request, post_list),
    )


def _redirect_follow(request, username, action):
    """Функция для реализации подписики и отписки от автора.
    """
    author_follow = get_object_or_404(User, username=username)
    user_follower = get_object_or_404(User, username=request.user.username)
    path_to_follow = redirect(
        'profile',
        username=username,
    )
    if author_follow == user_follower:
        return path_to_follow
    check_following = _check_follow(request, author_follow)
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
