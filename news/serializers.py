from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from .authentication import generate_access_token
from .models import Category, Comment, NewsVideo

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']

    def get_full_name(self, obj):
        return obj.get_full_name().strip()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'full_name']
        read_only_fields = ['id']

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def create(self, validated_data):
        full_name = validated_data.pop('full_name', '').strip()
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
        )
        user.set_password(validated_data['password'])
        if full_name:
            name_parts = full_name.split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    token = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)

    def validate(self, attrs):
        email = attrs.get('email', '').strip()
        password = attrs.get('password', '')

        try:
            account_user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError('Invalid email or password.') from exc

        user = authenticate(
            request=self.context.get('request'),
            username=account_user.username,
            password=password,
        )
        if user is None:
            raise serializers.ValidationError('Invalid email or password.')

        attrs['user'] = user
        attrs['token'] = generate_access_token(user)
        return attrs


class UserUpdateSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'full_name']

    def validate_email(self, value):
        queryset = User.objects.filter(email__iexact=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def update(self, instance, validated_data):
        full_name = validated_data.pop('full_name', None)
        if full_name is not None:
            full_name = full_name.strip()
            if full_name:
                name_parts = full_name.split(' ', 1)
                validated_data['first_name'] = name_parts[0]
                validated_data['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
            else:
                validated_data['first_name'] = ''
                validated_data['last_name'] = ''
        return super().update(instance, validated_data)


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    video = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'video', 'user', 'content', 'created_at']
        read_only_fields = ['id', 'video', 'user', 'created_at']


class NewsVideoSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.CharField(read_only=True)
    video_url = serializers.CharField(read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source='category',
        queryset=Category.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    thumbnail = serializers.ImageField(required=False, allow_null=True)
    uploaded_video = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = NewsVideo
        fields = [
            'id',
            'title',
            'description',
            'thumbnail',
            'uploaded_video',
            'created_at',
            'thumbnail_url',
            'video_url',
            'like_count',
            'comment_count',
            'category',
            'category_id',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'thumbnail_url',
            'video_url',
            'like_count',
            'comment_count',
            'category',
        ]

    def get_comment_count(self, obj):
        return obj.comments.count()

    def validate(self, attrs):
        description = attrs.get('description')
        thumbnail = attrs.get('thumbnail')
        uploaded_video = attrs.get('uploaded_video')
        instance = getattr(self, 'instance', None)

        final_description = description if description is not None else getattr(instance, 'description', '')
        final_thumbnail = thumbnail if thumbnail is not None else getattr(instance, 'thumbnail', None)
        final_uploaded_video = uploaded_video if uploaded_video is not None else getattr(instance, 'uploaded_video', None)
        final_youtube_link = attrs.get('youtube_link') if 'youtube_link' in attrs else getattr(instance, 'youtube_link', '')

        if not final_youtube_link and not final_uploaded_video:
            raise serializers.ValidationError({'uploaded_video': 'Upload a video file.'})
        if not final_youtube_link and not final_thumbnail:
            raise serializers.ValidationError({'thumbnail': 'Upload a thumbnail image.'})
        if not final_description and not final_youtube_link and not final_uploaded_video:
            raise serializers.ValidationError({'description': 'Add a description for the video.'})
        return attrs
