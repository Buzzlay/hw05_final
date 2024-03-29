from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .forms import PostForm, CommentForm
from .models import Post, Follow, Group, User


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "index.html", {
        'page': page,
        'paginator': paginator
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_posts_list = group.posts.all()
    paginator = Paginator(group_posts_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "group.html", {
        'group': group,
        'page': page,
        'paginator': paginator
    })


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'newpost.html', {
            'form': form
        })
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    cache.touch('index_page', 0)
    return redirect('index')


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.all()
    paginator = Paginator(author_posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = request.user.is_authenticated and author.following.filter(
        user=request.user
    ).exists()
    return render(request, 'profile.html', {
        'author': author,
        'paginator': paginator,
        'page': page,
        'following': following
    })


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    author = post.author
    form = CommentForm()
    comments = post.comments.all()
    return render(request, 'post.html', {
        'post': post,
        'author': author,
        'comments': comments,
        'form': form
    })


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if post.author != request.user:
        return redirect('post', username, post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        cache.touch('index_page', 0)
        return redirect('post', username, post_id)
    return render(request, 'newpost.html', {
        'form': form,
        'post': post
    })


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    author = post.author
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        form = CommentForm()
        return render(request, 'post.html', {
            'post': post,
            'author': author,
            'comments': comments,
            'form': form
        })
    comment = form.save(commit=False)
    comment.post = post
    comment.author = request.user
    comment.save()
    return redirect('post', username, post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {
        'page': page,
        'paginator': paginator
    })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    following = author.following.filter(user=request.user).exists()
    if username != request.user.username and not following:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    unfollow = get_object_or_404(Follow, user=request.user, author=author)
    unfollow.delete()
    return redirect('profile', username)


@api_view(['GET', 'POST'])
def obtain_auth_token(request):
    if request.method == 'POST':
        return Response({'message': f'Привет {request.data}'})
    return Response({'message': 'Привет, мир!'})