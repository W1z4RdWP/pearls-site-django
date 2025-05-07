from courses.models import CourseMessage

def unread_notifications(request):
    if request.user.is_authenticated:
        return {
            'unread_count': CourseMessage.objects.filter(
                recipient=request.user,
                is_read=False
            ).exclude(sender=request.user).count()
        }
    return {}