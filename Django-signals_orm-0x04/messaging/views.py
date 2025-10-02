from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db import transaction
from .models import Message, Notification, MessageHistory

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

@login_required
def delete_account_confirmation(request):
    """
    View to show account deletion confirmation page.
    """
    user = request.user
    
    # Get counts of user's data
    sent_messages_count = Message.objects.filter(sender=user).count()
    received_messages_count = Message.objects.filter(receiver=user).count()
    notifications_count = Notification.objects.filter(user=user).count()
    edit_history_count = MessageHistory.objects.filter(edited_by=user).count()
    
    context = {
        'sent_messages_count': sent_messages_count,
        'received_messages_count': received_messages_count,
        'notifications_count': notifications_count,
        'edit_history_count': edit_history_count,
        'total_data_count': (sent_messages_count + received_messages_count + 
                           notifications_count + edit_history_count)
    }
    
    return render(request, 'messaging/delete_account_confirmation.html', context)

@login_required
@transaction.atomic
def delete_account(request):
    """
    View to handle user account deletion.
    """
    if request.method == 'POST':
        user = request.user
        username = user.username
        
        try:
            # Store user data for confirmation message
            sent_messages_count = Message.objects.filter(sender=user).count()
            received_messages_count = Message.objects.filter(receiver=user).count()
            
            # Log the user out before deletion
            logout(request)
            
            # Delete the user (this will trigger the post_delete signal)
            user.delete()
            
            # Success message
            messages.success(
                request, 
                f"Your account '{username}' has been successfully deleted. "
                f"All your data including {sent_messages_count} sent messages, "
                f"{received_messages_count} received messages, and related data "
                f"has been permanently removed."
            )
            
            return redirect('home')
            
        except Exception as e:
            # Handle any errors during deletion
            messages.error(
                request,
                f"An error occurred while deleting your account: {str(e)}. "
                "Please try again or contact support."
            )
            return redirect('delete_account_confirmation')
    
    # If not POST, redirect to confirmation page
    return redirect('delete_account_confirmation')

@login_required
def user_data_summary(request):
    """
    API endpoint to get summary of user's data (for AJAX calls).
    """
    user = request.user
    
    data = {
        'sent_messages': Message.objects.filter(sender=user).count(),
        'received_messages': Message.objects.filter(receiver=user).count(),
        'notifications': Notification.objects.filter(user=user).count(),
        'edit_history': MessageHistory.objects.filter(edited_by=user).count(),
    }
    
    return JsonResponse(data)
