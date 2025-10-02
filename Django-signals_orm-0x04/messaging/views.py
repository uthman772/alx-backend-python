from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Prefetch, Q
from .models import Message, Notification, MessageHistory

@login_required
def message_thread(request, message_id):
    """
    View to display a message thread with all replies in threaded format.
    Uses optimized queries with select_related and prefetch_related.
    """
    root_message = get_object_or_404(Message, pk=message_id)
    
    # Check if user has permission to view this thread
    if root_message.sender != request.user and root_message.receiver != request.user:
        return render(request, 'messaging/access_denied.html')
    
    # Get the entire thread with optimized queries
    thread_messages = Message.objects.get_conversation_thread(root_message)
    
    # Mark messages as read when viewing thread
    unread_messages = thread_messages.filter(
        receiver=request.user, 
        is_read=False
    )
    unread_messages.update(is_read=True)
    
    context = {
        'root_message': root_message,
        'thread_messages': thread_messages,
        'thread_tree': build_thread_tree(thread_messages),
    }
    
    return render(request, 'messaging/message_thread.html', context)

@login_required
def create_reply(request, message_id):
    """
    View to handle creating replies to messages.
    """
    parent_message = get_object_or_404(Message, pk=message_id)
    
    # Check if user has permission to reply to this message
    if parent_message.sender != request.user and parent_message.receiver != request.user:
        return render(request, 'messaging/access_denied.html')
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        
        if content:
            reply = Message.objects.create(
                sender=request.user,
                receiver=parent_message.sender if request.user != parent_message.sender else parent_message.receiver,
                subject=f"Re: {parent_message.subject}",
                content=content,
                parent_message=parent_message
            )
            
            messages.success(request, "Your reply has been sent.")
            return redirect('messaging:message_thread', message_id=parent_message.get_thread_root().pk)
        else:
            messages.error(request, "Please provide content for your reply.")
    
    context = {
        'parent_message': parent_message,
    }
    return render(request, 'messaging/create_reply.html', context)

@login_required
def conversation_list(request):
    """
    View to display all conversations for the current user.
    Uses optimized queries to get root messages with reply counts.
    """
    # Get root messages with optimized queries
    conversations = Message.objects.get_root_messages(request.user)
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'messaging/conversation_list.html', context)

@login_required
def conversation_thread_api(request, message_id):
    """
    API endpoint to get conversation thread as JSON for AJAX loading.
    """
    root_message = get_object_or_404(Message, pk=message_id)
    
    # Check if user has permission to view this thread
    if root_message.sender != request.user and root_message.receiver != request.user:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get thread with optimized queries
    thread_messages = Message.objects.get_conversation_thread(root_message)
    
    thread_data = []
    for msg in thread_messages:
        thread_data.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'receiver': msg.receiver.username,
            'subject': msg.subject,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'is_read': msg.is_read,
            'depth': msg.depth,
            'parent_id': msg.parent_message.id if msg.parent_message else None,
            'is_root': msg.is_root_message,
        })
    
    return JsonResponse({
        'thread': thread_data,
        'root_message_id': root_message.id
    })

def build_thread_tree(messages_queryset):
    """
    Helper function to build a thread tree structure from a flat queryset.
    """
    messages_dict = {}
    root_messages = []
    
    # Create dictionary for quick lookup
    for message in messages_queryset:
        messages_dict[message.id] = {
            'message': message,
            'replies': []
        }
    
    # Build tree structure
    for message in messages_queryset:
        if message.parent_message:
            parent_id = message.parent_message.id
            if parent_id in messages_dict:
                messages_dict[parent_id]['replies'].append(messages_dict[message.id])
        else:
            root_messages.append(messages_dict[message.id])
    
    return root_messages

@login_required
def delete_account_confirmation(request):
    """View to show account deletion confirmation page."""
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
    """View to handle user account deletion."""
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
            
            messages.success(
                request, 
                f"Your account '{username}' has been successfully deleted."
            )
            
            return redirect('home')
            
        except Exception as e:
            messages.error(
                request,
                f"An error occurred while deleting your account: {str(e)}"
            )
            return redirect('delete_account_confirmation')
    
    return redirect('delete_account_confirmation')

@login_required
def user_data_summary(request):
    """API endpoint to get summary of user's data."""
    user = request.user
    
    data = {
        'sent_messages': Message.objects.filter(sender=user).count(),
        'received_messages': Message.objects.filter(receiver=user).count(),
        'notifications': Notification.objects.filter(user=user).count(),
        'edit_history': MessageHistory.objects.filter(edited_by=user).count(),
    }
    
    return JsonResponse(data)
