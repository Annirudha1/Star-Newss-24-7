import base64
import shutil
import tempfile

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Comment, NewsArticle, NewsSource, NewsVideo, RSSFeed

User = get_user_model()

THUMBNAIL_BYTES = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='
)

TEST_MEDIA_ROOT = tempfile.mkdtemp()
TEST_STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}


@override_settings(SECURE_SSL_REDIRECT=False, MEDIA_ROOT=TEST_MEDIA_ROOT, STORAGES=TEST_STORAGES)
class APITestCaseSuite(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(
            username='reporter',
            email='reporter@example.com',
            password='strongpass123',
            first_name='Daily',
            last_name='Reporter',
        )
        self.other_user = User.objects.create_user(
            username='viewer',
            email='viewer@example.com',
            password='strongpass123',
        )
        self.category = Category.objects.create(name='Politics')
        self.video = NewsVideo.objects.create(
            title='Top Story',
            description='Top story description.',
            thumbnail=SimpleUploadedFile('top-story.png', THUMBNAIL_BYTES, content_type='image/png'),
            uploaded_video=SimpleUploadedFile('top-story.mp4', b'fake-video-content', content_type='video/mp4'),
            category=self.category,
        )

    def authenticate(self):
        response = self.client.post(
            reverse('api-login'),
            {'email': 'reporter@example.com', 'password': 'strongpass123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['token']}")
        return response

    def test_privacy_and_delete_account_pages_are_publicly_available(self):
        privacy_response = self.client.get(reverse('privacy-policy'))
        delete_response = self.client.get(reverse('delete-account'))

        self.assertEqual(privacy_response.status_code, status.HTTP_200_OK)
        self.assertContains(privacy_response, 'Google Sign-In')
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        self.assertContains(delete_response, 'Sign in to continue')

    def test_public_publisher_and_policy_pages(self):
        pages = (
            ('about', 'Sunil Sharma'),
            ('contact', 'starnewshindimodinagar@gmail.com'),
            ('editorial-policy', 'Editorial Policy'),
            ('corrections-policy', 'Corrections Policy'),
            ('privacy-policy', 'Privacy Policy'),
            ('terms', 'Terms &amp; Conditions'),
            ('sources-policy', 'Original Content &amp; Attribution Policy'),
        )
        for route_name, expected_text in pages:
            with self.subTest(page=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertContains(response, expected_text)

    def test_contact_keeps_publisher_and_developer_contacts_separate(self):
        response = self.client.get(reverse('contact'))

        self.assertContains(response, 'Publisher / Owner:</strong> Sunil Sharma')
        self.assertContains(response, 'starnewshindimodinagar@gmail.com')
        self.assertContains(response, 'Technical support:</strong>')
        self.assertContains(response, 'pandey.anirudha2023@gmail.com')
        self.assertNotContains(response, '7976506751')

    def test_homepage_describes_original_news_without_rss_sections(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, 'Original news reporting and video updates')
        self.assertContains(response, 'Original STAR NEWS 24×7 Report')
        self.assertNotContains(response, 'Latest News from Our Sources')
        self.assertNotContains(response, 'RSS')

    def test_legacy_feed_and_imported_article_models_are_not_in_admin(self):
        self.assertNotIn(RSSFeed, admin.site._registry)
        self.assertNotIn(NewsArticle, admin.site._registry)
        self.assertIn(NewsSource, admin.site._registry)

    def test_web_account_deletion_removes_account_and_comments(self):
        comment = Comment.objects.create(video=self.video, user=self.user, content='Remove this comment')
        self.video.likes.add(self.user)
        self.client.force_login(self.user)

        page_response = self.client.get(reverse('delete-account'))
        self.assertContains(page_response, 'Permanently delete my account')

        unconfirmed_response = self.client.post(reverse('delete-account'), {'confirm_delete': 'no'})
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())
        self.assertEqual(unconfirmed_response.status_code, status.HTTP_200_OK)

        response = self.client.post(reverse('delete-account'), {'confirm_delete': 'yes'})

        self.assertRedirects(response, reverse('home'))
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())
        self.assertFalse(self.video.likes.filter(pk=self.user.pk).exists())

    def test_delete_me_api_removes_account_and_comments(self):
        comment = Comment.objects.create(video=self.video, user=self.user, content='Remove this comment')
        self.video.likes.add(self.user)
        self.authenticate()

        response = self.client.delete(reverse('api-me'))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())
        self.assertFalse(self.video.likes.filter(pk=self.user.pk).exists())

    def test_register_api_creates_user(self):
        response = self.client.post(
            reverse('api-register'),
            {
                'username': 'anchor',
                'email': 'anchor@example.com',
                'password': 'strongpass123',
                'full_name': 'Night Anchor',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='anchor@example.com').exists())
        self.assertEqual(response.data['user']['first_name'], 'Night')

    def test_register_api_allows_get_for_testing(self):
        response = self.client.get(
            reverse('api-register'),
            {
                'username': 'morninganchor',
                'email': 'morninganchor@example.com',
                'password': 'strongpass123',
                'full_name': 'Morning Anchor',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='morninganchor@example.com').exists())
        self.assertEqual(response.data['user']['first_name'], 'Morning')

    def test_login_and_me_api(self):
        login_response = self.authenticate()
        self.assertIn('token', login_response.data)

        me_response = self.client.get(reverse('api-me'))
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data['email'], 'reporter@example.com')

    def test_login_api_allows_get_for_testing(self):
        response = self.client.get(
            reverse('api-login'),
            {'email': 'reporter@example.com', 'password': 'strongpass123'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['email'], 'reporter@example.com')

    def test_video_create_like_and_comment_apis(self):
        self.authenticate()

        create_response = self.client.post(
            reverse('video-list'),
            {
                'title': 'Field Update',
                'description': 'A field update from the morning briefing.',
                'thumbnail': SimpleUploadedFile('field-update.png', THUMBNAIL_BYTES, content_type='image/png'),
                'uploaded_video': SimpleUploadedFile('field-update.mp4', b'fake-video-content', content_type='video/mp4'),
                'category_id': self.category.id,
            },
            format='multipart',
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        created_video_id = create_response.data['id']

        like_response = self.client.post(reverse('video-like-api', args=[created_video_id]))
        self.assertEqual(like_response.status_code, status.HTTP_200_OK)
        self.assertEqual(like_response.data['count'], 1)

        get_like_response = self.client.get(reverse('video-like-api', args=[created_video_id]))
        self.assertEqual(get_like_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_like_response.data['count'], 1)
        self.assertTrue(get_like_response.data['liked'])

        unlike_via_get_response = self.client.get(
            reverse('video-like-api', args=[created_video_id]),
            {'action': 'unlike'},
        )
        self.assertEqual(unlike_via_get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(unlike_via_get_response.data['count'], 0)
        self.assertFalse(unlike_via_get_response.data['liked'])

        like_via_get_response = self.client.get(
            reverse('video-like-api', args=[created_video_id]),
            {'action': 'like'},
        )
        self.assertEqual(like_via_get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(like_via_get_response.data['count'], 1)
        self.assertTrue(like_via_get_response.data['liked'])

        comment_response = self.client.post(
            reverse('video-comments', args=[created_video_id]),
            {'content': 'Important update.'},
            format='json',
        )
        self.assertEqual(comment_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.filter(video_id=created_video_id).count(), 1)

    def test_comment_owner_can_update_but_other_user_cannot(self):
        comment = Comment.objects.create(video=self.video, user=self.user, content='Initial note')

        self.authenticate()
        update_response = self.client.patch(
            reverse('comment-detail', args=[comment.id]),
            {'content': 'Updated note'},
            format='json',
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        self.client.credentials()
        other_login = self.client.post(
            reverse('api-login'),
            {'email': 'viewer@example.com', 'password': 'strongpass123'},
            format='json',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {other_login.data['token']}")
        forbidden_response = self.client.patch(
            reverse('comment-detail', args=[comment.id]),
            {'content': 'Hijacked note'},
            format='json',
        )
        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)
