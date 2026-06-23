from rest_framework import serializers

from .models import NewsVideo, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class NewsVideoSerializer(serializers.ModelSerializer):
    video_id = serializers.CharField(read_only=True)
    thumbnail_url = serializers.CharField(read_only=True)
    embed_url = serializers.CharField(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = NewsVideo
        fields = [
            'id',
            'title',
            'youtube_link',
            'created_at',
            'video_id',
            'thumbnail_url',
            'embed_url',
            'category',
        ]
        read_only_fields = ['id', 'created_at', 'video_id', 'thumbnail_url', 'embed_url', 'category']
