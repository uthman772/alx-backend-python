from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Message, MessageHistory

@login_required
def message_detail(request, message_id):
    """
    View to display message details and edit history.
    """
    message = get_object_or_404(Message, pk=message_id)
    
    # Check if user has permission to view this message
    if message.sender != request.user and message.receiver != request.user:
        return render(request, 'messaging/access_denied.html')
    
    # Get message history
    message_history = message.history.all().order_by('-edited_at')
    
    context = {
        'message': message,
        'message_history': message_history,
    }
    
    return render(request, 'messaging/message_detail.html', context)

@login_required
def message_history_api(request, message_id):
    """
    API endpoint to get message history as JSON.
    """
    message = get_object_or_404(Message, pk=message_id)
    
    # Check if user has permission to view this message
    if message.sender != request.user and message.receiver != request.user:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    history_data = []
    for history in message.history.all().order_by('-edited_at'):
        history_data.append({
            'old_subject': history.old_subject,
            'old_content': history.old_content,
            'edited_by': history.edited_by.username,
            'edited_at': history.edited_at.isoformat(),
        })
    
    return JsonResponse({'history': history_data})
