from rest_framework import serializers
from django.contrib.auth.models import User, Group
from courses.models import Course, Lesson
from myapp.models import ChangeLog, UserCourse
from messenger.models import ChatRoom, RoomMessage, RoomMessageAttachment
from shop.models import InternalProduct, ProductOrder
from users.models import Role
from tech_support.models import (
    Ticket, TicketStatus, TicketPriority, TicketCategory,
    TicketAttachment, TicketComment,
)


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



class UserCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCourse
        fields = '__all__'


class InternalProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternalProduct
        fields = '__all__'


class ProductOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductOrder
        fields = '__all__'


class ChangelogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChangeLog
        fields = '__all__'


class UserBasicSerializer(serializers.ModelSerializer):
    """Базовый сериализатор пользователя для вложенных объектов."""
    
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')


class MessengerChatRoomSerializer(serializers.ModelSerializer):
    """Сериализатор комнаты чата для API."""

    created_by = UserBasicSerializer(read_only=True)

    class Meta:
        model = ChatRoom
        fields = '__all__'


# ---------------------------------------------------------------------------
#  Builder API — база знаний (master_detail, lesson detail block)
# ---------------------------------------------------------------------------

class BuilderLessonDetailSerializer(serializers.ModelSerializer):
    """Сериализатор урока для блока деталей базы знаний (содержание, видео)."""

    video_id = serializers.CharField(allow_null=True, required=False)

    class Meta:
        model = Lesson
        fields = ('id', 'title', 'content', 'video_id')


class BuilderRoleSerializer(serializers.ModelSerializer):
    """Сериализатор должности для блока актуализации и выбора ответственного."""

    class Meta:
        model = Role
        fields = ('id', 'name')


# ---------------------------------------------------------------------------
#  Tech Support API — детальная страница тикета
# ---------------------------------------------------------------------------

class TicketStatusSerializer(serializers.ModelSerializer):
    """Сериализатор статуса тикета."""

    class Meta:
        model = TicketStatus
        fields = ('id', 'name', 'color', 'is_active')


class TicketPrioritySerializer(serializers.ModelSerializer):
    """Сериализатор приоритета тикета."""

    class Meta:
        model = TicketPriority
        fields = ('id', 'name', 'level', 'response_time_hours', 'color')


class TicketCategorySerializer(serializers.ModelSerializer):
    """Сериализатор категории тикета."""

    class Meta:
        model = TicketCategory
        fields = ('id', 'name')


class TicketAttachmentSerializer(serializers.ModelSerializer):
    """Сериализатор вложения тикета."""

    file_url = serializers.SerializerMethodField()

    class Meta:
        model = TicketAttachment
        fields = ('id', 'filename', 'file_url', 'uploaded_at')

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


class TicketCommentSerializer(serializers.ModelSerializer):
    """Сериализатор комментария к тикету."""

    author = UserBasicSerializer(read_only=True)

    class Meta:
        model = TicketComment
        fields = ('id', 'author', 'content', 'is_internal', 'created_at')


class TicketDetailSerializer(serializers.ModelSerializer):
    """Сериализатор тикета для детальной страницы."""

    status = TicketStatusSerializer(read_only=True)
    priority = TicketPrioritySerializer(read_only=True)
    category = TicketCategorySerializer(read_only=True)
    created_by = UserBasicSerializer(read_only=True)
    assigned_to = UserBasicSerializer(read_only=True)
    ticket_type_display = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)
    deadline_hours_left = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = (
            'id', 'ticket_number', 'title', 'description', 'ticket_type',
            'ticket_type_display', 'status', 'priority', 'category',
            'created_by', 'assigned_to', 'created_at', 'updated_at',
            'resolved_at', 'deadline', 'rating', 'student_feedback',
            'is_overdue', 'deadline_hours_left',
        )

    def get_ticket_type_display(self, obj):
        return obj.get_ticket_type_display()

    def get_deadline_hours_left(self, obj):
        td = obj.time_to_deadline
        if td is None:
            return None
        hours = abs(td.total_seconds()) / 3600
        return round(hours, 1)


class StaffUserOptionSerializer(serializers.ModelSerializer):
    """Сериализатор сотрудника для выпадающего списка назначения."""

    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'display_name')

    def get_display_name(self, obj):
        role_name = ''
        try:
            if hasattr(obj, 'profile') and obj.profile and obj.profile.role:
                role_name = obj.profile.role.name
        except Exception:
            pass
        name = obj.get_full_name() or obj.username
        if role_name:
            return f"{name} ({role_name})"
        return name