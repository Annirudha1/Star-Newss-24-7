from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import generate_access_token
from .forms import RegisterForm
from .models import Category, Comment, NewsVideo
from .serializers import (
    CommentSerializer,
    LoginSerializer,
    NewsVideoSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


class IsCommentOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff or obj.user_id == request.user.id


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


def privacy_policy_view(request):
    return public_policy_view(request, 'news/privacy_policy.html', 'privacy-policy')


def editorial_policy_view(request):
    return public_policy_view(request, 'news/editorial_policy.html', 'editorial-policy')


def corrections_policy_view(request):
    return public_policy_view(request, 'news/corrections_policy.html', 'corrections-policy')


def terms_view(request):
    return public_policy_view(request, 'news/terms.html', 'terms')


def sources_policy_view(request):
    return public_policy_view(request, 'news/sources_policy.html', 'sources-policy')


def public_policy_view(request, template_name, current_page):
    return render(request, template_name, {
        'current_page': current_page,
        'categories': Category.objects.all(),
        'selected_category': None,
    })


def delete_account_view(request):
    if request.method == 'POST' and not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST' and request.POST.get('confirm_delete') == 'yes':
        account = request.user
        logout(request)
        Comment.objects.filter(user=account).delete()
        account.delete()
        messages.success(request, 'Your account and associated comments have been deleted.')
        return redirect('home')

    return render(request, 'news/delete_account.html', {
        'current_page': 'delete-account',
        'categories': Category.objects.all(),
        'selected_category': None,
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
    serializer_class = NewsVideoSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = NewsVideo.objects.select_related('category').prefetch_related(
            'likes',
            Prefetch('comments', queryset=Comment.objects.select_related('user')),
        )
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset


class NewsVideoRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NewsVideoSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return NewsVideo.objects.select_related('category').prefetch_related(
            'likes',
            Prefetch('comments', queryset=Comment.objects.select_related('user')),
        )

class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def _get_input_data(self, request):
        if request.method == 'GET':
            return request.query_params
        return request.data

    def get(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=self._get_input_data(request))
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                'token': generate_access_token(user),
                'user': UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def _get_input_data(self, request):
        if request.method == 'GET':
            return request.query_params
        return request.data

    def get(self, request):
        return self._authenticate(request)

    def post(self, request):
        return self._authenticate(request)

    def _authenticate(self, request):
        serializer = LoginSerializer(data=self._get_input_data(request), context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(
            {
                'token': serializer.validated_data['token'],
                'user': UserSerializer(serializer.validated_data['user']).data,
            }
        )


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return self.post(request)

    def post(self, request):
        return Response({'detail': 'Logged out successfully.'})


class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)

    def delete(self, request):
        account = request.user
        Comment.objects.filter(user=account).delete()
        account.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class UserRetrieveAPIView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class VideoLikeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get(self, request, pk):
        video = get_object_or_404(NewsVideo, pk=pk)
        action = request.query_params.get('action')
        if action == 'toggle':
            if not request.user.is_authenticated:
                return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
            if video.likes.filter(pk=request.user.pk).exists():
                video.likes.remove(request.user)
                liked = False
            else:
                video.likes.add(request.user)
                liked = True
            return Response({'liked': liked, 'count': video.like_count})
        if action == 'like':
            if not request.user.is_authenticated:
                return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
            video.likes.add(request.user)
            return Response({'liked': True, 'count': video.like_count})
        if action == 'unlike':
            if not request.user.is_authenticated:
                return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
            video.likes.remove(request.user)
            return Response({'liked': False, 'count': video.like_count})

        liked = False
        if request.user.is_authenticated:
            liked = video.likes.filter(pk=request.user.pk).exists()
        return Response({'liked': liked, 'count': video.like_count})

    def post(self, request, pk):
        video = get_object_or_404(NewsVideo, pk=pk)
        video.likes.add(request.user)
        return Response({'liked': True, 'count': video.like_count})

    def delete(self, request, pk):
        video = get_object_or_404(NewsVideo, pk=pk)
        video.likes.remove(request.user)
        return Response({'liked': False, 'count': video.like_count})


class VideoCommentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        return Comment.objects.filter(video_id=self.kwargs['pk']).select_related('user', 'video')

    def perform_create(self, serializer):
        video = get_object_or_404(NewsVideo, pk=self.kwargs['pk'])
        serializer.save(video=video, user=self.request.user)


class CommentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.select_related('user', 'video')
    serializer_class = CommentSerializer
    permission_classes = [IsCommentOwnerOrReadOnly]
