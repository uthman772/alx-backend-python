from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import transaction
from .models import Message, Notification, MessageHistory

@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """
    Signal to create a notification when a new message is created.
    Handles both regular messages and replies.
    """
    if created:
        if instance.parent_message:
            # This is a reply - notify the parent message sender
            notification_type = 'reply'
            title = f"New reply from {instance.sender.username}"
            # Also notify the receiver if they're different from the parent sender
            if instance.receiver != instance.parent_message.sender:
                # Create notification for the direct receiver too
                Notification.objects.create(
                    user=instance.receiver,
                    message=instance,
                    notification_type='message',
                    title=f"New message from {instance.sender.username}",
                    message_preview=f"{instance.subject}: {instance.content[:100]}..."
                )
        else:
            # This is a new conversation
            notification_type = 'message'
            title = f"New message from {instance.sender.username}"
        
        # Create notification for the appropriate user
        notification_user = instance.parent_message.sender if instance.parent_message else instance.receiver
        
        Notification.objects.create(
            user=notification_user,
            message=instance,
            notification_type=notification_type,
            title=title,
            message_preview=f"{instance.subject}: {instance.content[:100]}..."
        )
        
        print(f"Notification created for {notification_user.username}: {title}")

@receiver(pre_save, sender=Message)
def log_message_edit(sender, instance, **kwargs):
    """
    Signal to log message edits before saving.
    Creates a MessageHistory entry when a message is edited.
    """
    if instance.pk:  # Only for existing messages (updates)
        try:
            original = Message.objects.get(pk=instance.pk)
            
            # Check if content or subject has changed
            if (original.content != instance.content or 
                original.subject != instance.subject):
                
                # Determine who is editing the message
                edited_by = instance.sender
                
                # Create message history entry
                MessageHistory.objects.create(
                    message=instance,
                    old_subject=original.subject,
                    old_content=original.content,
                    edited_by=edited_by
                )
                
                # Create notification for the receiver about the edit
                Notification.objects.create(
                    user=instance.receiver,
                    message=instance,
                    notification_type='edit',
                    title=f"Message edited by {instance.sender.username}",
                    message_preview=f"'{original.subject}' was edited"
                )
                
                print(f"Message edit logged for message ID {instance.pk}")
                
        except Message.DoesNotExist:
            pass  # New message, no history to log

@receiver(pre_save, sender=Message)
def handle_reply_subject(sender, instance, **kwargs):
    """
    Signal to automatically set subject for replies.
    """
    if instance.parent_message and not instance.pk:
        # New reply - set subject automatically
        if not instance.subject.startswith('Re: '):
            instance.subject = f"Re: {instance.parent_message.subject}"

@receiver(post_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """
    Signal to clean up all user-related data when a user is deleted.
    """
    user_id = instance.id
    username = instance.username
    
    print(f"Cleaning up data for deleted user: {username} (ID: {user_id})")
    
    try:
        # Log cleanup information
        sent_messages = Message.objects.filter(sender=instance)
        received_messages = Message.objects.filter(receiver=instance)
        
        print(f"Cleaning up {sent_messages.count()} sent messages")
        print(f"Cleaning up {received_messages.count()} received messages")
        
        user_notifications = Notification.objects.filter(user=instance)
        print(f"Cleaning up {user_notifications.count()} notifications")
        
        edit_history = MessageHistory.objects.filter(edited_by=instance)
        print(f"Cleaning up {edit_history.count()} edit history entries")
        
        print(f"Successfully cleaned up all data for user: {username}")
        
    except Exception as e:
        print(f"Error during cleanup for user {username}: {str(e)}")

def user_post_save_receiver(sender, instance, created, **kwargs):
    """
    Example signal for user creation (optional bonus)
    """
    if created:
        try:
            admin_user = User.objects.get(username='admin')
            welcome_message = Message.objects.create(
                sender=admin_user,
                receiver=instance,
                subject="Welcome to our messaging platform!",
                content="Welcome! We're glad to have you here. You can start conversations and reply to messages."
            )
            print(f"Welcome message created for new user: {instance.username}")
        except User.DoesNotExist:
            print("Admin user not found for welcome message")

# Connect the user signal (optional)
post_save.connect(user_post_save_receiver, sender=User)
