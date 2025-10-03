from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Prefetch, Q
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie, vary_on_headers
from .models import Message, Notification, MessageHistory
import time

@login_required
@cache_page(60)  # Cache for 60 seconds
@vary_on_cookie  # Vary cache based on user cookie (authentication)
def conversation_list(request):
    """
    View to display all conversations for the current user.
    Cached for 60 seconds per user.
    """
    # Add a delay to simulate expensive operation (for testing cache)
    time.sleep(1)  # Remove this in production
    
    conversations = Message.objects.get_root_messages(request.user)
    
    # Get unread count for the badge
    unread_count = Message.unread_messages.unread_count_for_user(request.user)
    
    context = {
        'conversations': conversations,
        'unread_count': unread_count,
        'cached_at': time.time(),  # For testing cache
    }
    return render(request, 'messaging/conversation_list.html', context)

@login_required
@cache_page(60)  # Cache for 60 seconds
@vary_on_cookie  # Vary cache based on user
def message_thread(request, message_id):
    """
    View to display a message thread with all replies in threaded format.
    Cached for 60 seconds per user and message.
    """
    # Add a delay to simulate expensive operation (for testing cache)
    time.sleep(1)  # Remove this in production
    
    root_message = get_object_or_404(Message, pk=message_id)
    
    # Check if user has permission to view this thread
    if root_message.sender != request.user and root_message.receiver != request.user:
        return render(request, 'messaging/access_denied.html')
    
    # Mark the message as read when viewing
    if root_message.receiver == request.user and not root_message.is_read:
        root_message.mark_as_read()
    
    # Get the entire thread with optimized queries
    thread_messages = Message.objects.get_conversation_thread(root_message)
    
    context = {
        'root_message': root_message,
        'thread_messages': thread_messages,
        'thread_tree': build_thread_tree(thread_messages),
        'cached_at': time.time(),  # For testing cache
    }
    
    return render(request, 'messaging/message_thread.html', context)

@login_required
@cache_page(60)  # Cache for 60 seconds
@vary_on_cookie  # Vary cache based on user
def unread_messages(request):
    """
    View to display only unread messages for the current user.
    Cached for 60 seconds per user.
    """
    # Add a delay to simulate expensive operation (for testing cache)
    time.sleep(1)  # Remove this in production
    
    # Get unread messages using custom manager with optimized query
    unread_messages_list = Message.unread_messages.for_user(request.user)
    
    # Get unread count using custom manager method
    unread_count = Message.unread_messages.unread_count_for_user(request.user)
    
    context = {
        'unread_messages': unread_messages_list,
        'unread_count': unread_count,
        'page_title': 'Unread Messages',
        'cached_at': time.time(),  # For testing cache
    }
    
    return render(request, 'messaging/unread_messages.html', context)

@login_required
@cache_page(60)  # Cache for 60 seconds
@vary_on_cookie  # Vary cache based on user
def inbox_summary(request):
    """
    View showing inbox summary with read and unread messages.
    Cached for 60 seconds per user.
    """
    # Add a delay to simulate expensive operation (for testing cache)
    time.sleep(1)  # Remove this in production
    
    # Get unread messages using custom manager
    unread_messages_list = Message.unread_messages.for_user(request.user)
    
    # Get read messages using custom manager
    read_messages_list = Message.read_messages.for_user(request.user)[:20]
    
    # Get total counts
    unread_count = unread_messages_list.count()
    read_count = Message.read_messages.for_user(request.user).count()
    total_count = Message.objects.get_user_conversations(request.user).count()
    
    context = {
        'unread_messages': unread_messages_list,
        'read_messages': read_messages_list,
        'unread_count': unread_count,
        'read_count': read_count,
        'total_count': total_count,
        'page_title': 'Inbox Summary',
        'cached_at': time.time(),  # For testing cache
    }
    
    return render(request, 'messaging/inbox_summary.html', context)

# API endpoints - typically not cached or cached differently
@login_required
def unread_messages_api(request):
    """
    API endpoint to get unread messages count and list.
    Not cached as it needs real-time data.
    """
    unread_count = Message.unread_messages.unread_count_for_user(request.user)
    
    # Get recent unread messages with limited fields
    recent_unread = Message.unread_messages.for_user(request.user)[:5]
    
    messages_data = []
    for msg in recent_unread:
        messages_data.append({
            'id': msg.id,
            'subject': msg.subject,
            'preview': msg.content[:100] + '...' if len(msg.content) > 100 else msg.content,
            'sender': msg.sender.username,
            'timestamp': msg.timestamp.isoformat(),
            'url': msg.get_absolute_url(),
        })
    
    return JsonResponse({
        'unread_count': unread_count,
        'recent_messages': messages_data,
        'cached': False,  # Indicate this is not cached
    })

@login_required
def conversation_thread_api(request, message_id):
    """
    API endpoint to get conversation thread as JSON for AJAX loading.
    Not cached as it needs real-time data for message status.
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
        'root_message_id': root_message.id,
        'cached': False,  # Indicate this is not cached
    })

# Views that should NOT be cached (forms, actions, etc.)
@login_required
def create_reply(request, message_id):
    """
    View to handle creating replies to messages.
    This should NOT be cached as it handles form submissions.
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
def mark_message_read(request, message_id):
    """
    View to mark a specific message as read.
    This should NOT be cached as it changes state.
    """
    message = get_object_or_404(Message, pk=message_id, receiver=request.user)
    
    # Use the instance method to mark as read
    message.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Message marked as read',
            'unread_count': Message.unread_messages.unread_count_for_user(request.user)
        })
    
    messages.success(request, "Message marked as read.")
    return redirect('messaging:unread_messages')

@login_required
def mark_all_read(request):
    """
    View to mark all unread messages as read for the current user.
    This should NOT be cached as it changes state.
    """
    if request.method == 'POST':
        updated_count = Message.unread_messages.mark_as_read(request.user)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Marked {updated_count} messages as read',
                'unread_count': 0
            })
        
        messages.success(request, f"Marked {updated_count} messages as read.")
        return redirect('messaging:unread_messages')
    
    return redirect('messaging:unread_messages')

# Helper function
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
