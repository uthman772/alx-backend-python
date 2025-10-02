from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
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
