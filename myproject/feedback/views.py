from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required


from .forms import CourseMessageForm
from .models import CourseMessage




@login_required
def notifications(request):
    # Получаем только входящие сообщения
    messages = CourseMessage.objects.filter(
        recipient=request.user
    ).exclude(sender=request.user).order_by('-timestamp')

    # Помечаем как прочитанные
    messages.update(is_read=True)

    return render(request, 'feedback/notifications.html', {
        'messages': messages
    })


# @login_required
# def send_feedback(request):
#     if request.method == 'POST':
#         form = FeedbackForm(request.POST, user=request.user)
#         if form.is_valid():
#             feedback = form.save(commit=False)
#             feedback.sender = request.user
#             feedback.recipient = feedback.course.author
#             feedback.save()
#             return redirect('messages_inbox')
#     else:
#         form = FeedbackForm(user=request.user)
#     return render(request, 'feedback/send_feedback.html', {'form': form})

# @login_required
# def messages_inbox(request):
#     messages = FeedbackMessage.objects.filter(recipient=request.user).order_by('-timestamp')
#     return render(request, 'feedback/messages_inbox.html', {'messages': messages})

# @login_required
# def message_detail(request, message_id):
#     message = get_object_or_404(FeedbackMessage, id=message_id)
#     if request.user != message.recipient and request.user != message.sender:
#         return HttpResponseForbidden()
    
#     if request.method == 'POST':
#         form = FeedbackForm(request.POST)
#         if form.is_valid():
#             reply = form.save(commit=False)
#             reply.sender = request.user
#             reply.recipient = message.sender
#             reply.parent_message = message
#             reply.save()
#             return redirect('message_detail', message_id=message_id)
    
#     message.is_read = True
#     message.save()
#     replies = FeedbackMessage.objects.filter(parent_message=message)
#     form = FeedbackForm()
#     return render(request, 'feedback/message_detail.html', {
#         'message': message,
#         'replies': replies,
#         'form': form
#     })
