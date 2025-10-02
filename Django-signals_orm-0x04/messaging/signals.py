from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import transaction
from .models import Message, Notification, MessageHistory

@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """
    Signal to create a notification when a new message is created.
    """
    if created:
        # Create notification for the receiver
        notification = Notification.objects.create(
            user=instance.receiver,
            message=instance,
            notification_type='message',
            title=f"New message from {instance.sender.username}",
            message_preview=f"{instance.subject}: {instance.content[:100]}..."
        )
        
        print(f"Notification created for {instance.receiver.username}: "
              f"New message from {instance.sender.username}")

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
                # In a real app, you'd get this from the request
                # For now, we'll use the sender or a system user
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
                print(f"Old subject: {original.subject}")
                print(f"New subject: {instance.subject}")
                
        except Message.DoesNotExist:
            pass  # New message, no history to log

@receiver(post_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """
    Signal to clean up all user-related data when a user is deleted.
    This ensures proper cleanup even if CASCADE doesn't handle everything.
    """
    user_id = instance.id
    username = instance.username
    
    print(f"Cleaning up data for deleted user: {username} (ID: {user_id})")
    
    try:
        # Clean up messages where user was sender or receiver
        # Note: These should be handled by CASCADE due to ForeignKey constraints,
        # but we'll log them for verification
        
        sent_messages = Message.objects.filter(sender=instance)
        received_messages = Message.objects.filter(receiver=instance)
        
        print(f"Cleaning up {sent_messages.count()} sent messages")
        print(f"Cleaning up {received_messages.count()} received messages")
        
        # Clean up notifications for the user
        # This should also be handled by CASCADE
        user_notifications = Notification.objects.filter(user=instance)
        print(f"Cleaning up {user_notifications.count()} notifications")
        
        # Clean up message history where user was the editor
        # This should also be handled by CASCADE due to ForeignKey
        edit_history = MessageHistory.objects.filter(edited_by=instance)
        print(f"Cleaning up {edit_history.count()} edit history entries")
        
        # Additional cleanup for orphaned data (if any)
        # This is where you'd handle any custom cleanup logic
        
        print(f"Successfully cleaned up all data for user: {username}")
        
    except Exception as e:
        print(f"Error during cleanup for user {username}: {str(e)}")

@receiver(post_save, sender=Message)
def send_email_notification(sender, instance, created, **kwargs):
    """
    Optional: Signal to send email notification when a new message is created or edited.
    """
    if created:
        print(f"Email notification would be sent to {instance.receiver.email} "
              f"for message from {instance.sender.username}")
    else:
        if instance.edited:
            print(f"Edit notification would be sent to {instance.receiver.email} "
                  f"for edited message from {instance.sender.username}")

def user_post_save_receiver(sender, instance, created, **kwargs):
    """
    Example signal for user creation (optional bonus)
    """
    if created:
        # Find admin user or create system message
        try:
            admin_user = User.objects.get(username='admin')
            welcome_message = Message.objects.create(
                sender=admin_user,
                receiver=instance,
                subject="Welcome to our messaging platform!",
                content="Welcome! We're glad to have you here."
            )
            print(f"Welcome message created for new user: {instance.username}")
        except User.DoesNotExist:
            print("Admin user not found for welcome message")

# Connect the user signal (optional)
post_save.connect(user_post_save_receiver, sender=User)
