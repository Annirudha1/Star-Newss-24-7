from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import generics
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from .forms import RegisterForm
from .models import Category, NewsVideo
from .serializers import NewsVideoSerializer

User = get_user_model()


def home(request, category_slug=None):
    categories = Category.objects.all()
    selected_category = None

    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        videos = selected_category.videos.all()
    else:
        videos = NewsVideo.objects.all()

    return render(request, 'news/index.html', {
        'videos': videos,
        'categories': categories,
        'selected_category': selected_category,
        'current_page': 'home',
    })


def about_view(request):
    categories = Category.objects.all()
    return render(request, 'news/about.html', {
        'categories': categories,
        'selected_category': None,
        'current_page': 'about',
    })


def contact_view(request):
    categories = Category.objects.all()
    return render(request, 'news/contact.html', {
        'categories': categories,
        'selected_category': None,
        'current_page': 'contact',
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = None

        if email and password:
            try:
                account_user = User.objects.get(email__iexact=email)
                user = authenticate(request, username=account_user.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            return redirect('home')

        messages.error(request, 'Invalid email or password. Please try again.')

    return render(request, 'news/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Account created successfully. You can now sign in.')
        return redirect('login')

    return render(request, 'news/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been signed out.')
    return redirect('home')


@require_POST
@login_required
def like_toggle(request, pk):
    video = get_object_or_404(NewsVideo, pk=pk)
    user = request.user
    if user in video.likes.all():
        video.likes.remove(user)
        liked = False
    else:
        video.likes.add(user)
        liked = True
    return JsonResponse({'liked': liked, 'count': video.like_count})


@require_POST
@login_required
def comment_create(request, pk):
    video = get_object_or_404(NewsVideo, pk=pk)
    content = request.POST.get('content', '').strip()
    if not content:
        return HttpResponseBadRequest('Empty comment')

    comment = video.comments.create(user=request.user, content=content)

    return JsonResponse({
        'id': comment.id,
        'user': str(request.user),
        'content': comment.content,
        'created_at': comment.created_at.isoformat(),
        'count': video.comments.count(),
    })


class NewsVideoListCreateAPIView(generics.ListCreateAPIView):
    queryset = NewsVideo.objects.all()
    serializer_class = NewsVideoSerializer


class NewsVideoRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = NewsVideo.objects.all()
    serializer_class = NewsVideoSerializer
