from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('category/<slug:category_slug>/', views.home, name='category_videos'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('api/videos/', views.NewsVideoListCreateAPIView.as_view(), name='video-list'),
    path('api/videos/<int:pk>/', views.NewsVideoRetrieveUpdateDestroyAPIView.as_view(), name='video-detail'),
    path('video/<int:pk>/like/', views.like_toggle, name='video-like'),
    path('video/<int:pk>/comment/', views.comment_create, name='video-comment'),
]
