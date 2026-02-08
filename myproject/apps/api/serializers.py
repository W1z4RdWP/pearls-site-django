from rest_framework import serializers
from django.contrib.auth.models import User, Group
from courses.models import Course


class GroupSerializer(serializers.ModelSerializer):
    """Сериализатор группы пользователя."""

    class Meta:
        model = Group
        fields = ('id', 'name')


class UserMeSerializer(serializers.ModelSerializer):
    """Сериализатор текущего пользователя для navbar."""

    groups = GroupSerializer(many=True, read_only=True)
    avatar_url = serializers.SerializerMethodField()
    is_mentor = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_staff',
            'is_superuser',
            'groups',
            'avatar_url',
            'is_mentor',
        )

    def get_avatar_url(self, obj):
        try:
            if obj.profile and obj.profile.image:
                return obj.profile.image.url
        except Exception:
            pass
        return '/media/profile_pics/default.jpg'

    def get_is_mentor(self, obj):
        try:
            return obj.profile.is_mentor_user
        except Exception:
            return False


class CourseListSerializer(serializers.ModelSerializer):
    """Сериализатор курса для списка на главной странице."""

    image_url = serializers.SerializerMethodField()
    description_plain = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            'id',
            'title',
            'slug',
            'image_url',
            'description_plain',
            'created_at',
        )

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return '/static/global/imgs/default.jpg'

    def get_description_plain(self, obj):
        """Возвращает первые 50 слов описания без HTML-тегов."""
        import re
        if not obj.description:
            return ''
        text = re.sub(r'<[^>]+>', '', str(obj.description))
        words = text.split()
        return ' '.join(words[:50]) + ('...' if len(words) > 50 else '')
