from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import paginator_view

POSTS_ON_LIST: int = 10


def index(request):
    posts = Post.objects.all().select_related()
    page_obj = paginator_view(request, posts)
    index = request
    context = {'page_obj': page_obj, 'index': index}
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginator_view(request, posts)
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = paginator_view(request, posts)
    user = request.user
    following = request.user.is_authenticated and Follow.objects.filter(
        user=user, author=author
    ).exists()
    context = {
        'author': author,
        'posts': posts,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': CommentForm(),
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None,)
        context = {'form': form, 'is_edit': False, }
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user.username)
        context = {'form': form, 'is_edit': False, }
        return render(request, 'posts/create_post.html', context)
    form = PostForm()
    context = {'form': form, 'is_edit': False, }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect("posts:post_detail", post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id=post_id)
    else:
        context = {'form': form, 'is_edit': True, 'post': post}
        return render(request, 'posts/create_post.html', context)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect("posts:post_detail", post_id=post_id)
    post.delete()
    return redirect('posts:profile', request.user.username)


@login_required
def add_comment(request, post_id):
    """Функция обработки формы добавления комментария"""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator_view(request, post_list)
    follow = request
    context = {
        'post_list': post_list,
        'page_obj': page_obj,
        'follow': follow,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    already_followed_user = Follow.objects.filter(user=request.user,
                                                  author=author).exists()
    if user == author:
        return redirect('posts:profile', username=username)
    if already_followed_user:
        return redirect('posts:profile', username=username)
    Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow_qs = Follow.objects.filter(author=author, user=request.user)
    if follow_qs.exists():
        follow_qs.delete()
    return redirect('posts:profile', username=username)
