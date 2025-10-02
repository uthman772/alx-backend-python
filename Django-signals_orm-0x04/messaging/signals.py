from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Message, Notification

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
        
        # Print to console for demonstration (optional)
        print(f"Notification created for {instance.receiver.username}: "
              f"New message from {instance.sender.username}")

@receiver(post_save, sender=Message)
def send_email_notification(sender, instance, created, **kwargs):
    """
    Optional: Signal to send email notification when a new message is created.
    This can be expanded to actually send emails.
    """
    if created:
        # Here you would integrate with your email service
        # For now, we'll just log it
        print(f"Email notification would be sent to {instance.receiver.email} "
              f"for message from {instance.sender.username}")

def user_post_save_receiver(sender, instance, created, **kwargs):
    """
    Example signal for user creation (optional bonus)
    """
    if created:
        # Create a welcome notification for new users
        welcome_message = Message.objects.create(
            sender=User.objects.get(username='admin'),  # or system user
            receiver=instance,
            subject="Welcome to our messaging platform!",
            content="Welcome! We're glad to have you here."
        )
        print(f"Welcome message created for new user: {instance.username}")

# Connect the user signal (optional)
post_save.connect(user_post_save_receiver, sender=User)
