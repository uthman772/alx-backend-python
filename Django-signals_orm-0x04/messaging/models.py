from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Message(models.Model):
    """
    Model representing a message between users.
    """
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_messages'
    )
    subject = models.CharField(max_length=200)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    edited = models.BooleanField(default=False)  # New field to track edits
    last_edited = models.DateTimeField(null=True, blank=True)  # Track last edit time
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.sender} to {self.receiver}: {self.subject}"
    
    def save(self, *args, **kwargs):
        """
        Custom save method to update edited fields
        """
        if self.pk:  # If instance already exists (updating)
            original = Message.objects.get(pk=self.pk)
            if (original.content != self.content or 
                original.subject != self.subject):
                self.edited = True
                self.last_edited = timezone.now()
        super().save(*args, **kwargs)


class MessageHistory(models.Model):
    """
    Model to store historical versions of edited messages.
    """
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE, 
        related_name='history'
    )
    old_subject = models.CharField(max_length=200)
    old_content = models.TextField()
    edited_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='message_edits'
    )
    edited_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-edited_at']
        verbose_name = 'Message History'
        verbose_name_plural = 'Message Histories'
    
    def __str__(self):
        return f"History for {self.message.subject} (edited at {self.edited_at})"


class Notification(models.Model):
    """
    Model representing notifications for users when they receive new messages.
    """
    NOTIFICATION_TYPES = (
        ('message', 'New Message'),
        ('system', 'System Notification'),
        ('edit', 'Message Edited'),  # New notification type
    )
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        null=True,
        blank=True
    )
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES, 
        default='message'
    )
    title = models.CharField(max_length=200)
    message_preview = models.TextField(max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"
