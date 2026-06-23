from django.contrib import admin
from .models import Category, NewsVideo, Comment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'sort_order')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('sort_order', 'name')


@admin.register(NewsVideo)
class NewsVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'youtube_link', 'created_at')
    list_filter = ('category',)
    search_fields = ('title', 'youtube_link', 'category__name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


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
