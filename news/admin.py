from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from botocore.exceptions import ClientError

from .models import Category, NewsVideo, Comment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'sort_order')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('sort_order', 'name')


@admin.register(NewsVideo)
class NewsVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'thumbnail_preview', 'video_file_link', 'created_at', 'delete_button')
    list_filter = ('category',)
    search_fields = ('title', 'description', 'category__name')
    readonly_fields = ('created_at', 'thumbnail_preview', 'video_file_link')
    ordering = ('-created_at',)
    fields = ('title', 'description', 'thumbnail', 'uploaded_video', 'category', 'created_at', 'thumbnail_preview', 'video_file_link')

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        try:
            return super().changeform_view(request, object_id, form_url, extra_context)
        except ClientError as exc:
            error = exc.response.get('Error', {})
            operation_name = getattr(exc, 'operation_name', 'Cloudflare R2')
            message = error.get('Message') or str(exc)
            self.message_user(
                request,
                f'Cloudflare R2 upload failed during {operation_name}: {message}. '
                'Check that the R2 API token has Object Write permission for this bucket.',
                level=messages.ERROR,
            )
            return HttpResponseRedirect(request.path)

    def delete_button(self, obj):
        delete_url = reverse('admin:news_newsvideo_delete', args=[obj.pk])
        return format_html('<a class="button" href="{}">Delete</a>', delete_url)
    delete_button.short_description = 'Delete'

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="height: 72px; width: auto; border-radius: 8px; object-fit: cover;" />', obj.thumbnail_url)
        return 'No thumbnail'
    thumbnail_preview.short_description = 'Thumbnail'

    def video_file_link(self, obj):
        if obj.uploaded_video:
            return format_html('<a href="{}" target="_blank" rel="noopener">{}</a>', obj.video_url, obj.uploaded_video.name)
        return 'No video file'
    video_file_link.short_description = 'Video file'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('video', 'user_display', 'short_content', 'created_at')
    list_filter = ('video', 'user')
    search_fields = ('content', 'user__username', 'video__title')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def user_display(self, obj):
        return obj.user.username if obj.user else 'Anonymous'
    user_display.short_description = 'User'

    def short_content(self, obj):
        return (obj.content[:75] + '...') if len(obj.content) > 75 else obj.content
    short_content.short_description = 'Comment'
