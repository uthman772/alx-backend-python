from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Count, Case, When, Value, BooleanField, QuerySet
from django.urls import reverse

class UnreadMessagesManager(models.Manager):
    """
    Custom manager for filtering unread messages with optimized queries.
    """
    
    def get_queryset(self):
        """
        Default queryset for unread messages manager.
        """
        return super().get_queryset().filter(is_read=False)
    
    def for_user(self, user):
        """
        Get unread messages for a specific user with optimized query.
        Uses .only() to retrieve only necessary fields.
        """
        return self.get_queryset().filter(
            receiver=user
        ).select_related('sender').only(
            'id', 'subject', 'content', 'timestamp', 'sender__username', 'sender__id'
        ).order_by('-timestamp')
    
    def unread_count_for_user(self, user):
        """
        Get count of unread messages for a user with optimized query.
        """
        return self.get_queryset().filter(receiver=user).count()
    
    def mark_as_read(self, user, message_ids=None):
        """
        Mark messages as read for a user.
        If message_ids is provided, only mark those messages.
        Otherwise, mark all unread messages for the user.
        """
        queryset = self.get_queryset().filter(receiver=user)
        
        if message_ids:
            queryset = queryset.filter(id__in=message_ids)
        
        return queryset.update(is_read=True)

class ReadMessagesManager(models.Manager):
    """
    Custom manager for filtering read messages with optimized queries.
    """
    
    def get_queryset(self):
        """
        Default queryset for read messages manager.
        """
        return super().get_queryset().filter(is_read=True)
    
    def for_user(self, user):
        """
        Get read messages for a specific user with optimized query.
        """
        return self.get_queryset().filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related('sender', 'receiver').only(
            'id', 'subject', 'content', 'timestamp', 'is_read', 
            'sender__username', 'receiver__username'
        ).order_by('-timestamp')

class MessageQuerySet(models.QuerySet):
    """
    Custom QuerySet for Message model with additional methods.
    """
    
    def with_reply_counts(self):
        """
        Annotate queryset with reply counts.
        """
        return self.annotate(
            reply_count=Count('replies')
        )
    
    def recent_messages(self, days=7):
        """
        Get messages from recent days.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        recent_date = timezone.now() - timedelta(days=days)
        return self.filter(timestamp__gte=recent_date)
    
    def for_conversation(self, user1, user2):
        """
        Get messages between two specific users.
        """
        return self.filter(
            (Q(sender=user1) & Q(receiver=user2)) |
            (Q(sender=user2) & Q(receiver=user1))
        ).select_related('sender', 'receiver').order_by('timestamp')

class MessageManager(models.Manager):
    """
    Custom manager for Message model with optimized queries for threaded conversations.
    """
    
    def get_queryset(self):
        """
        Return the custom QuerySet.
        """
        return MessageQuerySet(self.model, using=self._db)
    
    def get_conversation_thread(self, root_message):
        """
        Get entire conversation thread starting from a root message.
        Uses prefetch_related to optimize database queries.
        """
        return self.filter(
            Q(pk=root_message.pk) | Q(parent_message=root_message) |
            Q(parent_message__parent_message=root_message)
        ).select_related('sender', 'receiver', 'parent_message').prefetch_related('replies')
    
    def get_user_conversations(self, user):
        """
        Get all conversations for a user (both sent and received).
        Optimized with select_related and prefetch_related.
        """
        return self.filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related('sender', 'receiver', 'parent_message').prefetch_related('replies')
    
    def get_root_messages(self, user):
        """
        Get root messages (not replies) for a user with reply counts.
        """
        return self.filter(
            (Q(sender=user) | Q(receiver=user)) & 
            Q(parent_message__isnull=True)
        ).select_related('sender', 'receiver').annotate(
            reply_count=Count('replies'),
            has_unread_replies=Count(
                Case(
                    When(replies__is_read=False, replies__receiver=user, then=Value(1)),
                    output_field=BooleanField()
                )
            )
        ).order_by('-timestamp')
    
    def unread(self):
        """
        Shortcut to unread messages manager.
        """
        return UnreadMessagesManager().get_queryset()
    
    def read(self):
        """
        Shortcut to read messages manager.
        """
        return ReadMessagesManager().get_queryset()

class Message(models.Model):
    """
    Model representing a message between users with threading support.
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
    
    # Read status field - using is_read instead of 'read' to avoid conflict
    is_read = models.BooleanField(default=False, verbose_name='Read status')
    
    edited = models.BooleanField(default=False)
    last_edited = models.DateTimeField(null=True, blank=True)
    
    # Threading support - self-referential foreign key for replies
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='replies',
        null=True,
        blank=True,
        verbose_name='Parent Message'
    )
    
    # Custom managers
    objects = MessageManager()
    unread_messages = UnreadMessagesManager()
    read_messages = ReadMessagesManager()
    
    class Meta:
        ordering = ['timestamp']  # Order by timestamp for threaded view
        indexes = [
            models.Index(fields=['sender', 'timestamp']),
            models.Index(fields=['receiver', 'timestamp']),
            models.Index(fields=['parent_message', 'timestamp']),
            models.Index(fields=['receiver', 'is_read']),  # Index for unread queries
            models.Index(fields=['is_read']),  # General index for read status
        ]
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
    
    def __str__(self):
        read_status = "✓" if self.is_read else "✗"
        return f"{read_status} {self.sender} to {self.receiver}: {self.subject}"
    
    def save(self, *args, **kwargs):
        """
        Custom save method to update edited fields and handle threading.
        """
        if self.pk:  # If instance already exists (updating)
            original = Message.objects.get(pk=self.pk)
            if (original.content != self.content or 
                original.subject != self.subject):
                self.edited = True
                self.last_edited = timezone.now()
        
        # If this is a reply, inherit some properties from parent
        if self.parent_message and not self.subject.startswith('Re: '):
            self.subject = f"Re: {self.parent_message.subject}"
        
        super().save(*args, **kwargs)
    
    @property
    def is_root_message(self):
        """Check if this is a root message (not a reply)."""
        return self.parent_message is None
    
    @property
    def depth(self):
        """Calculate the depth of this message in the thread."""
        depth = 0
        current = self
        while current.parent_message:
            depth += 1
            current = current.parent_message
            if depth > 10:  # Safety limit
                break
        return depth
    
    def mark_as_read(self, commit=True):
        """
        Mark this message as read.
        """
        self.is_read = True
        if commit:
            self.save(update_fields=['is_read'])
    
    def mark_as_unread(self, commit=True):
        """
        Mark this message as unread.
        """
        self.is_read = False
        if commit:
            self.save(update_fields=['is_read'])
    
    def get_absolute_url(self):
        """Get URL for this message detail view."""
        return reverse('messaging:message_thread', kwargs={'message_id': self.pk})
    
    def get_thread_root(self):
        """Get the root message of this thread."""
        current = self
        while current.parent_message:
            current = current.parent_message
        return current
    
    def get_all_replies(self):
        """Get all replies in this thread (optimized query)."""
        return Message.objects.filter(
            parent_message=self.get_thread_root()
        ).select_related('sender', 'receiver').order_by('timestamp')


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
        ('edit', 'Message Edited'),
        ('reply', 'New Reply'),
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
